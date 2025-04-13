#!/usr/bin/env python3
"""
PII Redactor Tool - Redact personally identifiable information (PII) from PDF documents.
"""

import argparse
from pathlib import Path
import sys
import os
import logging
from datetime import datetime
import time
from pii_redactor.redactor import PIIRedactor
from pii_redactor.utils import OUTPUT_DIR, check_env_key, validate_evaluate_input, validate_input
from pii_redactor.evaluate_metrics import evaluate
from dotenv import load_dotenv
import json

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
        start = time.time()
        success = redactor.redact_pdf(input_file, output_file)  # Perform the redaction
        end = time.time()

        if success:
            logger.info(f"Successfully redacted. Redacted file path: {output_file}")
            logger.info(f"Time taken to redact PII from file: {end - start:.2f}ss")
            return 0
        else:
            logger.error("Redaction process failed.")
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
    parser.add_argument("-e", "--evaluate", action="store_true", help="Evaluate redaction with ground truth")
    parser.add_argument("-gt", "--ground_truth", type=str, help="Path to ground truth JSON file")

    args = parser.parse_args()

    logger = setup_logging()  # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)  # Enable debug logging if verbose flag is set

    input_path = args.input_file
    if not validate_input(input_path, logger):  # Validate the input file
        return 1

    # Generate output file path if not provided
    output_path = args.output_file or generate_output_filename(input_path)

    # Run redaction
    status = process_pdf(input_path, output_path, logger)
    if status != 0:
        logger.error("Redaction process failed.")
        return status

    # Run evaluation if flag is set
    if args.evaluate:
        if not validate_evaluate_input(args, logger):  # Validate evaluation inputs
            return 1

        logger.info("Running evaluation against ground truth...")
        try:
            results = evaluate(input_path, output_path, args.ground_truth)
            logger.info("Evaluation complete.")
        except Exception as e:
            logger.exception(f"Evaluation failed: {e}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())  # Exit with the return code from main()