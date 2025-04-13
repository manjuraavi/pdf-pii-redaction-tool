# 📄 PDF PII Redactor Tool

A multilingual, context-aware PII redaction tool that removes sensitive information from PDF documents (not just masking — the data is truly deleted) ensuring thorough privacy protection. 

## 📚 Table of Contents

- [✨ Features](#features)
- [⚙️ Installation](#installation)
- [📖 Usage Guide](#usage-guide)
  - [💻 Command Line Interface](#command-line-interface)
  - [🌐 Web Interface](#web-interface)
  - [📊 Evaluation Mode](#evaluation-mode)
  - [🧪 Running Tests](#running-tests)
- [📂 Code Structure](#code-structure)
- [🛠️ Technical Approach](#technical-approach)
  - [🏗️ Architecture](#architecture)
  - [🔍 PII Detection Methodology](#pii-detection-methodology)
  - [🖍️ Redaction Process](#redaction-process)
- [🔑 PII Types Detected](#pii-types-detected)
- [💡 Design Decisions](#design-decisions)
- [⚠️ Limitations](#limitations)
- [🚀 Future Improvements](#future-improvements)
- [📜 License](#license)
- [🙌 Credits](#credits)

## ✨ Features

- **Comprehensive PII Detection**: Identifies a wide range of personal information including names, email addresses, phone numbers, addresses, IDs, and more
- **Hybrid Detection Approach**: Combines regex pattern matching with LLM-based detection for improved accuracy
- **PDF Processing**: Works with standard PDFs containing selectable text
- **Multiple Interfaces**: Use via command line or web interface
- **Evaluation Capabilities**: Compare redaction results with ground truth for quality assessment
- **Multi-language Support**: Detects PII in multiple languages
- **Progress Tracking**: Real-time progress and logging information
- **Customizable Output**: Save redacted PDFs with your preferred naming convention

## ⚙️ Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Option 1: Install from GitHub (Recommended)
Install the PII Redactor tool directly from GitHub:

```bash    
pip install git+https://github.com/manjuraavi/pdf-pii-redaction-tool.git
```

Set up your OpenAI API key:
   - Option A: Create a `.env` file in the project root with:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - Option B: Set it as an environment variable:
     ```bash
     export OPENAI_API_KEY=your_api_key_here  # On Windows: set OPENAI_API_KEY=your_api_key_here 
     ```

Then you can run the tool with:

```bash
pii-redactor /path/to/your/document.pdf
```

### Option 2: Clone and run locally (for devs):
Run the tool locally for development or customization purposes

1. Clone the repository:
   ```bash
   git clone https://github.com/manjuraavi/pdf-pii-redaction-tool.git
   cd pdf-pii-redaction-tool
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows
    # OR
    source venv/bin/activate   # On macOS/Linux

   ```

3. Install the package and dependencies:
   ```bash
   pip install -r requirements.txt

   pip install -e .
   ```

4. Set up your OpenAI API key:
   - Option A: Create a `.env` file in the project root with:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - Option B: Set it as an environment variable:
     ```bash
     export OPENAI_API_KEY=your_api_key_here  # On Windows: set OPENAI_API_KEY=your_api_key_here
     ```

## 📖 Usage Guide

### 💻 Command Line Interface

Redact a PDF:

```bash
pii-redactor /path/to/your/document.pdf
```

The redacted document will be saved to the `output` directory with a default name.

Save to a custom location:

```bash
pii-redactor /path/to/your/document.pdf -o /path/to/output/redacted.pdf
```

Enable verbose logging:

```bash
pii-redactor /path/to/your/document.pdf -v
```

### 🌐 Web Interface

Launch the Streamlit web application:

```bash
pii-redactor --web
```

Then:
1. Open your browser to the URL shown in the terminal (typically http://localhost:8501)
2. Enter your OpenAI API key in the sidebar (if not set in environment)
3. Upload a PDF document
4. Click "Redact PII"
5. Download the redacted PDF when processing is complete

### 📊 Evaluation Mode

To evaluate redaction against a ground truth file:

1. In CLI:

```bash
pii-redactor /path/to/document.pdf -e -gt /path/to/ground_truth.json
```

Ground truth format (JSON):

```json
{
  "pii": [
    {"type": "name", "text": "John Doe", "page": 1},
    {"type": "email", "text": "john.doe@example.com", "page": 1},
    {"type": "phone", "text": "123-456-7890", "page": 2}
  ]
}
```

2. In the web interface, enable the "Enable Evaluation" checkbox in advanced options and upload a ground truth file.

### 🧪 Running Tests

The project includes comprehensive tests to ensure functionality works as expected:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test modules
pytest tests/test_pii_detector.py
pytest tests/test_redactor.py

# Run with coverage report
pytest --cov=pii_redactor
```

## 📂 Code Structure

The project follows a modular architecture with clear separation of concerns:

```
pii-redactor/
├── pii_redactor/                # Main package
│   ├── __init__.py
│   ├── main.py                   # Command line interface
│   ├── redactor.py              # Core redaction functionality
│   ├── pii_detector.py          # PII detection logic
│   ├── pdf_processor.py         # PDF handling
│   ├── evaluate_metrics.py      # Evaluation functionality
│   ├── utils.py                 # Utility functions
│   ├── streamlit_app.py         # Web interface
├── tests/                       # Test suite
├── output/                      # Default output directory
├── logs/                        # Log files
├── README.md
├── LICENSE
├── setup.py
└── requirements.txt
```

### Core Files and Their Functions

- **redactor.py**: Main class that orchestrates the PDF redaction process, locating PII within pages and applying redactions
- **pii_detector.py**: Implements PII detection using regex patterns and LLM validation/expansion
- **pdf_processor.py**: Handles PDF operations like text extraction and content manipulation
- **evaluate_metrics.py**: Provides functionality to evaluate redaction quality against ground truth

## 🛠️ Technical Approach

### 🏗️ Architecture

The PII Redactor Tool is built with a modular architecture that separates concerns:

1. **PDF Processing**: Handles PDF parsing and text extraction
2. **PII Detection**: Identifies sensitive information using pattern matching and AI
3. **Redaction**: Applies visual redactions to the PDF
4. **Evaluation**: Measures the quality of redaction against ground truth

### 🔍 PII Detection Methodology

The tool uses a multi-layered approach to PII detection:

1. **Regex Pattern Matching**: Fast first-pass detection for common PII patterns
2. **Validation Rules**: Domain-specific rules to reduce false positives (e.g., Luhn algorithm for credit cards)
3. **LLM Enhancement**: Large Language Model (OpenAI's GPT-4) to detect complex or contextual PII
4. **Language Detection**: Adapts detection based on document language

This hybrid approach achieves a balance between precision and recall, using computationally less expensive methods first before engaging the more powerful but resource-intensive LLM.

### 🖍️ Redaction Process

The redaction workflow consists of several steps:

1. **Extract Text**: Parse the PDF to extract text while preserving layout information
2. **Detect PII**: Apply the detection pipeline to identify sensitive information
3. **Locate Text**: Find the exact position of PII text on each page with awareness of text fragmentation
4. **Apply Redactions**: Add redaction annotations over the identified areas
5. **Sanitize Metadata**: Remove document metadata that might contain sensitive information
6. **Save Output**: Generate the redacted PDF with all sensitive information obscured

## 🔑 PII Types Detected

The tool is designed to detect a comprehensive range of PII, including but not limited to:

### Direct Identifiers
- Names (full names, first names, last names, nicknames)
- Email addresses
- Phone numbers (various formats)
- Physical addresses (full or partial)
- Social security numbers
- National ID/passport numbers
- Driver's license numbers
- Tax identification numbers
- Date of birth (various formats)
- Credit card numbers (with Luhn algorithm validation)
- Bank account details
- Biometric references

### Indirect Identifiers
- Booking/reservation codes
- Customer/order IDs
- Patient/student/employee numbers
- Job titles when tied to specific individuals
- Vehicle registration numbers
- Educational institutions when linked to individuals
- Workplace information
- IP addresses
- Device identifiers
- Travel itineraries
- Location data

The combination of regex pattern detection and LLM analysis allows the tool to identify both structured PII (like SSNs with predictable formats) and unstructured PII (like descriptive references to individuals).

## 💡 Design Decisions

### PDF Redaction Implementation

#### Selected Approach: PyMuPDF with `apply_redactions()`

PyMuPDF (fitz) provides true content removal through its redaction API. Implentation as below:

1. Uses `page.add_redact_annot()` to mark PII areas for redaction
2. Calls `page.apply_redactions()` to permanently remove the underlying text
3. Uses `page.wrap_contents()` to ensure proper content removal by normalizing the PDF content stream
4. Sets `garbage=4, deflate=True, clean=True, incremental=False` when saving to maximize sanitization
5. Removes metadata with `doc.set_metadata({})` and `doc.del_xml_metadata()`

**Technical Advantages:**
- Complete text removal from the PDF structure, not just visual masking
- PDF content stream is rewritten rather than just modified
- Maximum garbage collection with `garbage=4` removes unreferenced objects
- Non-incremental save (`incremental=False`) ensures a complete document rewrite

**Compared to Alternatives:**
   
1. **PDF to Image Conversion**
   - Renders PDF to images, then back to PDF
   - Pros: Completely removes text layer
   - Cons: Eliminates searchability, increases file size, reduces quality, removes accessibility features
   
2. **Text Replacement**
   - Replaces PII with placeholder characters (e.g., "XXXXX")
   - Pros: Maintains document structure
   - Cons: Complex to implement properly, risk of incomplete replacement if text spans objects

3. **Adobe PDF Library**
   - Commercial solution with dedicated redaction features
   - Pros: Industry standard, comprehensive
   - Cons: Licensing costs, external dependency, complex integration

### PII Dectection Strategy

#### Selected Approach: OpenAI GPT-4 with Hybrid Detection

Combined regex pattern matching with LLM-based detection:

1. Initial fast-pass detection using compiled regex patterns
2. LLM validation and expansion to catch contextual PII
3. Feedback loop to improve pattern detection based on LLM findings

**Technical Advantages:**
- Zero-shot learning capabilities eliminate need for labeled training data
- Contextual understanding allows detection of implied PII
- Ability to handle novel PII formats without explicit pattern definitions
- Multi-language support without dedicated language models

**Compared to Alternatives:**

1. **Named Entity Recognition (Spacy/NLTK)**
   - Uses statistical models trained on labeled data
   - Pros: Fast local processing, no API costs
   - Cons: Limited to trained entity types, poor with contextual PII, requires separate models per language
   - Performance metrics: Typically 70-85% F1 score on standard PII types, poor on contextual PII

2. **Microsoft Presidio**
   - Uses analyzer engines with rule-based recognizers
   - Pros: Open-source, customizable, no API dependency
   - Cons: English-centric, requires custom recognizers for domain-specific PII
   - Performance metrics: 80-90% F1 score on well-formatted PII, lower on unstructured text

3. **Regular Expressions Only**
   - Relies solely on pattern matching
   - Pros: Very fast, no external dependencies, predictable behavior
   - Cons: High false positive/negative rates, no contextual understanding, language-specific
   - Performance metrics: High recall but low precision (many false positives)

4. **Fine-tuned Domain-Specific Models**
   - Custom models trained specifically for PII detection
   - Pros: Optimized for specific use cases, potential for high accuracy
   - Cons: Requires extensive training data, time-consuming development, limited generalizability
   - Performance metrics: Can achieve 90%+ F1 scores in narrow domains

### PDF Processing Strategy

Our text matching and redaction algorithm addresses several technical challenges:

1. **Text Fragmentation Handling**
   - Implementation: Custom `find_pii_matches_on_page()` function that handles text broken across blocks
   - Technical challenge: In PDFs, text that visually appears contiguous may be split into multiple blocks
   - Our solution: Sliding window approach to reconstruct text spans and fuzzy matching

2. **Position Determination**
   - Implementation: PyMuPDF's text extraction with positional data
   - Technical challenge: Mapping text content to exact coordinates for redaction
   - Our solution: Using PyMuPDF's block extraction with `get_text("blocks")` to preserve position information

3. **Handling Complex Layouts**
   - Implementation: Contextual text analysis and position normalization
   - Technical challenge: Text in columns, tables, or custom layouts may have non-linear reading order
   - Our solution: Page-level text extraction combined with smart matching algorithms

**Technical Trade-offs:**
- PyMuPDF vs PDFBox/PDFlib/iText: PyMuPDF offers better Python integration but less commercial support
- Regex+LLM vs pure NER: Higher accuracy at the cost of API dependency and latency
- Full-document vs page-by-page processing: Better context detection vs memory efficiency
- Complete redaction vs selective redaction: Security vs performance

### Command Line + Web Interface

Providing both interfaces serves different user needs:
- CLI: Automation, batch processing, integration with workflows
- Web UI: Accessibility for non-technical users, visual feedback, and easier evaluation

### Evaluation Metrics

The evaluation system measures:
- True positives: Correctly redacted PII
- False negatives: Missed PII
- False positives: Unnecessarily redacted text
- Precision, recall, and F1 score

These metrics help tune the system and provide confidence in the redaction quality.

## ⚠️ Limitations

Despite the tool's capabilities, there are several limitations to be aware of:

1. **Scanned PDFs**: The tool cannot process scanned documents or images without OCR preprocessing.

2. **Language Dependencies**: While the LLM component is multilingual, regex patterns are primarily optimized for English and may not catch all patterns in other languages.

3. **API Dependency and Costs**: Utilizing OpenAI's API requires a valid OpenAI API key to function and incurs costs based on token usage, which increases with document length.

4. **Processing Speed**: Large documents may take significant time to process due to the API call latency and the thorough redaction process.

5. **Complex Layouts**: Documents with highly complex layouts or unusual formatting may present challenges for accurate text position matching.

6. **Specific PII Types**: Detecting certain PII types like medical information or genetic data requires domain knowledge that may be incomplete in the model.

## 🚀 Future Improvements

Several enhancements could further improve the tool:

1. **Local LLM Option**: Integrate with locally-hosted models to reduce API dependency and costs.

2. **Custom Redaction Styles**: Allow users to customize the appearance of redactions (colors, labels, etc.).

3. **Batch Processing**: Enhance CLI to handle multiple documents in a single command.

4. **Redaction Policies**: Allow users to define which types of PII to redact based on their needs.

5. **Performance Optimization**: Improve processing speed through parallelization and smarter text chunking.

6. **Document Type Specialization**: Add specific detection patterns for common document types (resumes, medical records, financial statements).


## 📜 License
This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🙌 Credits
Created by [Manjusha Raavi](https://github.com/manjuraavi)
