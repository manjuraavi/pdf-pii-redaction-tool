import os

# Path Setup
# Get the current directory (where the script is located)
current_directory = os.path.dirname(__file__)

# Get the project directory (assuming the script is in a subdirectory of the project)
project_directory = os.path.abspath(os.path.join(current_directory, os.pardir))

# Define the paths for various directories in the project
TEST_DATA_DIR = os.path.join(project_directory, "test_data")
SRC_DIR = os.path.join(project_directory, "pii_redactor")
TEST_DIR = os.path.join(project_directory, "tests")
OUTPUT_DIR = os.path.join(project_directory, "output")

# Define paths for test input and output files
EXAMPLE_INPUT_FILE = os.path.join(TEST_DATA_DIR, "sample.pdf")
EXAMPLE_OUTPUT_FILE = os.path.join(TEST_DATA_DIR, "sample_redacted.pdf")