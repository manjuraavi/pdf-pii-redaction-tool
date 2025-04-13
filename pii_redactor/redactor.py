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
        Attempts to find and match PII text in a PDF page, even if it's split across lines 
        with semantic similarity and layout awareness.
        
        Inputs: 
            page (fitz.Page) - PDF page object
            pii_text (str) - PII text to search for
        
        Outputs: 
            list - List of matching rectangles for the PII text
        """
        matches = []
        pii_text = pii_text.strip()
        
        if not pii_text:
            return matches
        
        # 1. Try exact match first with various whitespace adjustments
        for text_variant in [
            pii_text,
            pii_text.replace(" ", ""),  # No spaces
            " ".join(pii_text.split()),  # Normalized spaces
            pii_text.replace("-", ""),   # No hyphens
            pii_text.replace("-", " ")   # Hyphens as spaces
        ]:
            if text_variant:
                variant_matches = page.search_for(text_variant, quads=False)
                matches.extend(variant_matches)
        
        # 2. Try word proximity matching for multi-word text
        words = pii_text.split()
        if len(words) > 1 and not matches:
            # Get the text layout from the page
            page_blocks = page.get_text("dict")["blocks"]
            
            # Look for consecutive words that might be near each other
            for block in page_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
                            line_text = ""
                            spans = []
                            
                            # Collect spans and text for this line
                            for span in line["spans"]:
                                if "text" in span:
                                    line_text += span["text"] + " "
                                    spans.append(span)
                            
                            # Check if multiple words from PII appear in this line
                            word_matches = 0
                            matching_spans = []
                            
                            for word in words:
                                if word and len(word) > 2 and word.lower() in line_text.lower():
                                    word_matches += 1
                                    # Find spans containing this word
                                    for span in spans:
                                        if word.lower() in span["text"].lower():
                                            matching_spans.append(span)
                            
                            # If we found multiple words, create a rectangle covering all matching spans
                            if word_matches >= 2 and matching_spans:
                                # Create a rectangle that encompasses all matching spans
                                x0 = min(span["bbox"][0] for span in matching_spans)
                                y0 = min(span["bbox"][1] for span in matching_spans)
                                x1 = max(span["bbox"][2] for span in matching_spans)
                                y1 = max(span["bbox"][3] for span in matching_spans)
                                matches.append(fitz.Rect(x0, y0, x1, y1))
        
        # 3. Try common separators for splitting the text
        if not matches:
            separators = [",", "\n", ";", ".", "-", ":", "/"]
            for sep in separators:
                if sep in pii_text:
                    parts = [part.strip() for part in pii_text.split(sep) if part.strip() and len(part.strip()) > 3]
                    for part in parts:
                        part_matches = page.search_for(part, quads=False)
                        matches.extend(part_matches)
        
        # 4. For short PII like numbers, try character grouping
        if not matches and len(pii_text) <= 16 and any(c.isdigit() for c in pii_text):
            # For things like credit cards, SSNs, phone numbers, try digit groups
            digit_groups = []
            current_group = ""
            
            for char in pii_text:
                if char.isdigit():
                    current_group += char
                else:
                    if current_group and len(current_group) >= 3:
                        digit_groups.append(current_group)
                    current_group = ""
            
            # Add the last group if it exists
            if current_group and len(current_group) >= 3:
                digit_groups.append(current_group)
            
            # Search for each digit group
            for group in digit_groups:
                group_matches = page.search_for(group, quads=False)
                matches.extend(group_matches)
        
        # Remove duplicates while preserving order
        unique_matches = []
        for match in matches:
            if match not in unique_matches:
                unique_matches.append(match)
        
        return unique_matches

    def redact_pdf(self, input_path, output_path):
        """
        Redact PII from a PDF file and save the redacted version.
        Inputs: input_path (str) - Path to the input PDF, output_path (str) - Path to save the redacted PDF.
        Outputs: bool - True if redaction is successful, False otherwise.
        """
        doc = None
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
                    
                    # Get the text of the current page for context
                    page_text = page.get_text()
                    
                    for pii in pii_data:
                        text_to_find = pii.get("text")  # Get the PII text to redact
                        if not text_to_find:
                            continue

                        # Find matches using our enhanced matching function
                        matches = self.find_pii_matches_on_page(page, text_to_find)

                        # Add redaction annotations for all matches
                        for rect in matches:
                            page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill for redaction

                    page.apply_redactions()  # Apply the redactions to the page
                except Exception as page_error:
                    if self.logger:
                        self.logger.error(f"Error processing page {page_num + 1}: {page_error}")

            # Save PDF and remove metadata
            doc.set_metadata({})  # Clear metadata
            doc.del_xml_metadata()  # Remove XML metadata
            doc.save(output_path, garbage=4, deflate=True, clean=True, pretty=True, incremental=False)  # Save final version
            
            if self.logger:
                self.logger.info(f"Successfully redacted: {output_path}")
            else:
                print("Successfully redacted")
            
            return True

        except Exception as e:
            # Handle any exceptions during the redaction process
            if self.logger:
                self.logger.exception("Redaction failed")
            else:
                print(f"Redaction failed: {e}")
            return False
        
        finally:
            # Ensure document is closed even if an exception occurs
            if doc:
                doc.close()