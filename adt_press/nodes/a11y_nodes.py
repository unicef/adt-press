import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from adt_press.models.config import TemplateConfig
from adt_press.utils.html import render_template


def _write_package_json(work_dir: Path) -> None:
    pkg = work_dir / "package.json"

    base = {
        "type": "module",
        "dependencies": {
            "@guidepup/virtual-screen-reader": "^0.32.1",
            "jsdom": "^24.1.0",
            "axe-core": "^4.9.0",
            "canvas": "^2.11.2",
        },
    }

    if pkg.exists():
        try:
            current = json.loads(pkg.read_text())
        except Exception:
            current = {}
        deps = current.get("dependencies", {})
        deps.update(base["dependencies"])
        current["dependencies"] = deps
        current.setdefault("type", "module")
        pkg.write_text(json.dumps(current, indent=2))
    else:
        pkg.write_text(json.dumps(base, indent=2))


def adt_a11y_results(run_output_dir_config: str, package_adt_web: str) -> dict[str, Any]:
    """
    Run a lightweight WCAG smoke test over generated ADT HTML pages using
    @guidepup/virtual-screen-reader.

    Args:
        run_output_dir_config: Output directory of the pipeline (contains adt/).
        package_adt_web: Dependency to ensure ADT pages are generated before running.

    Returns:
        Parsed JSON results produced by the node script.
    """

    run_dir = Path(run_output_dir_config).resolve()
    adt_dir = run_dir / "adt"
    results_path = run_dir / "adt_a11y_report.json"

    work_dir = run_dir / ".a11y_runner"
    work_dir.mkdir(parents=True, exist_ok=True)
    _write_package_json(work_dir)

    # Ensure JS dependencies are present (installed once per run_output_dir)
    try:
        subprocess.run(["npm", "install"], cwd=work_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - surfaced to caller
        return {"error": f"npm install failed: {exc.stderr.decode() if exc.stderr else exc}"}

    script = """
import fs from 'fs';
import path from 'path';
import { JSDOM } from 'jsdom';
import { virtual } from '@guidepup/virtual-screen-reader';

const [,, adtDir, resultsPath] = process.argv;

async function tabThrough(doc, maxSteps = 150) {
  const phrases = [];
  try {
    await virtual.start({ container: doc.body });

    for (let i = 0; i < maxSteps; i++) {
      await virtual.next();
      const phrase = await virtual.lastSpokenPhrase();
      if (!phrase) break;
      if (phrase.toLowerCase() === 'end of document') { phrases.push(phrase); break; }
      // stop if we keep repeating
      if (phrases.length && phrases[phrases.length - 1] === phrase) {
        if (phrases.length > 5 && phrases.slice(-5).every(p => p === phrase)) break;
      }
      phrases.push(phrase);
    }
  } catch (error) {
    return { error: String(error) };
  } finally {
    try { await virtual.stop(); } catch (e) { /* ignore */ }
  }

  return { phrases };
}

function collectHtmlFiles(dir) {
  const results = [];
  const stack = [dir];
  while (stack.length) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.html') && !entry.name.startsWith('test-zoom')) {
        results.push(fullPath);
      }
    }
  }
  return results;
}

async function readPage(filePath) {
  const html = fs.readFileSync(filePath, 'utf-8');
  const dom = new JSDOM(html, { url: 'file://' + filePath });
  global.window = dom.window;
  global.document = dom.window.document;
  global.Node = dom.window.Node;

  const tabResult = await tabThrough(dom.window.document, 150);

  // cleanup globals to avoid leaks between pages
  delete global.window;
  delete global.document;
  delete global.Node;

  return { file: filePath, ...(tabResult.error ? { error: tabResult.error } : { phrases: tabResult.phrases }) };
}

async function main() {
  const files = collectHtmlFiles(adtDir);
  const results = [];
  for (const file of files) {
    results.push(await readPage(file));
  }
  fs.writeFileSync(resultsPath, JSON.stringify({ files: results }, null, 2));
}

main();
"""

    run_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, dir=work_dir) as f:
        f.write(script)
        script_path = Path(f.name)

    try:
        subprocess.run(
            ["node", str(script_path), str(adt_dir), str(results_path)],
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - surfaced to pipeline
        return {"error": exc.stderr or str(exc)}
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except OSError:
            pass

    if results_path.exists():
        return cast(dict[str, Any], json.loads(results_path.read_text()))
    return {"error": "results file not found"}


def adt_aria_at_results(run_output_dir_config: str, package_adt_web: str) -> dict[str, Any]:
    """Run lightweight ARIA-AT-inspired checks against generated ADT pages.

    This is not the full ARIA-AT harness, but exercises common expectations:
    - presence of landmarks (main, nav)
    - headings hierarchy
    - form controls have accessible names
    - virtual screen reader phrases for the first few tabbable elements
    """

    run_dir = Path(run_output_dir_config).resolve()
    adt_dir = run_dir / "adt"
    results_path = run_dir / "adt_aria_at_report.json"

    work_dir = run_dir / ".a11y_runner"
    work_dir.mkdir(parents=True, exist_ok=True)
    _write_package_json(work_dir)

    try:
        subprocess.run(["npm", "install"], cwd=work_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        return {"error": f"npm install failed: {exc.stderr.decode() if exc.stderr else exc}"}

    script = """
import fs from 'fs';
import path from 'path';
import { JSDOM } from 'jsdom';
import { virtual } from '@guidepup/virtual-screen-reader';

const [,, adtDir, resultsPath] = process.argv;

function collectHtmlFiles(dir) {
  const results = [];
  const stack = [dir];
  while (stack.length) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.html') && !entry.name.startsWith('test-zoom')) {
        results.push(fullPath);
      }
    }
  }
  return results;
}

function headingLevels(doc) {
  return Array.from(doc.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(h => parseInt(h.tagName[1], 10));
}

function landmarks(doc) {
  return {
    hasMain: !!doc.querySelector('main'),
    hasNav: !!doc.querySelector('nav'),
  };
}

function controlsWithNames(doc) {
  const controls = Array.from(doc.querySelectorAll('input,select,textarea,button')); 
  return controls.map(ctrl => {
    const label = ctrl.getAttribute('aria-label') || ctrl.getAttribute('aria-labelledby');
    const id = ctrl.id || ctrl.name || ctrl.type;
    return { id, hasName: !!label };
  });
}

async function tabThrough(doc, maxSteps = 50) {
  const phrases = [];
  try {
    await virtual.start({ container: doc.body });
    for (let i = 0; i < maxSteps; i++) {
      await virtual.next();
      const phrase = await virtual.lastSpokenPhrase();
      if (!phrase) break;
      if (phrase.toLowerCase() === 'end of document') { phrases.push(phrase); break; }
      if (phrases.length && phrases[phrases.length - 1] === phrase) {
        if (phrases.length > 5 && phrases.slice(-5).every(p => p === phrase)) break;
      }
      phrases.push(phrase);
    }
  } catch (error) {
    return { error: String(error) };
  } finally {
    try { await virtual.stop(); } catch (e) { /* ignore */ }
  }
  return { phrases };
}

async function analyze(filePath) {
  const html = fs.readFileSync(filePath, 'utf-8');
  const dom = new JSDOM(html, { url: 'file://' + filePath, pretendToBeVisual: true });

  // Establish globals *before* loading axe so it can detect the environment.
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  globalThis.Node = dom.window.Node;
  global.window = dom.window;
  global.document = dom.window.document;
  global.Node = dom.window.Node;

  // Provide real canvas via node-canvas to satisfy axe color-contrast internals.
  const { createCanvas, Image, ImageData } = await import('canvas');
  globalThis.Image = Image;
  globalThis.ImageData = ImageData;
  const HTMLCanvasElement = dom.window.HTMLCanvasElement;
  if (HTMLCanvasElement) {
    HTMLCanvasElement.prototype.getContext = function getContext(type) {
      return createCanvas(1, 1).getContext(type);
    };
  }

  // Run axe for WCAG 2.x A/AA rules.
  const axeModule = await import('axe-core');
  const axeSource = axeModule.source || axeModule.default?.source;
  // Initialize axe inside this JSDOM window to avoid stale globals across pages.
  dom.window.eval(axeSource);
  const axe = dom.window.axe;
  // Use configure instead of inline rules to avoid shape/validation errors.
  await axe.configure({
    rules: [{ id: 'color-contrast', enabled: true}],
  });

  let axeResults;
  try {
    axeResults = await axe.run(dom.window.document, {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice', 'cat.color', 'cat.semantics', 'cat.time-and-media', 'cat.tables', 'cat.keyboard', 'cat.sensory-and-visual-cues', 'cat.forms', 'cat.text-alternatives'],
      },
    });
  } catch (error) {
    axeResults = { error: String(error) };
  }

  const doc = dom.window.document;
  const headings = headingLevels(doc);
  const lm = landmarks(doc);
  const controls = controlsWithNames(doc);
  const tabResult = await tabThrough(doc);

  return { file: filePath, headings, landmarks: lm, controls, tabResult, axe: axeResults };
}

async function main() {
  const files = collectHtmlFiles(adtDir);
  const results = [];
  for (const file of files) {
    results.push(await analyze(file));
  }
  fs.writeFileSync(resultsPath, JSON.stringify({ files: results }, null, 2));
}

main();
"""

    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, dir=work_dir) as f:
        f.write(script)
        script_path = Path(f.name)

    try:
        subprocess.run(
            ["node", str(script_path), str(adt_dir), str(results_path)],
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        return {"error": exc.stderr or str(exc)}
    finally:
        script_path.unlink(missing_ok=True)

    if results_path.exists():
        return cast(dict[str, Any], json.loads(results_path.read_text()))
    return {"error": "results file not found"}


def adt_aria_at_report(template_config: TemplateConfig, adt_aria_at_results: dict[str, Any]) -> str:
    files = list(adt_aria_at_results.get("files", [])) if isinstance(adt_aria_at_results, dict) else []
    return render_template(
        template_config,
        "templates/adt_aria_at_report.html",
        dict(results=adt_aria_at_results, files=files),
    )


def adt_a11y_report(template_config: TemplateConfig, adt_a11y_results: dict[str, Any]) -> str:
    """Render a simple HTML report summarizing screen reader phrases per page."""

    return render_template(
        template_config,
        "templates/adt_a11y_report.html",
        dict(results=adt_a11y_results),
    )
