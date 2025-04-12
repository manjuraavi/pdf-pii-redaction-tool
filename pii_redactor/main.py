#!/usr/bin/env python3
"""
PII Redactor Tool - Redact personally identifiable information (PII) from PDF documents.
This file acts as the entry point to the tool through CLI. 
"""

import argparse
import sys
import os
import logging
from datetime import datetime
from pii_redactor.redactor import PIIRedactor
from pii_redactor.utils import OUTPUT_DIR
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Set up logging configuration with file and console output.
    Inputs: log_dir (str) - Directory to store log files.
    Outputs: logger (logging.Logger) - Configured logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate a timestamp for the log file
    log_file = os.path.join(log_dir, f"pii_redactor_{timestamp}.log")

    # Configure logging to write to both a file and the console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger("pii-redactor")

def generate_output_filename(input_file: str) -> str:
    """
    Generate a default output filename if one is not provided.
    If the filename already exists, append a numeric suffix to make it unique.
    Inputs: input_file (str) - Path to the input file.
    Outputs: str - Generated unique output filename.
    """
    base = os.path.splitext(os.path.basename(input_file))[0]  # Extract the base name
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"{base}_redacted.pdf")  # Initial output filename

    counter = 1
    while os.path.exists(output_file):  # Check if the file already exists
        output_file = os.path.join(OUTPUT_DIR, f"{base}_redacted_{counter}.pdf")  # Append a numeric suffix
        counter += 1

    return output_file

def validate_input(input_path: str, logger: logging.Logger) -> bool:
    """
    Validate that the input path exists and is a valid non-scanned PDF.
    Inputs: input_path (str) - Path to the input file, logger (logging.Logger) - Logger instance.
    Outputs: bool - True if the input is valid, False otherwise.
    """
    if not os.path.exists(input_path):  # Check if the file exists
        logger.error(f"Input file not found: {input_path}")
        print(f"Error: Input file '{input_path}' not found.")
        return False

    if not input_path.lower().endswith(".pdf"):  # Ensure the file is a PDF
        logger.error("Unsupported file format")
        print("Error: Only PDF files are supported.")
        return False

    try:
        import fitz  # Import PyMuPDF for PDF processing
        doc = fitz.open(input_path)
        # Check if the PDF has at least one page with selectable text
        if len(doc) == 0 or all(page.get_text().strip() == '' for page in doc):
            logger.error("The PDF file is either empty or consists of scanned images.")
            print("Error: Input file appears to be a scanned PDF or contains no selectable text.")
            return False
        doc.close()
    except Exception as e:
        logger.error(f"Error validating PDF file: {e}")
        return False

    return True

def check_env_key(logger: logging.Logger) -> str:
    """
    Check for the required OpenAI API key from the environment.
    Inputs: logger (logging.Logger) - Logger instance.
    Outputs: str - The OpenAI API key if found, otherwise None.
    """
    key = os.getenv("OPENAI_API_KEY")  # Retrieve the API key from environment variables
    if not key:
        logger.error("Missing OPENAI_API_KEY in environment.")
        print("Error: OPENAI_API_KEY not found in .env file or environment variables.")
    return key

def process_pdf(input_file: str, output_file: str, logger: logging.Logger) -> int:
    """
    Run the redaction pipeline on the input PDF.
    Inputs: input_file (str) - Path to the input PDF, output_file (str) - Path to save the redacted PDF,
            logger (logging.Logger) - Logger instance.
    Outputs: int - 0 if successful, 1 otherwise.
    """
    try:
        openai_api_key = check_env_key(logger)  # Check for the OpenAI API key
        if not openai_api_key:
            return 1

        logger.info(f"Starting PII redaction on {input_file}")
        # Initialize the redactor with the logger and API key
        redactor = PIIRedactor(logger=logger, openai_api_key=openai_api_key)
        success = redactor.redact_pdf(input_file, output_file)  # Perform the redaction

        if success:
            logger.info(f"Successfully redacted: {output_file}")
            print(f"Output saved to: {output_file}")
            return 0
        else:
            logger.error("Redaction process failed.")
            print("Error: Redaction failed.")
            return 1

    except Exception as e:
        logger.exception(f"Unhandled exception during redaction: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def main() -> int:
    """
    Main function to parse CLI arguments and trigger processing.
    Inputs: None (CLI arguments are parsed internally).
    Outputs: int - Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="PII Redaction Tool - Redacts sensitive data from PDF files."
    )
    parser.add_argument("input_file", type=str, help="Path to the input PDF file")
    parser.add_argument("-o", "--output", dest="output_file", type=str, help="Path to save the redacted PDF")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    logger = setup_logging()  # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)  # Enable debug logging if verbose flag is set

    input_path = args.input_file
    if not validate_input(input_path, logger):  # Validate the input file
        return 1

    # Generate output file path if not provided
    output_path = args.output_file or generate_output_filename(input_path)

    return process_pdf(input_path, output_path, logger)  # Process the PDF

if __name__ == "__main__":
    sys.exit(main())  # Exit with the return code from main()