# PII Redactor

A multilingual, context-aware PII redaction tool that removes sensitive information from PDF documents (not just masking — the data is truly deleted). Supports regex, LLM validation, and is designed to handle tables, addresses split across lines, and multiple languages.

---

## Features

- Deletes underlying PII text from PDFs (not just black-box masking)
- Supports multilingual documents via auto language detection
- Uses regex + LLM (OpenAI or local model) for high-accuracy PII detection
- Handles complex PDF structures (tables, line-breaks, blocks)
- CLI interface for simple usage
- Unit + E2E tested with real examples

---

## Installation

### Clone and install locally:
```bash
git clone https://github.com/yourusername/pii-redaction-tool.git
cd pii-redaction-tool
python -m venv venv
venv\Scripts\activate   # On Windows
# OR
source venv/bin/activate   # On macOS/Linux

pip install -r requirements.txt
```

### Requirements
- Python 3.8+
- Optional: `.env` file with `OPENAI_API_KEY`
- See `requirements.txt` for exact dependencies.

---

## Usage

### From CLI:
```bash
pii-redactor input.pdf -o output_redacted.pdf
```

### Run Tests:
```bash
pytest tests/
```

---

## Project Structure

```bash
pii-redaction-tool/
├── src/              # Core modules
│   ├── main.py       # CLI entry point
│   ├── pdf_processor.py
│   ├── pii_detector.py
│   ├── redactor.py
│   ├── utils.py
│   └── ...
├── tests/            # Test cases
├── requirements.txt
├── README.md
└── .gitignore
```
---

## Approach & Design Decisions

### Detection Pipeline
1. Extract full text blocks from each PDF page
2. Detect language using `langdetect`
3. Run regex patterns for common PII (emails, phones, CCs, etc.)
4. Pass detected + raw text to LLM (OpenAI GPT-4 or local LLaMA) for validation and context expansion

### Redaction
- Use PyMuPDF to search for each PII string, accounting for multi-line or fragmented matches
- Redact using white-fill, then **permanently delete underlying text** with `apply_redactions()`
- Sanitize output: strip metadata, compress, clean PDF

---

## Limitations

- Does not support scanned image PDFs (OCR not implemented yet)
- LLM may miss or hallucinate PII on rare edge cases
- Performance may degrade with large PDFs if using cloud LLMs
- Requires an OpenAI API key for GPT

---

## Potential Improvements

- [ ] Add OCR (Tesseract or PaddleOCR) for image-based PII detection
- [ ] Use fast local models (e.g., `phi`, `mistral`) for offline LLM
- [ ] Add streaming PDF reader for memory efficiency
- [ ] Add UI for non-tech users (Flask or Streamlit)
- [ ] Annotated preview of redacted content

---

## License
This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Credits
Created by [Manjusha Raavi](https://github.com/manjuraavi)