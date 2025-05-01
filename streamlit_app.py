# Streamlit UI for PII Redactor Tool - Web interface to redact personally identifiable 
# information (PII) from PDF documents.

import pandas as pd
import streamlit as st
import os
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from pii_redactor.redactor import PIIRedactor
from pii_redactor.utils import OUTPUT_DIR, check_env_key
from dotenv import load_dotenv
import tempfile
import base64
import json

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Set up logging configuration with file and console output."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pii_redactor_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger("pii-redactor")

logger = setup_logging()

# Function to create a download link for the redacted PDF
def get_download_link(file_path, file_name):
    """Generate a download link for a file"""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    b64 = base64.b64encode(file_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">Download Redacted PDF</a>'

def validate_ground_truth_structure(ground_truth_data):
    """Validate that the ground truth JSON file has the correct structure"""
    
    # Check if 'pii' key exists and is a list
    if "pii" not in ground_truth_data or not isinstance(ground_truth_data["pii"], list):
        return False
    
    # Check each item in the 'pii' list
    for item in ground_truth_data["pii"]:
        if not isinstance(item, dict):
            return False
        if not all(key in item for key in ["type", "text", "page"]):
            return False
        if not isinstance(item["type"], str) or not isinstance(item["text"], str) or not isinstance(item["page"], int):
            return False
    
    return True

# Main Streamlit UI
def main():
    st.set_page_config(
        page_title="PII Redactor Tool",
        page_icon="🔒",
        layout="centered"
    )
    
    st.title("PII Redactor Tool")
    st.markdown("Upload PDF documents to redact personally identifiable information (PII)")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # API Key input (with password protection)
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", 
                                    help="Enter your OpenAI API key or set it in the .env file")
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # File upload section
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
      
    # Process the uploaded file
    if uploaded_file is not None:                
        try:

            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                input_path = tmp_file.name

            if not input_path.lower().endswith(".pdf"):
                st.error("Uploaded file is not a valid PDF.")
                return
        
            # Define output path
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            base_name = os.path.splitext(uploaded_file.name)[0]
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}_redacted.pdf")
        
            # Process button
            if st.button("Redact PII"):
                # Check API key
                if not check_env_key(logger):
                    st.error("OpenAI API key not found. Please enter it in the sidebar.")
                    return
                
                # Show progress
                with st.spinner("Redacting PII from document..."):
                    try:
                        # Initialize redactor
                        openai_api_key = os.environ.get("OPENAI_API_KEY")
                        redactor = PIIRedactor(logger=logger, openai_api_key=openai_api_key)
                        
                        # Start timer
                        start_time = time.time()
                        
                        # Perform redaction
                        success = redactor.redact_pdf(input_path, output_path)
                        
                        # End timer
                        end_time = time.time()
                        
                        if success:
                            st.success(f"Redaction complete in {end_time - start_time:.2f} seconds!")
                            
                            # Generate download link
                            st.markdown(get_download_link(output_path, f"{base_name}_redacted.pdf"), unsafe_allow_html=True)
                            
                            # Show preview with side-by-side visual comparison
                            # with st.expander("🔍 Preview: Original vs Redacted PDF"):
                            #     col1, col2 = st.columns(2)

                            #     with col1:
                            #         st.markdown("**📝 Original PDF**")
                            #         with open(input_path, "rb") as f:
                            #             st.download_button(
                            #                 label="Download Original",
                            #                 data=f.read(),
                            #                 file_name=uploaded_file.name,
                            #                 mime="application/pdf"
                            #             )
                            #         st.markdown(
                            #             f'<iframe src="data:application/pdf;base64,{base64.b64encode(open(input_path, "rb").read()).decode()}" width="100%" height="500"></iframe>',
                            #             unsafe_allow_html=True
                            #         )

                            #     with col2:
                            #         st.markdown("**🔒 Redacted PDF**")
                            #         with open(output_path, "rb") as f:
                            #             st.download_button(
                            #                 label="Download Redacted",
                            #                 data=f.read(),
                            #                 file_name=f"{base_name}_redacted.pdf",
                            #                 mime="application/pdf"
                            #             )
                            #         st.markdown(
                            #             f'<iframe src="data:application/pdf;base64,{base64.b64encode(open(output_path, "rb").read()).decode()}" width="100%" height="500"></iframe>',
                            #             unsafe_allow_html=True
                            #         )
                    except Exception as e:
                        st.error(f"Error during redaction: {str(e)}")
                        logger.error(f"Redaction error: {str(e)}")
        except Exception as e:
            st.error(f"Error processing the uploaded file: {str(e)}")
        finally:
                # Clean up temp file
            os.unlink(input_path)
    
    # Instructions/Help section
    with st.expander("How to Use"):
        st.markdown("""
        1. Enter your OpenAI API key in the sidebar
        2. Upload a PDF document containing PII
        3. Click "Redact PII" to process the document
        4. Download the redacted PDF when processing is complete
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("PII Redactor Tool © 2025 | Built with Streamlit")

if __name__ == "__main__":
    main()
