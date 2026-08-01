import os
import shutil
import threading
import gradio as gr
import pandas as pd

import main as pipeline  # import the module; call pipeline.main() — NOT main()

# ── Guard against concurrent / double-click invocations ──────────────────────
_lock = threading.Lock()
_running = False


def process_pipeline(uploaded_file):
    global _running

    with _lock:
        if _running:
            return (
                "⚠️ Pipeline is already running. Please wait…",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(interactive=False),
            )
        _running = True

    try:
        # ── Validate upload ───────────────────────────────────────────────────
        if uploaded_file is None:
            return (
                "❌ Please upload brands.csv first.",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(interactive=True),
            )

        # ── Copy uploaded file to project root ───────────────────────────────
        file_path = (
            uploaded_file
            if isinstance(uploaded_file, str)
            else uploaded_file.name
        )
        shutil.copy(file_path, "brands.csv")

        # ── Run backend exactly ONCE ──────────────────────────────────────────
        pipeline.main()

        # ── Read outputs ──────────────────────────────────────────────────────
        ranked_csv    = "output/ranked_accounts.csv"
        signals_json  = "output/signals.json"
        outreach_json = "output/top5_outreach.json"

        if not os.path.exists(ranked_csv):
            return (
                "❌ ranked_accounts.csv not found after pipeline run.",
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(interactive=True),
            )

        df = pd.read_csv(ranked_csv)

        return (
            "✅ Pipeline Completed Successfully!",
            gr.update(value=df),
            gr.update(value=ranked_csv    if os.path.exists(ranked_csv)    else None),
            gr.update(value=signals_json  if os.path.exists(signals_json)  else None),
            gr.update(value=outreach_json if os.path.exists(outreach_json) else None),
            gr.update(interactive=True),
        )

    except Exception as e:
        return (
            f"❌ Pipeline failed:\n{e}",
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(interactive=True),
        )

    finally:
        with _lock:
            _running = False


# ── UI ────────────────────────────────────────────────────────────────────────
with gr.Blocks(
    title="ClickPost AI Sales Intelligence",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(
        """
#  ClickPost AI Sales Intelligence

Upload **brands.csv**, run the AI pipeline and download the generated outputs.
"""
    )

    with gr.Row():

        with gr.Column(scale=1):

            file_input = gr.File(
                label="Upload brands.csv",
                file_types=[".csv"],
            )

            process_btn = gr.Button(
                " Start Processing",
                variant="primary",
                interactive=True,
            )

            status = gr.Markdown(value="**Status:** Ready")

        with gr.Column(scale=2):

            results = gr.Dataframe(
                label="Ranked Accounts",
                interactive=False,
                wrap=True,
            )

            gr.Markdown("## Downloads")

            ranked_file   = gr.File(label="Ranked Accounts CSV")
            signals_file  = gr.File(label="Signals JSON")
            outreach_file = gr.File(label="Top 5 Outreach JSON")

    # ── Event wiring (two-step chain) ─────────────────────────────────────────
    # Step A (queue=False): instantly disable button + show "Running…"
    # Step B             : run the pipeline; re-enable button on return
    process_btn.click(
        fn=lambda: (
            "**Status:** 🔄 Running… (this may take a few minutes)",
            gr.update(interactive=False),
        ),
        inputs=None,
        outputs=[status, process_btn],
        queue=False,
    ).then(
        fn=process_pipeline,
        inputs=file_input,
        outputs=[
            status,
            results,
            ranked_file,
            signals_file,
            outreach_file,
            process_btn,
        ],
    )


if __name__ == "__main__":
    demo.launch(
        inbrowser=True,
        share=False,
    )