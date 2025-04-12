import os
import pytest
import fitz
import warnings
from pii_redactor.redactor import PIIRedactor
from pii_redactor.pii_detector import PIIDetector
from pii_redactor.utils import OUTPUT_DIR, TEST_DATA_DIR, EXAMPLE_INPUT_FILE, EXAMPLE_OUTPUT_FILE
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define paths for test input and output files
INPUT_FILE = os.path.join(TEST_DATA_DIR, "example_1.pdf")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "example_1_redacted.pdf")

def test_end_to_end_redaction():
    """
    Test the end-to-end functionality of the redaction tool.
    Inputs: None (uses predefined test files).
    Outputs: None (asserts success of redaction and output file creation).
    """
    if not os.path.exists(EXAMPLE_INPUT_FILE):  # Check if the input file exists
        pytest.skip("Test PDF file not found")

    # Initialize the redactor with the OpenAI API key
    redactor = PIIRedactor(openai_api_key=os.getenv("OPENAI_API_KEY"))
    result = redactor.redact_pdf(EXAMPLE_INPUT_FILE, EXAMPLE_OUTPUT_FILE)  # Perform redaction

    # Assert that the redaction was successful and the output file exists
    assert result is True
    assert os.path.exists(EXAMPLE_OUTPUT_FILE)
    assert os.path.getsize(EXAMPLE_OUTPUT_FILE) > 0  # Ensure the output file is not empty

def test_redacted_text_removed():
    """
    Test that specific PII text is removed from the redacted PDF.
    Inputs: None (uses predefined test files).
    Outputs: None (asserts that PII text is not present in the output file).
    """
    if not os.path.exists(EXAMPLE_OUTPUT_FILE):  # Check if the redacted file exists
        pytest.skip("Redacted PDF not found")

    # Open the redacted PDF and extract all text
    with fitz.open(EXAMPLE_OUTPUT_FILE) as doc:
        full_text = "".join([page.get_text() for page in doc])

    # Assert that specific PII text is not present in the redacted file
    assert "manjushaa.raavi@gmail.com" not in full_text
    assert "+91 9390759782" not in full_text

def test_reduction_tool():
    """
    Test the redaction tool with a sample PDF and validate PII removal.
    Inputs: None (uses predefined test files).
    Outputs: None (asserts that detected PII is removed from the output file).
    """
    if not os.path.exists(INPUT_FILE):  # Check if the input file exists
        print("Test PDF file not found")
        pytest.skip("Test PDF file not found")

    # Open the input PDF and extract all text
    doc = fitz.open(INPUT_FILE)
    full_document_text = ""
    for page in doc:
        blocks = page.get_text("blocks")  # Extract text blocks from the page
        full_document_text += "\n".join([block[4] for block in blocks if isinstance(block[4], str)]) + "\n"

    # Detect PII in the extracted text
    detector = PIIDetector(openai_api_key=os.getenv("OPENAI_API_KEY"))
    detected_pii = detector.detect_pii(full_document_text)

    if not detected_pii:  # Skip the test if no PII is detected
        print("No PII detected to validate redaction")
        pytest.skip("No PII detected to validate redaction")

    # Perform redaction on the input file
    redactor = PIIRedactor(openai_api_key=os.getenv("OPENAI_API_KEY"))
    redactor.redact_pdf(INPUT_FILE, OUTPUT_FILE)

    # Open the redacted PDF and extract all text
    with fitz.open(OUTPUT_FILE) as doc:
        redacted_text = "".join([page.get_text() for page in doc])

    # Assert that all detected PII is removed from the redacted file
    for pii in detected_pii:
        assert pii["text"] not in redacted_text, f"PII '{pii['text']}' was not removed"