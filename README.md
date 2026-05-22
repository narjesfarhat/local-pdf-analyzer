# 📄 Local PDF Analyzer

A multimodal PDF analyzer that extracts and analyzes **text, tables, and figures** from any PDF using a fully local LLM via Ollama.

> No API keys. No cloud. No vision model. 100% private.

---

## ✨ Features

- ✅ Text extraction per page
- ✅ Table extraction and formatting
- ✅ Figure/chart structure inference (no vision model needed)
- ✅ Local LLM analysis via Ollama (phi3, qwen2.5)
- ✅ Batch processing with automatic memory management
- ✅ Resume support — safely continues after crashes
- ✅ Retry logic with backoff on timeout

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| `pdfplumber` | Text and table extraction |
| `PyMuPDF (fitz)` | Page structure and image metadata |
| `Ollama` | Local LLM inference |
| `qwen2.5:0.5b` | Default analysis model |
| `Python 3.10+` | Core language |

---

## ⚙️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/local-pdf-analyzer.git
cd local-pdf-analyzer
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install pymupdf pdfplumber requests
```

**4. Install Ollama and pull the model**

Download Ollama from https://ollama.com then run:
```bash
ollama pull qwen2.5:0.5b
```

---

## 🚀 Usage

**Analyze a full PDF:**
```bash
python pdf_analyzer.py yourfile.pdf
```

**Analyze specific pages only:**
```bash
python pdf_analyzer.py yourfile.pdf --pages 1-10
```

**Resume after a crash:**
```bash
python pdf_analyzer.py yourfile.pdf
```
Already-processed pages are automatically skipped.

**Clean error pages and reprocess:**
```bash
python clean_errors.py
python pdf_analyzer.py yourfile.pdf
```

---

## 📁 Project Structure

```
local-pdf-analyzer/
├── pdf_analyzer.py       # Main analyzer
├── clean_errors.py       # Removes failed pages from output
├── analysis_output.txt   # Generated analysis (auto-created)
└── README.md
```

---

## 🔧 Configuration

At the top of `pdf_analyzer.py` you can adjust:

```python
TEXT_MODEL  = "qwen2.5:0.5b"  # or "phi3", "qwen2.5"
BATCH_SIZE  = 10               # pages before Ollama restarts
LLM_TIMEOUT = 180              # seconds per request
LLM_RETRIES = 2                # retries on timeout
```

---

## 💡 How It Works

1. **Extract** — pdfplumber pulls text and tables from each page
2. **Structure** — PyMuPDF counts images and drawings per page
3. **Analyze** — all extracted data is sent as a structured prompt to the local LLM
4. **Save** — results are appended to `analysis_output.txt` page by page

The model never sees the actual images — it reasons about charts and figures from surrounding text and structural metadata. This makes it work on any machine without a GPU.

---

## 📋 Requirements

- Python 3.10+
- Ollama installed and running
- 4GB+ RAM recommended

---

## 🙋 Author

Built by [Narjes Farhat](https://github.com/narjesfarhat)  
[Portfolio](https://narjesf.wordpress.com) · [LinkedIn](https://linkedin.com/in/narjesfarhat)
