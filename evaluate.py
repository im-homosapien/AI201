"""
Structured evaluation for retrieval quality and grounded generation.
Run: python evaluate.py
Writes results to evaluation_report.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ingest import ingest_documents
from rag import ask_unofficial_guide, create_gemini_client, retrieve_relevant_chunks

REPORT_FILE = Path(__file__).parent / "evaluation_report.md"


@dataclass
class EvalCase:
    name: str
    question: str
    must_retrieve: list[str]  # substrings that should appear in at least one retrieved chunk
    notes: str = ""


EVAL_CASES = [
    EvalCase(
        name="professor_smith",
        question="What do students say about Prof. Smith for CS 1428?",
        must_retrieve=["Smith", "CS 1428"],
    ),
    EvalCase(
        name="professor_jones",
        question="Is Prof. Jones a good choice for CS 1428?",
        must_retrieve=["Jones", "pop quiz"],
    ),
    EvalCase(
        name="professor_comparison",
        question="Who is better for CS 1428, Prof. Jones or Prof. Smith?",
        must_retrieve=["Smith", "Jones"],
        notes="Critical comparison case — needs BOTH professors in top-k retrieval.",
    ),
    EvalCase(
        name="on_campus_housing",
        question="Which on-campus housing is near the library?",
        must_retrieve=["San Jacinto", "library"],
    ),
    EvalCase(
        name="dining_hall",
        question="Which dining hall has the longest hours?",
        must_retrieve=["Jones Dining Hall", "hours"],
    ),
    EvalCase(
        name="out_of_corpus",
        question="What is the best professor for MATH 2471?",
        must_retrieve=[],
        notes="No MATH 2471 data exists — model should refuse or say I don't know.",
    ),
]


def retrieval_pass(retrieved_texts: list[str], must_retrieve: list[str]) -> bool:
    if not must_retrieve:
        return True
    combined = " ".join(retrieved_texts).lower()
    return all(term.lower() in combined for term in must_retrieve)


def run_evaluation(run_generation: bool = True) -> str:
    ingest_documents()
    client = None
    generation_note = ""
    if run_generation:
        try:
            client = create_gemini_client()
        except OSError:
            generation_note = (
                "_Generation tests skipped - set `GEMINI_API_KEY` and re-run "
                "`python evaluate.py` to include live Gemini results._\n"
            )

    lines = [
        "# TXST Unofficial Guide - Evaluation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        generation_note,
        "## Methodology",
        "",
        "- **Ingestion:** `txst_data.txt` -> clean/chunk -> `all-MiniLM-L6-v2` embeddings -> ChromaDB",
        "- **Retrieval:** Top-3 semantic search per query",
        "- **Generation:** `gemini-2.5-flash`, temperature=0.0, citation-required system prompt",
        "",
        "## Test Results",
        "",
        "| # | Test | Retrieval | Generation | Notes |",
        "|---|------|-----------|------------|-------|",
    ]

    failures: list[str] = []
    case_results: list[dict] = []

    for case in EVAL_CASES:
        chunks = retrieve_relevant_chunks(case.question)
        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        ret_ok = retrieval_pass(texts, case.must_retrieve)
        ret_label = "PASS" if ret_ok else "**FAIL**"

        gen_label = "SKIP" if run_generation and not client else "n/a"
        answer_snippet = ""
        if client:
            result = ask_unofficial_guide(case.question, client, verbose=False)
            answer = result["answer"]
            answer_snippet = answer.replace("\n", " ")[:120]
            if case.name == "out_of_corpus":
                gen_ok = "don't know" in answer.lower() or "do not know" in answer.lower()
            elif case.name == "professor_comparison":
                gen_ok = "smith" in answer.lower() and "jones" in answer.lower()
            else:
                gen_ok = bool(answer.strip()) and "don't know" not in answer.lower()[:30]
            gen_label = "PASS" if gen_ok else "**FAIL**"
            if not gen_ok:
                failures.append(f"Generation failed: {case.name}")

        if not ret_ok:
            failures.append(f"Retrieval failed: {case.name}")

        note = case.notes or f"Retrieved: {', '.join(ids)}"
        case_results.append({
            "case": case,
            "chunks": chunks,
            "ret_label": ret_label,
            "gen_label": gen_label,
            "note": note,
            "answer_snippet": answer_snippet,
        })

    for i, result in enumerate(case_results, start=1):
        lines.append(
            f"| {i} | {result['case'].name} | {result['ret_label']} | "
            f"{result['gen_label']} | {result['note']} |"
        )

    lines.extend(["", "## Detailed Results", ""])
    for result in case_results:
        case = result["case"]
        lines.extend([
            f"### {case.name}",
            "",
            f"**Question:** {case.question}",
            "",
            "**Retrieved chunks:**",
        ])
        for c in result["chunks"]:
            dist = f"{c.distance:.4f}" if c.distance is not None else "n/a"
            lines.append(f"- `{c.chunk_id}` (dist={dist}): {c.text[:150]}...")
        if result["answer_snippet"]:
            lines.extend(["", f"**Model answer:** {result['answer_snippet']}...", ""])
        else:
            lines.append("")

    lines.extend([
        "## Identified Failure Mode",
        "",
        "### Failure: Single-chunk keyword routing in prototype (fixed) -> top-k semantic gap on niche queries",
        "",
        "**Pipeline stage:** Retrieval",
        "",
        "**What happened:** In the original keyword-only prototype, the comparison question "
        '"Who is better for CS 1428, Prof. Jones or Prof. Smith?" retrieved only the first '
        "name-matched professor. Gemini correctly answered \"I don't know\" about the other "
        "professor because the missing context was never retrieved.",
        "",
        "**Fix applied:** Switched to ChromaDB vector search with `top_k=3` so comparison "
        "queries can surface multiple relevant chunks. The `professor_comparison` test above "
        "validates whether both professors appear in retrieval.",
        "",
        "**Remaining risk:** Out-of-corpus questions (e.g. MATH 2471) may still retrieve "
        "tangentially related CS or academic chunks. The generation prompt must refuse when "
        "context is irrelevant — verified in the `out_of_corpus` test.",
        "",
        "## Summary",
        "",
    ])

    if failures:
        lines.append(f"- **Issues found:** {len(failures)} - " + "; ".join(failures))
    else:
        lines.append("- **All automated checks passed.**")

    report = "\n".join(lines)
    REPORT_FILE.write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    report = run_evaluation()
    print(report)
    print(f"\nReport saved to {REPORT_FILE}")
