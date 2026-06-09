"""
CodePath AI201 — Project 1: The Unofficial Guide (TXST)
Gradio web UI for the RAG pipeline.
Run: python app.py  ->  http://localhost:7860
"""

import sys

import gradio as gr

from ingest import ingest_documents
from rag import ask


def build_ui() -> gr.Blocks:
    def handle_query(question: str):
        if not question.strip():
            return "Please enter a question.", ""
        try:
            result = ask(question.strip())
            return result["answer_text"], result["sources_display"]
        except EnvironmentError as exc:
            return str(exc), ""
        except Exception as exc:
            return f"Error: {exc}", ""

    with gr.Blocks(title="TXST Unofficial Guide") as demo:
        gr.Markdown(
            "# The Unofficial Guide — Texas State University\n"
            "Ask about CS professors, housing, dining, and campus tips. "
            "Answers are grounded in collected student documents only."
        )
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. Who is better for CS 1428, Prof. Jones or Prof. Smith?",
            lines=2,
        )
        btn = gr.Button("Ask", variant="primary")
        answer = gr.Textbox(label="Answer", lines=10)
        sources = gr.Textbox(label="Retrieved from", lines=4)
        btn.click(handle_query, inputs=inp, outputs=[answer, sources])
        inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    return demo


def main() -> None:
    try:
        chunks, _ = ingest_documents()
        print(f"Indexed {len(chunks)} chunks. Starting Gradio UI...")
    except Exception as exc:
        print(f"ERROR during ingestion: {exc}", file=sys.stderr)
        sys.exit(1)

    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
