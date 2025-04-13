import json
import logging
import os

# Path Setup
# Get the current directory (where the script is located)
current_directory = os.path.dirname(__file__)

# Get the project directory (assuming the script is in a subdirectory of the project)
project_directory = os.path.abspath(os.path.join(current_directory, os.pardir))

# Define the paths for various directories in the project

SRC_DIR = os.path.join(project_directory, "pii_redactor")
TEST_DIR = os.path.join(project_directory, "tests")
OUTPUT_DIR = os.path.join(project_directory, "output")

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

def validate_evaluate_input(args, logger):
    """
    Validate input for evaluation mode.
    """
    if not args.ground_truth:
        logger.error("Ground truth file (--ground_truth) is required when using --evaluate")
        return False
    
    if not os.path.exists(args.ground_truth):
        logger.error(f"Ground truth file not found: {args.ground_truth}")
        return False
    
    # Check if the ground truth file is valid JSON
    try:
        with open(args.ground_truth, 'r') as f:
            json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in ground truth file: {args.ground_truth}")
        return False
    
    return True