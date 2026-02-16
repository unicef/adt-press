# ADT Press Setup & Run Checklist

This document summarizes the steps we followed to go from a fresh clone to a working `uv run adt-press.py` invocation in this repo.

1. **Prepare the system**
   - Confirm you are on Python 3.13+ (the project requires Python >=3.13 in `pyproject.toml`).
   - Install the `uv` package manager (used for dependency management):
     ```bash
     python3 -m pip install --user --upgrade uv
     ```
   - Ensure the install directory (`$HOME/Library/Python/3.9/bin` on macOS) is on your `PATH` so `uv` commands are available:
     ```bash
     export PATH="$HOME/Library/Python/3.9/bin:$PATH"
     ```
     Source your shell profile or re-open the terminal until `uv --version` works.

2. **Install dependencies via `uv`**
   - From the repository root run:
     ```bash
     uv sync
     ```
     This downloads all Python dependencies defined in `pyproject.toml` and builds packages such as `pycairo`.
   - If the build fails (e.g., `pycairo` complaining about missing `cairo`), install the native library before retrying:
     ```bash
     brew install cairo pkg-config
     ```
   - If the application later tries to visualize a Hamilton graph, install Graphviz so the `dot` executable works:
     ```bash
     brew install graphviz
     ```

3. **Set required environment variables**
   - The pipeline uses OpenAI (and optionally Azure) models. Export the API key(s) in the same shell where you run `uv`:
     ```bash
     export OPENAI_API_KEY="sk-..."
     export AZURE_API_KEY="..."        # optional when using Azure TTS
     export AZURE_API_BASE="https://..."  # optional
     ```
   - Verify `uv` sees the variables before running the pipeline:
     ```bash
     uv run python -c 'import os; print(os.environ.get("OPENAI_API_KEY"))'
     ```
     If the output is empty, prepend the key when invoking `uv run` e.g. `OPENAI_API_KEY=... uv run ...` or source the exports immediately before the command.

4. **Run the main script**
   - Always specify the `pdf_path` override (absolute or relative); otherwise, OmegaConf cannot compute `run_output_dir` and the run will fail. Example:
     ```bash
     uv run adt-press.py pdf_path=assets/raven.pdf caption_strategy=llm speech_strategy=tts quiz_strategy=llm render_strategy=two_column_story\
       page_grouping=spread default_model=gpt-5 speech.provider=openai speech.format=mp3 speech.bit_rate=64k speech.sample_rate=24000\
       speech.providers.openai.model=gpt-4o-mini-tts speech.providers.azure.model=azure/speech/azure-tts image_filters.size.max_side=3500\
       image_filters.size.min_side=150 image_filters.blank.threshold=2 prompts.section_quiz.sections_per_quiz=5\
       speech.providers.openai.languages="[\"en\"]" speech.providers.azure.languages="[\"es\", \"ta\", \"si\"]"\
       text_filters.pruned_text_types="[\"footer_text\", \"page_number\", \"other\"]"\
       section_filters.pruned_section_types="[\"inside_cover\", \"back_cover\", \"credits\"]"\
       section_filters.quiz_count_section_types="[\"boxed_text\", \"text_only\", \"text_and_single_image\", \"text_and_images\", \"images_only\"]"
     ```
   - The command extracts the PDF, runs metadata/LLM steps, and, depending on your overrides, may produce speech, captions, and the ADT HTML. Adjust overrides (e.g., disable `speech_strategy` or specify `page_range`) as needed.
   - If Graphviz is installed, the Hamilton driver automatically creates `output/<label>/run.png`; otherwise disable the graph view with `HAMILTON_DISABLE_GRAPH_RENDERING=1` or by not calling `view_run`.

5. **Troubleshooting pointers**
   - If `uv` still says `command not found`, check the PATH again or run `python3 -m pip install uv --user` inside the same shell and add the corresponding `bin` directory. Use `which uv` to confirm.
   - When `pycairo` fails to build, the log references missing `cairo` dependency; install it via Homebrew (`brew install cairo pkg-config`) before rerunning `uv sync`.
   - Authentication errors from `litellm`/`openai` mean `OPENAI_API_KEY` was not available; ensure it is exported and visible to `uv run` or pass it inline with the command.
   - Graphviz errors like `dot` missing can be resolved by installing Graphviz or by setting `HAMILTON_DISABLE_GRAPH_RENDERING=1` when you don't need to render the execution graph.

6. **Optional GUI (Wizard)**
   - Run `python wizard.py` (or `python3 wizard.py`) to launch the wizard interface, which hosts a local HTTP server for configuring and executing the pipeline.
     ```bash
     python wizard.py
     # or
     python3 wizard.py
     ```
   - Make sure the chosen port (default `127.0.0.1:<port>`) is free before starting the wizard; stop any conflicting process if you see `Address already in use`.
   - The wizard uses the same `uv` environment and configuration logic, so the prerequisites regarding `uv`, dependencies, and environment variables still apply.

7. **After a successful run**
   - The outputs land in `output/<label>/`; open the generated HTML report(s) inside that directory to review the ADT pages, media, and speech files.
   - Re-run with different overrides to generate sections, captions, speech, quizzes, or to use other render strategies.
