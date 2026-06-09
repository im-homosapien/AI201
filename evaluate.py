"""
Structured evaluation — 5 test questions from planning.md.
Run: python evaluate.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ingest import ingest_documents
from rag import ask, create_gemini_client, retrieve_relevant_chunks

REPORT_FILE = Path(__file__).parent / "evaluation_report.md"


@dataclass
class EvalCase:
    name: str
    question: str
    expected_answer: str
    must_retrieve: list[str]


EVAL_CASES = [
    EvalCase(
        name="professor_smith",
        question="What do students say about Prof. Smith for CS 1428?",
        expected_answer="Clear lectures, extra credit on labs, math-heavy exams, 4.5/5 rating.",
        must_retrieve=["Smith", "extra credit"],
    ),
    EvalCase(
        name="professor_jones",
        question="Is Prof. Jones a good choice for CS 1428?",
        expected_answer="No — pop quizzes, strict attendance, harsh grading, 2/10 rating.",
        must_retrieve=["Jones", "pop quiz"],
    ),
    EvalCase(
        name="housing_library",
        question="Which on-campus housing is near Alkek Library?",
        expected_answer="San Jacinto Hall, near Alkek Library and LBJ Student Center.",
        must_retrieve=["San Jacinto", "Alkek"],
    ),
    EvalCase(
        name="dining_hours",
        question="Which dining hall has the widest hours on main campus?",
        expected_answer="Jones Dining Hall (JDH) has the widest hours on main campus.",
        must_retrieve=["Jones Dining Hall", "widest hours"],
    ),
    EvalCase(
        name="out_of_scope",
        question="Who is the best professor for MATH 2471 at TXST?",
        expected_answer="System should refuse — no MATH 2471 documents in corpus.",
        must_retrieve=[],
    ),
]


def retrieval_pass(texts: list[str], must_retrieve: list[str]) -> bool:
    if not must_retrieve:
        return True
    combined = " ".join(texts).lower()
    return all(term.lower() in combined for term in must_retrieve)


def judge_accuracy(case: EvalCase, answer: str) -> str:
    lower = answer.lower()
    if case.name == "out_of_scope":
        if "don't have enough information" in lower or "don't know" in lower:
            return "accurate"
        return "inaccurate"
    if case.name == "professor_jones":
        if "pop quiz" in lower or "2/10" in lower or "harsh" in lower:
            return "accurate"
        return "partially accurate"
    if case.name == "professor_smith":
        if "smith" in lower and ("4.5" in lower or "extra credit" in lower):
            return "accurate"
        return "partially accurate"
    if case.name == "housing_library":
        if "san jacinto" in lower:
            return "accurate"
        return "inaccurate"
    if case.name == "dining_hours":
        if "jones" in lower and "hour" in lower:
            return "accurate"
        return "partially accurate"
    return "partially accurate"


def run_evaluation() -> str:
    ingest_documents()
    try:
        create_gemini_client()
        has_key = True
    except OSError:
        has_key = False

    lines = [
        "# TXST Unofficial Guide - Evaluation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "| # | Question | Retrieval | Response accuracy |",
        "|---|----------|-----------|-------------------|",
    ]

    details: list[str] = ["", "## Detailed Results", ""]
    failures: list[str] = []

    for i, case in enumerate(EVAL_CASES, start=1):
        chunks = retrieve_relevant_chunks(case.question)
        texts = [c.text for c in chunks]
        ret_ok = retrieval_pass(texts, case.must_retrieve)
        ret_label = "PASS" if ret_ok else "FAIL"

        gen_label = "SKIP (no API key)"
        answer = ""
        if has_key:
            result = ask(case.question)
            answer = result["answer_text"]
            gen_label = judge_accuracy(case, answer)
            if gen_label == "inaccurate":
                failures.append(case.name)

        if not ret_ok:
            failures.append(f"retrieval:{case.name}")

        lines.append(f"| {i} | {case.question[:50]}... | {ret_label} | {gen_label} |")

        details.extend([
            f"### Q{i}: {case.name}",
            "",
            f"**Question:** {case.question}",
            f"**Expected:** {case.expected_answer}",
            f"**Retrieval:** {ret_label}",
            f"**Accuracy:** {gen_label}",
            "",
            "**Retrieved chunks:**",
        ])
        for c in chunks:
            dist = f"{c.distance:.4f}" if c.distance is not None else "n/a"
            details.append(f"- `{c.source_file}` (dist={dist}): {c.text[:120]}...")
        if answer:
            details.extend(["", f"**System response:** {answer}", ""])
        else:
            details.append("")

    lines.extend(details)
    lines.extend([
        "## Failure Case",
        "",
        "**Question:** Who is the best professor for MATH 2471 at TXST?",
        "",
        "**Pipeline stage:** Retrieval + Generation",
        "",
        "**What happened:** Retrieval returns CS 1428 professor chunks (semantic similarity "
        "to 'professor' queries) even though MATH 2471 is not in the corpus. Without strict "
        "grounding, the LLM might hallucinate a math professor name.",
        "",
        "**Mitigation:** System prompt requires refusal when context lacks the answer. "
        "Programmatic source list shows retrieved docs are CS-related, not MATH 2471.",
        "",
        "## Summary",
        "",
    ])
    if failures:
        lines.append(f"Issues: {', '.join(failures)}")
    else:
        lines.append("All retrieval checks passed." + (" Run with GEMINI_API_KEY for generation scores." if not has_key else ""))

    report = "\n".join(lines)
    REPORT_FILE.write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    report = run_evaluation()
    print(report)
    print(f"\nReport saved to {REPORT_FILE}")
