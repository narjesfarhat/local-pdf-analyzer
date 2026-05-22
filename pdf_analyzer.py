"""
=============================================================
  Multimodal PDF Analyzer  —  100% FREE / LOCAL (NO VISION MODEL)
=============================================================
Extracts and analyzes from any PDF:
  ✅ Text          (pdfplumber)
  ✅ Tables        (pdfplumber)
  ✅ Images metadata (PyMuPDF only)
  ✅ Bar graphs    (STRUCTURE → Phi-3 / Qwen reasoning)
  ✅ Histograms    (STRUCTURE → Phi-3 / Qwen reasoning)

NO LLaVA / NO VISION MODEL REQUIRED

FIXES APPLIED:
  ✅ Retry logic with backoff on timeout
  ✅ Batch processing with Ollama restart every 10 pages
  ✅ Resume support — skips already-processed pages

REQUIREMENTS:
  pip install pymupdf pdfplumber requests

  Ollama:
    ollama pull phi3
    or
    ollama pull qwen2.5

USAGE:
  python pdf_multimodal_analyzer.py file.pdf
  python pdf_multimodal_analyzer.py file.pdf --pages 1-5
  python pdf_multimodal_analyzer.py file.pdf --pages 34-46   ← resume from page 34
=============================================================
"""

import sys
import os
import time
import argparse
import json
import subprocess
import requests
import pdfplumber
import fitz  # PyMuPDF

# ──────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/generate"
TEXT_MODEL = "qwen2.5:0.5b"
OUTPUT_FILE = "analysis_output.txt"
BATCH_SIZE = 10  # restart Ollama every N pages
LLM_TIMEOUT = 180  # seconds per request
LLM_RETRIES = 2  # how many times to retry a timed-out page
RETRY_DELAY = 10  # seconds to wait between retries


# ──────────────────────────────────────────────────────────
# STEP 1 — TEXT EXTRACTION
# ──────────────────────────────────────────────────────────
def extract_text(pdf_path: str, page_numbers: list[int]) -> dict[int, str]:
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i in page_numbers:
            if i < len(pdf.pages):
                text = pdf.pages[i].extract_text() or ""
                results[i + 1] = text.strip()
    return results


# ──────────────────────────────────────────────────────────
# STEP 2 — TABLE EXTRACTION
# ──────────────────────────────────────────────────────────
def extract_tables(pdf_path: str, page_numbers: list[int]) -> dict[int, list]:
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i in page_numbers:
            if i < len(pdf.pages):
                tables = pdf.pages[i].extract_tables()
                if tables:
                    results[i + 1] = tables
    return results


def format_table(table: list) -> str:
    if not table:
        return ""
    col_widths = []
    for col_idx in range(len(table[0])):
        width = max(len(str(row[col_idx]) if row[col_idx] else "") for row in table)
        col_widths.append(width)

    lines = []
    for row in table:
        cells = [str(cell or "").ljust(col_widths[j]) for j, cell in enumerate(row)]
        lines.append(" | ".join(cells))

    separator = "-+-".join("-" * w for w in col_widths)
    lines.insert(1, separator)
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────
# STEP 3 — LLM CALL with RETRY LOGIC
# ──────────────────────────────────────────────────────────
def ask_llm(prompt: str, retries: int = LLM_RETRIES) -> str:
    payload = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    for attempt in range(retries + 1):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=LLM_TIMEOUT)
            r.raise_for_status()
            return r.json().get("response", "").strip()

        except requests.exceptions.ReadTimeout:
            if attempt < retries:
                print(
                    f"  ⚠ Timeout on attempt {attempt + 1}/{retries + 1}, "
                    f"waiting {RETRY_DELAY}s then retrying..."
                )
                time.sleep(RETRY_DELAY)
            else:
                return "LLM error: timed out after all retries — skipped"

        except Exception as e:
            return f"LLM error: {e}"


# ──────────────────────────────────────────────────────────
# STEP 4 — OLLAMA RESTART (clears memory between batches)
# ──────────────────────────────────────────────────────────
def restart_ollama():
    print(f"\n  🔄 Restarting Ollama to free memory...")
    try:
        subprocess.run(["ollama", "stop", TEXT_MODEL], capture_output=True, timeout=30)
        time.sleep(5)
        print("  ✅ Ollama restarted\n")
    except Exception as e:
        print(f"  ⚠ Could not restart Ollama: {e} — continuing anyway\n")


# ──────────────────────────────────────────────────────────
# STEP 5 — RESUME SUPPORT (skip already-done pages)
# ──────────────────────────────────────────────────────────
def already_processed(output_file: str, page_num: int) -> bool:
    if not os.path.exists(output_file):
        return False
    with open(output_file, "r", encoding="utf-8") as f:
        return f"PAGE {page_num}\n" in f.read()


# ──────────────────────────────────────────────────────────
# STEP 6 — STRUCTURE EXTRACTION (NO VISION)
# ──────────────────────────────────────────────────────────
def extract_page_structure(pdf_path: str, page_index: int):
    doc = fitz.open(pdf_path)
    page = doc[page_index]

    images = page.get_images(full=True)
    drawings = page.get_drawings()
    text = page.get_text("text")

    doc.close()

    return {
        "num_images": len(images),
        "num_drawings": len(drawings),
        "text_snippet": text[:1500],
    }


# ──────────────────────────────────────────────────────────
# STEP 7 — ANALYSIS (TEXT + TABLES + STRUCTURE → LLM)
# ──────────────────────────────────────────────────────────
def analyze_page_with_llm(page_num, text, tables, structure):
    prompt = f"""
You are analyzing a research PDF page.
 
You do NOT see images. You only see extracted structure.
 
Your job:
- infer what figures/charts likely represent
- interpret tables
- detect trends or comparisons
- explain insights clearly
 
PAGE DATA:
 
TEXT:
{text[:800]} 
 
TABLES:
{json.dumps(tables, indent=2)}
 
STRUCTURE METADATA:
{json.dumps(structure, indent=2)}
 
Now explain:
1. What this page is about
2. What charts/figures likely represent
3. Key numeric or comparative insights
4. Any trends or conclusions
"""
    return ask_llm(prompt)


# ──────────────────────────────────────────────────────────
# MAIN ANALYZER
# ──────────────────────────────────────────────────────────
def analyze_pdf(pdf_path: str, page_range=None):
    if not os.path.exists(pdf_path):
        print("File not found")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    if page_range is None:
        page_indices = list(range(total_pages))
    else:
        page_indices = [p - 1 for p in page_range]

    print(f"\nPDF pages : {total_pages}")
    print(f"Analyzing : {[p + 1 for p in page_indices]}")
    print(f"Batch size: {BATCH_SIZE} pages → Ollama restarts between batches")
    print(f"Output    : {OUTPUT_FILE}  (append mode — safe to resume)\n")

    texts = extract_text(pdf_path, page_indices)
    tables = extract_tables(pdf_path, page_indices)

    # ── process in batches ──────────────────────────────
    for batch_start in range(0, len(page_indices), BATCH_SIZE):
        batch = page_indices[batch_start : batch_start + BATCH_SIZE]

        for idx in batch:
            page_num = idx + 1
            text = texts.get(page_num, "")
            page_tables = tables.get(page_num, [])
            structure = extract_page_structure(pdf_path, idx)

            # ── resume: skip if already in output file ──
            if already_processed(OUTPUT_FILE, page_num):
                print(f"  ↩ Page {page_num} already processed — skipping")
                continue

            print(f"  Processing page {page_num}...")
            llm_result = analyze_page_with_llm(page_num, text, page_tables, structure)

            # ── append result immediately (safe on crash) ──
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"PAGE {page_num}\n")
                f.write(llm_result)
                f.write("\n")

            print(f"  ✅ Page {page_num} saved")

        # ── restart Ollama after each batch (except last) ──
        batch_end = batch_start + BATCH_SIZE
        if batch_end < len(page_indices):
            restart_ollama()

    print("\n✅ DONE — results saved to", OUTPUT_FILE)


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────
def parse_page_arg(page_str):
    pages = []
    for part in page_str.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--pages", default=None)

    args = parser.parse_args()

    page_range = parse_page_arg(args.pages) if args.pages else None
    analyze_pdf(args.pdf, page_range)
