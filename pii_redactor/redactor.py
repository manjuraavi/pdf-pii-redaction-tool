import fitz  # PyMuPDF
from pii_redactor.pdf_processor import PdfProcessor
from pii_redactor.pii_detector import PIIDetector

class PIIRedactor:
    """
    Class to handle PII redaction in PDF files using a PDF processor and PII detector.
    """

    def __init__(self, openai_api_key=None, logger=None):
        """
        Initialize the PIIRedactor with a PDF processor, PII detector, and logger.
        Inputs: openai_api_key (str) - API key for PII detection, logger (logging.Logger) - Logger instance.
        Outputs: None
        """
        self.pdf_processor = PdfProcessor()  # Initialize the PDF processor
        self.pii_detector = PIIDetector(openai_api_key=openai_api_key, logger=logger)  # Initialize the PII detector
        self.logger = logger  # Logger instance for logging messages

    def find_pii_matches_on_page(self, page, pii_text):
        """
        Attempts to find and match PII text in a PDF page, even if it's split across lines with semantic similarity and layout awareness.
        Inputs: page (fitz.Page) - PDF page object, pii_text (str) - PII text to search for.
        Outputs: list - List of matching rectangles for the PII text.
        """
        matches = []

        # Try full match first
        full_matches = page.search_for(pii_text.strip(), quads=False)  # Search for exact matches
        matches.extend(full_matches)

        # If no matches, try partial matching
        if not full_matches:
            separators = [",", "\n", ";"]  # Common separators for splitting text
            for sep in separators:
                if sep in pii_text:
                    # Split the text by the separator and search for each part
                    parts = [part.strip() for part in pii_text.split(sep) if part.strip()]
                    for part in parts:
                        partials = page.search_for(part, quads=False)
                        matches.extend(partials)
                    break  # Stop after finding matches for one separator

        return matches

    def redact_pdf(self, input_path, output_path):
        """
        Redact PII from a PDF file and save the redacted version.
        Inputs: input_path (str) - Path to the input PDF, output_path (str) - Path to save the redacted PDF.
        Outputs: bool - True if redaction is successful, False otherwise.
        """
        try:
            if self.logger:
                self.logger.info(f"Starting redaction on {input_path}")
            else:
                print(f"Starting redaction on {input_path}")

            doc = fitz.open(input_path)  # Open the input PDF file

            # Extract all text from the document to maintain context
            full_document_text = ""
            for page in doc:
                blocks = page.get_text("blocks")  # Extract text blocks from the page
                full_document_text += "\n".join([block[4] for block in blocks if isinstance(block[4], str)]) + "\n"

            # Detect PII in the entire document text
            pii_data = self.pii_detector.detect_pii(full_document_text)
            if not pii_data:
                # If no PII is detected, log and return success
                if self.logger:
                    self.logger.info("No PII detected.")
                return True
                        
            if self.logger:
                self.logger.info(f"Detected PII in document: {pii_data}")

            # Process each page for redaction
            for page_num, page in enumerate(doc):
                try:
                    page.wrap_contents()  # Wrap page contents to avoid layout issues
                    for pii in pii_data:
                        text_to_find = pii.get("text")  # Get the PII text to redact
                        if not text_to_find:
                            continue

                        matches = self.find_pii_matches_on_page(page, text_to_find)  # Find matches for the PII text
                        if not matches:
                            # Attempt to find matches for text that might be split across lines
                            text_lines = text_to_find.splitlines()
                            for line in text_lines:
                                line_matches = self.find_pii_matches_on_page(page, line)
                                matches.extend(line_matches)

                        # Add redaction annotations for all matches
                        for rect in matches:
                            page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill for redaction

                    page.apply_redactions()  # Apply the redactions to the page
                except Exception as page_error:
                    if self.logger:
                        self.logger.error(f"Error processing page {page_num + 1}: {page_error}")

            # Save PDF and remove metadata
            # doc.save(output_path, garbage=4, deflate=True, clean=True, pretty=True)  # Save with optimizations
            doc.set_metadata({})  # Clear metadata
            doc.del_xml_metadata()  # Remove XML metadata
            doc.save(output_path, garbage=4, deflate=True, clean=True, pretty=True, incremental=False)  # Save final version
            doc.close()

            print("Successfully redacted")
            if self.logger:
                self.logger.info(f"Successfully redacted: {output_path}")
            return True
            # Handle edge cases for text with spaces or commas split across lines
            for pii in pii_data:
                text_to_find = pii.get("text")
                if not text_to_find:
                    continue

                # Attempt to find matches for text split across lines or with separators
                matches = self.find_pii_matches_on_page(page, text_to_find)
                if not matches:
                    # Handle cases where text might be split across lines or contain separators
                    words = text_to_find.split()
                    for i in range(len(words)):
                        for j in range(i + 1, len(words) + 1):
                            partial_text = " ".join(words[i:j])
                            partial_matches = self.find_pii_matches_on_page(page, partial_text)
                            matches.extend(partial_matches)

                if not matches and self.logger:
                    self.logger.warning(f"No match found on page {page_num + 1} for: {text_to_find}")

                # Add redaction annotations for all matches
                for rect in matches:
                    page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill for redaction

        except Exception as e:
            # Handle any exceptions during the redaction process
            if self.logger:
                self.logger.exception("Redaction failed")
            else:
                print(f"Redaction failed: {e}")
            return False