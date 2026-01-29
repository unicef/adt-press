"""ADT Press Wizard — a simple local web UI for first-time PDF conversion.

Run with:  uv run wizard.py   (or python3 wizard.py)
Opens a page in your default browser at http://localhost:<port>.
"""

import json
import os
import subprocess
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- streaming state (one job at a time) ----------
_lock = threading.Lock()
_log_lines: list[str] = []
_running = False


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADT Press Wizard</title>
<style>
  :root { --bg: #f6f8fa; --card: #fff; --accent: #0969da; --border: #d1d9e0;
          --text: #1f2328; --muted: #656d76; --hover: #f3f4f6; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--text); display: flex; justify-content: center;
         padding: 32px 16px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px;
          padding: 0; max-width: 620px; width: 100%; overflow: hidden; }
  h1 { font-size: 20px; padding: 20px 24px 0; }

  /* ── tabs ── */
  .tabs { display: flex; border-bottom: 1px solid var(--border); padding: 12px 24px 0; gap: 0;
          overflow-x: auto; }
  .tab { padding: 8px 14px; font-size: 13px; font-weight: 500; color: var(--muted); cursor: pointer;
         border: none; background: none; border-bottom: 2px solid transparent; white-space: nowrap; }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
  .pane { display: none; padding: 20px 24px; }
  .pane.active { display: block; }

  /* ── form elements ── */
  label { display: block; font-weight: 600; font-size: 13px; margin-bottom: 3px; }
  .hint { font-size: 11px; color: var(--muted); margin-bottom: 10px; }
  input[type="text"], input[type="number"], select {
    width: 100%; padding: 7px 10px; border: 1px solid var(--border);
    border-radius: 6px; font-size: 13px; margin-bottom: 4px; }
  input[type="number"] { -moz-appearance: textfield; }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  fieldset { border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }
  legend { font-weight: 600; font-size: 13px; padding: 0 6px; }
  .checks { display: grid; grid-template-columns: 1fr 1fr; gap: 3px 14px; }
  .checks label { font-weight: 400; display: flex; align-items: center; gap: 5px; cursor: pointer;
                   font-size: 13px; }
  .section-title { font-weight: 600; font-size: 14px; margin: 14px 0 6px; }
  .section-title:first-child { margin-top: 0; }

  /* ── tag input ── */
  .tag-wrap { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 6px 8px;
              border: 1px solid var(--border); border-radius: 6px; min-height: 36px; margin-bottom: 4px; }
  .tag { display: inline-flex; align-items: center; gap: 4px; background: #ddf4ff; color: #0969da;
         padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; }
  .tag button { background: none; border: none; cursor: pointer; font-size: 14px; color: #0969da;
                padding: 0 2px; line-height: 1; }
  .tag-input { border: none; outline: none; font-size: 13px; flex: 1; min-width: 80px; padding: 2px 0; }

  /* ── bottom bar ── */
  .bottom { padding: 16px 24px; border-top: 1px solid var(--border); }
  button.primary { background: var(--accent); color: #fff; border: none; border-radius: 8px;
                   padding: 10px 24px; font-size: 14px; font-weight: 600; cursor: pointer; width: 100%; }
  button.primary:disabled { opacity: .5; cursor: not-allowed; }
  #log-wrap { margin-top: 12px; display: none; }
  #log { background: #0d1117; color: #c9d1d9; font-family: "SF Mono", Menlo, Consolas, monospace;
         font-size: 11px; padding: 12px; border-radius: 8px; height: 240px; overflow-y: auto;
         white-space: pre-wrap; word-break: break-all; }
</style>
</head>
<body>
<div class="card">
  <h1>ADT Press Wizard</h1>

  <!-- ── Tabs ── -->
  <div class="tabs">
    <button class="tab active" onclick="switchTab('convert',this)">Convert</button>
    <button class="tab" onclick="switchTab('speech',this)">Speech / TTS</button>
    <button class="tab" onclick="switchTab('render',this)">Rendering</button>
    <button class="tab" onclick="switchTab('filters',this)">Filters</button>
    <button class="tab" onclick="switchTab('advanced',this)">Advanced</button>
  </div>

  <!-- ════════════════ TAB: Convert ════════════════ -->
  <div id="tab-convert" class="pane active">
    <label for="pdf">PDF file path</label>
    <input type="text" id="pdf" placeholder="/path/to/textbook.pdf">
    <div class="hint">Full path to the PDF you want to convert.</div>

    <div class="row">
      <div>
        <label for="lbl">Label <span style="font-weight:400;color:var(--muted)">(optional)</span></label>
        <input type="text" id="lbl" placeholder="auto from filename">
        <div class="hint">The output folder will be: output/&lt;label&gt;</div>
      </div>
      <div>
        <label for="lang">Input language</label>
        <select id="lang">
          <option value="auto" selected>auto-detect</option>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="pt">Portuguese</option>
          <option value="ar">Arabic</option>
          <option value="ta">Tamil</option>
          <option value="si">Sinhala</option>
          <option value="sw">Swahili</option>
          <option value="hi">Hindi</option>
          <option value="zh">Chinese</option>
          <option value="ru">Russian</option>
          <option value="de">German</option>
          <option value="ja">Japanese</option>
          <option value="ko">Korean</option>
          <option value="vi">Vietnamese</option>
          <option value="th">Thai</option>
          <option value="id">Indonesian</option>
          <option value="tr">Turkish</option>
        </select>
      </div>
    </div>

    <label style="margin-top:10px">Output languages</label>
    <div class="tag-wrap" id="out-langs-wrap">
      <input class="tag-input" id="out-lang-input" placeholder="Type language code + Enter (e.g. es, fr)"
             list="lang-list">
    </div>
    <div class="hint">Leave empty to use the input language only. Add codes like en, es, fr, ar, ta, etc.</div>
    <datalist id="lang-list">
      <option value="en"><option value="es"><option value="fr"><option value="pt"><option value="ar">
      <option value="ta"><option value="si"><option value="sw"><option value="hi"><option value="zh">
      <option value="ru"><option value="de"><option value="ja"><option value="ko"><option value="vi">
      <option value="th"><option value="id"><option value="tr"><option value="bn"><option value="ur">
      <option value="nl"><option value="pl"><option value="sv"><option value="fil">
    </datalist>

    <fieldset>
      <legend>Features</legend>
      <div class="checks">
        <label><input type="checkbox" data-key="glossary_strategy"    data-val="llm"> Glossary</label>
        <label><input type="checkbox" data-key="explanation_strategy" data-val="llm"> Explanations</label>
        <label><input type="checkbox" data-key="easy_read_strategy"   data-val="llm"> Easy Read</label>
        <label><input type="checkbox" data-key="caption_strategy"     data-val="llm"> Image Captions</label>
        <label><input type="checkbox" data-key="crop_strategy"        data-val="llm"> Image Cropping</label>
        <label><input type="checkbox" id="cb-activity" data-key="activity_strategy" data-val="llm"
                      onchange="if(this.checked) document.getElementById('cb-quiz').checked=false; toggleQuizOpts();"> Activities</label>
        <label><input type="checkbox" id="cb-quiz" data-key="quiz_strategy" data-val="llm"
                      onchange="if(this.checked) document.getElementById('cb-activity').checked=false; toggleQuizOpts();"> Quizzes</label>
        <label><input type="checkbox" data-key="speech_strategy"      data-val="tts"> Text-to-Speech</label>
      </div>
      <div id="quiz-opts" style="display:none; margin-top:8px; padding-left:4px;">
        <div class="row">
          <div>
            <label for="quiz-per">Sections per quiz</label>
            <input type="number" id="quiz-per" value="3" min="1" style="width:80px">
          </div>
        </div>
        <div class="hint">How many content sections are grouped before a quiz is inserted.</div>
      </div>
    </fieldset>

    <fieldset>
      <legend>Page Range</legend>
      <div class="row">
        <div>
          <label for="pstart">Start page</label>
          <input type="number" id="pstart" value="0" min="0">
        </div>
        <div>
          <label for="pend">End page</label>
          <input type="number" id="pend" value="0" min="0">
        </div>
      </div>
      <div class="hint">0 = process all pages.</div>
    </fieldset>
  </div>

  <!-- ════════════════ TAB: Speech / TTS ════════════════ -->
  <div id="tab-speech" class="pane">
    <div class="row">
      <div>
        <label for="speech-provider">Provider</label>
        <select id="speech-provider">
          <option value="openai" selected>OpenAI</option>
          <option value="azure">Azure</option>
          <option value="dynamic">dynamic</option>
        </select>
        <div class="hint">Which TTS provider to use.</div>
      </div>
      <div>
        <label for="speech-format">Audio format</label>
        <select id="speech-format">
          <option value="mp3" selected>mp3</option>
          <option value="wav">wav</option>
          <option value="ogg">ogg</option>
        </select>
      </div>
    </div>

    <fieldset>
      <legend>OpenAI</legend>
      <label for="openai-model">Model</label>
      <input type="text" id="openai-model" value="gpt-4o-mini-tts">
      <label>Languages handled by OpenAI</label>
      <div class="tag-wrap" id="openai-langs-wrap">
        <span class="tag">en <button onclick="removeTag(this)">&times;</button></span>
        <input class="tag-input" id="openai-lang-input" placeholder="Add language code…" list="lang-list">
      </div>
    </fieldset>

    <fieldset>
      <legend>Azure</legend>
      <label for="azure-model">Model</label>
      <input type="text" id="azure-model" value="azure/speech/azure-tts">
      <label>Languages handled by Azure</label>
      <div class="tag-wrap" id="azure-langs-wrap">
        <span class="tag">es <button onclick="removeTag(this)">&times;</button></span>
        <span class="tag">ta <button onclick="removeTag(this)">&times;</button></span>
        <span class="tag">si <button onclick="removeTag(this)">&times;</button></span>
        <input class="tag-input" id="azure-lang-input" placeholder="Add language code…" list="lang-list">
      </div>
    </fieldset>

    <div class="row">
      <div>
        <label for="speech-bitrate">Bit rate</label>
        <input type="text" id="speech-bitrate" value="64k">
      </div>
      <div>
        <label for="speech-samplerate">Sample rate</label>
        <input type="number" id="speech-samplerate" value="24000">
      </div>
    </div>
  </div>

  <!-- ════════════════ TAB: Rendering ════════════════ -->
  <div id="tab-render" class="pane">
    <div class="row">
      <div>
        <label for="render-strategy">Render strategy</label>
        <select id="render-strategy">
          <option value="dynamic" selected>dynamic</option>
          <option value="two_column">two_column</option>
          <option value="two_column_story">two_column_story</option>
          <option value="single_column">single_column</option>
          <option value="html">html</option>
          <option value="overlay">overlay</option>
        </select>
        <div class="hint">"dynamic" picks per section type.</div>
      </div>
      <div></div>
    </div>

    <div class="row" style="margin-top:8px">
      <div>
        <label for="page-grouping">Page grouping</label>
        <select id="page-grouping">
          <option value="single" selected>single</option>
          <option value="spread">spread</option>
        </select>
        <div class="hint">"spread" pairs even-odd pages.</div>
      </div>
      <div></div>
    </div>
  </div>

  <!-- ════════════════ TAB: Filters ════════════════ -->
  <div id="tab-filters" class="pane">
    <fieldset>
      <legend>Image Filters</legend>
      <div class="row">
        <div>
          <label for="img-max">Max side (px)</label>
          <input type="number" id="img-max" value="3500">
        </div>
        <div>
          <label for="img-min">Min side (px)</label>
          <input type="number" id="img-min" value="150">
        </div>
        <div>
          <label for="img-blank">Blank threshold</label>
          <input type="number" id="img-blank" value="2">
        </div>
      </div>
    </fieldset>

    <fieldset>
      <legend>Pruned Text Types</legend>
      <div class="hint">Checked types are removed from output.</div>
      <div class="checks" id="pruned-text-checks">
        <label><input type="checkbox" value="book_title"> book_title</label>
        <label><input type="checkbox" value="book_subtitle"> book_subtitle</label>
        <label><input type="checkbox" value="book_author"> book_author</label>
        <label><input type="checkbox" value="book_metadata"> book_metadata</label>
        <label><input type="checkbox" value="section_heading"> section_heading</label>
        <label><input type="checkbox" value="section_text"> section_text</label>
        <label><input type="checkbox" value="instruction_text"> instruction_text</label>
        <label><input type="checkbox" value="activity_number"> activity_number</label>
        <label><input type="checkbox" value="activity_title"> activity_title</label>
        <label><input type="checkbox" value="activity_option"> activity_option</label>
        <label><input type="checkbox" value="fill_in_the_blank"> fill_in_the_blank</label>
        <label><input type="checkbox" value="image_associated_text"> image_associated_text</label>
        <label><input type="checkbox" value="image_overlay"> image_overlay</label>
        <label><input type="checkbox" value="math"> math</label>
        <label><input type="checkbox" value="standalone_text"> standalone_text</label>
        <label><input type="checkbox" value="header_text"> header_text</label>
        <label><input type="checkbox" value="footer_text" checked> footer_text</label>
        <label><input type="checkbox" value="page_number" checked> page_number</label>
        <label><input type="checkbox" value="other" checked> other</label>
      </div>
    </fieldset>

    <fieldset>
      <legend>Pruned Section Types</legend>
      <div class="hint">Checked types are excluded from output.</div>
      <div class="checks" id="pruned-section-checks">
        <label><input type="checkbox" value="front_cover"> front_cover</label>
        <label><input type="checkbox" value="inside_cover" checked> inside_cover</label>
        <label><input type="checkbox" value="back_cover" checked> back_cover</label>
        <label><input type="checkbox" value="separator"> separator</label>
        <label><input type="checkbox" value="credits" checked> credits</label>
        <label><input type="checkbox" value="foreword"> foreword</label>
        <label><input type="checkbox" value="table_of_contents"> table_of_contents</label>
      </div>
    </fieldset>

    <fieldset>
      <legend>Quiz-Counting Section Types</legend>
      <div class="hint">Only these types count toward quiz grouping.</div>
      <div class="checks" id="quiz-section-checks">
        <label><input type="checkbox" value="boxed_text" checked> boxed_text</label>
        <label><input type="checkbox" value="text_only" checked> text_only</label>
        <label><input type="checkbox" value="text_and_single_image" checked> text_and_single_image</label>
        <label><input type="checkbox" value="text_and_images" checked> text_and_images</label>
        <label><input type="checkbox" value="images_only" checked> images_only</label>
      </div>
    </fieldset>
  </div>

  <!-- ════════════════ TAB: Advanced ════════════════ -->
  <div id="tab-advanced" class="pane">
    <label for="default-model">Default LLM model</label>
    <input type="text" id="default-model" value="gpt-5">
    <div class="hint">Used for all prompts unless overridden.</div>

    <label for="output-dir" style="margin-top:10px">Output directory</label>
    <input type="text" id="output-dir" value="output">
    <div class="hint">Base output directory. Each run creates a subfolder named by label.</div>

    <label for="custom-plate" style="margin-top:10px">Custom plate path <span style="font-weight:400;color:var(--muted)">(optional)</span></label>
    <input type="text" id="custom-plate" placeholder="">
    <div class="hint">If set, this existing plate JSON is used instead of generating one.</div>
  </div>

  <!-- ════════════════ Bottom bar ════════════════ -->
  <div class="bottom">
    <button class="primary" id="run" onclick="run()">Run Conversion</button>
    <div id="log-wrap">
      <div id="log"></div>
    </div>
  </div>
</div>

<script>
/* ── tabs ── */
function switchTab(id, btn) {
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
}

/* ── tag inputs ── */
function removeTag(btn) { btn.parentElement.remove(); }

function addTag(wrapId, value) {
  value = value.trim().toLowerCase();
  if (!value) return;
  const wrap = document.getElementById(wrapId);
  // no duplicates
  const existing = [...wrap.querySelectorAll('.tag')].map(t => t.textContent.replace('\u00d7','').trim());
  if (existing.includes(value)) return;
  const tag = document.createElement('span');
  tag.className = 'tag';
  tag.innerHTML = value + ' <button onclick="removeTag(this)">&times;</button>';
  wrap.insertBefore(tag, wrap.querySelector('.tag-input'));
}

function getTags(wrapId) {
  return [...document.getElementById(wrapId).querySelectorAll('.tag')]
    .map(t => t.textContent.replace('\u00d7','').trim())
    .filter(Boolean);
}

function getChecked(containerId) {
  return [...document.querySelectorAll('#' + containerId + ' input:checked')].map(c => c.value);
}

// wire up tag inputs
document.querySelectorAll('.tag-input').forEach(input => {
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(input.parentElement.id, input.value);
      input.value = '';
    }
  });
});

/* ── quiz options toggle ── */
function toggleQuizOpts() {
  document.getElementById('quiz-opts').style.display =
    document.getElementById('cb-quiz').checked ? 'block' : 'none';
}

/* ── run ── */
let polling = null;

function run() {
  const pdf = document.getElementById('pdf').value.trim();
  if (!pdf) { alert('Please enter a PDF file path on the Convert tab.'); return; }

  const btn = document.getElementById('run');
  btn.disabled = true;
  btn.textContent = 'Running\u2026';

  const logWrap = document.getElementById('log-wrap');
  const log = document.getElementById('log');
  logWrap.style.display = 'block';
  log.textContent = '';

  const p = new URLSearchParams();

  // ── Convert tab ──
  p.set('pdf_path', pdf);
  const lbl = document.getElementById('lbl').value.trim();
  if (lbl) p.set('label', lbl);
  const lang = document.getElementById('lang').value;
  if (lang !== 'auto') p.set('input_language', lang);

  const outLangs = getTags('out-langs-wrap');
  if (outLangs.length) p.set('output_languages', JSON.stringify(outLangs));

  document.querySelectorAll('#tab-convert .checks input:checked').forEach(cb => {
    if (cb.dataset.key) p.set(cb.dataset.key, cb.dataset.val);
  });

  const ps = document.getElementById('pstart').value.trim();
  const pe = document.getElementById('pend').value.trim();
  if (ps !== '0' || pe !== '0') {
    p.set('page_range.start', ps || '0');
    p.set('page_range.end', pe || '0');
  }

  // ── Speech tab ──
  p.set('speech.provider', document.getElementById('speech-provider').value);
  p.set('speech.format', document.getElementById('speech-format').value);
  p.set('speech.bit_rate', document.getElementById('speech-bitrate').value);
  p.set('speech.sample_rate', document.getElementById('speech-samplerate').value);
  p.set('speech.providers.openai.model', document.getElementById('openai-model').value);
  p.set('speech.providers.azure.model', document.getElementById('azure-model').value);

  const oaiLangs = getTags('openai-langs-wrap');
  if (oaiLangs.length) p.set('speech.providers.openai.languages', JSON.stringify(oaiLangs));
  const azLangs = getTags('azure-langs-wrap');
  if (azLangs.length) p.set('speech.providers.azure.languages', JSON.stringify(azLangs));

  // ── Render tab ──
  p.set('render_strategy', document.getElementById('render-strategy').value);
  p.set('page_grouping', document.getElementById('page-grouping').value);

  // ── Filters tab ──
  p.set('image_filters.size.max_side', document.getElementById('img-max').value);
  p.set('image_filters.size.min_side', document.getElementById('img-min').value);
  p.set('image_filters.blank.threshold', document.getElementById('img-blank').value);

  const prunedText = getChecked('pruned-text-checks');
  p.set('text_filters.pruned_text_types', JSON.stringify(prunedText));
  const prunedSec = getChecked('pruned-section-checks');
  p.set('section_filters.pruned_section_types', JSON.stringify(prunedSec));
  const quizSec = getChecked('quiz-section-checks');
  p.set('section_filters.quiz_count_section_types', JSON.stringify(quizSec));

  // ── Advanced tab ──
  p.set('default_model', document.getElementById('default-model').value);
  const outDir = document.getElementById('output-dir').value.trim();
  if (outDir && outDir !== 'output') p.set('output_dir', outDir);
  const customPlate = document.getElementById('custom-plate').value.trim();
  if (customPlate) p.set('custom_plate_path', customPlate);
  p.set('prompts.section_quiz.sections_per_quiz', document.getElementById('quiz-per').value);

  fetch('/run', { method: 'POST', body: p })
    .then(r => r.json())
    .then(data => {
      if (data.error) { log.textContent = 'ERROR: ' + data.error; btn.disabled = false; btn.textContent = 'Run Conversion'; return; }
      pollLog();
    })
    .catch(err => { log.textContent = 'Request failed: ' + err; btn.disabled = false; btn.textContent = 'Run Conversion'; });
}

function pollLog() {
  if (polling) clearInterval(polling);
  let seen = 0;
  const log = document.getElementById('log');
  polling = setInterval(() => {
    fetch('/log?offset=' + seen)
      .then(r => r.json())
      .then(data => {
        if (data.lines.length) {
          seen += data.lines.length;
          log.textContent += data.lines.join('');
          log.scrollTop = log.scrollHeight;
        }
        if (!data.running && data.lines.length === 0) {
          clearInterval(polling);
          polling = null;
          const btn = document.getElementById('run');
          btn.disabled = false;
          btn.textContent = 'Run Conversion';
        }
      });
  }, 400);
}
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/" or self.path == "":
            self._send(200, "text/html", HTML_PAGE.encode())
        elif self.path.startswith("/log"):
            offset = 0
            if "?" in self.path:
                qs = parse_qs(self.path.split("?", 1)[1])
                offset = int(qs.get("offset", ["0"])[0])
            with _lock:
                lines = _log_lines[offset:]
                running = _running
            self._send(200, "application/json", json.dumps({"lines": lines, "running": running}).encode())
        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self) -> None:
        global _running
        if self.path != "/run":
            self._send(404, "text/plain", b"Not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        pdf_path = params.get("pdf_path", [""])[0]
        if not pdf_path:
            self._send(400, "application/json", json.dumps({"error": "pdf_path is required"}).encode())
            return

        cmd = ["uv", "run", "adt-press.py", f"pdf_path={pdf_path}"]

        # Simple key=value params (skip pdf_path, already added; skip list/json params)
        SIMPLE_KEYS = [
            "label", "input_language",
            "glossary_strategy", "explanation_strategy", "easy_read_strategy",
            "caption_strategy", "crop_strategy", "activity_strategy",
            "quiz_strategy", "speech_strategy",
            "render_strategy", "page_grouping",
            "default_model", "output_dir", "custom_plate_path",
            "speech.provider", "speech.format", "speech.bit_rate", "speech.sample_rate",
            "speech.providers.openai.model", "speech.providers.azure.model",
            "image_filters.size.max_side", "image_filters.size.min_side",
            "image_filters.blank.threshold",
            "prompts.section_quiz.sections_per_quiz",
        ]
        for key in SIMPLE_KEYS:
            val = params.get(key, [""])[0]
            if val:
                cmd.append(f"{key}={val}")

        # Page range
        ps = params.get("page_range.start", ["0"])[0]
        pe = params.get("page_range.end", ["0"])[0]
        if ps != "0" or pe != "0":
            cmd.append(f"page_range.start={ps}")
            cmd.append(f"page_range.end={pe}")

        # List params (sent as JSON arrays)
        for key in [
            "output_languages",
            "speech.providers.openai.languages",
            "speech.providers.azure.languages",
            "text_filters.pruned_text_types",
            "section_filters.pruned_section_types",
            "section_filters.quiz_count_section_types",
        ]:
            raw = params.get(key, [""])[0]
            if raw:
                try:
                    items = json.loads(raw)
                    cmd.append(f"{key}={json.dumps(items)}")
                except json.JSONDecodeError:
                    pass

        with _lock:
            if _running:
                self._send(409, "application/json", json.dumps({"error": "A conversion is already running."}).encode())
                return
            _running = True
            _log_lines.clear()
            _log_lines.append(f"$ {' '.join(cmd)}\n\n")

        threading.Thread(target=_run_process, args=(cmd,), daemon=True).start()
        self._send(200, "application/json", json.dumps({"ok": True}).encode())

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


def _run_process(cmd: list[str]) -> None:
    global _running
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=SCRIPT_DIR)
        assert proc.stdout is not None
        for line in proc.stdout:
            with _lock:
                _log_lines.append(line)
        proc.wait()
        with _lock:
            _log_lines.append(f"\n{'=' * 40}\nProcess finished (exit code {proc.returncode}).\n")
    except Exception as exc:
        with _lock:
            _log_lines.append(f"\nERROR: {exc}\n")
    finally:
        with _lock:
            _running = False


def main() -> None:
    port = 8471
    server = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"ADT Press Wizard running at {url}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
