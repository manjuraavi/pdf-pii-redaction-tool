import os
import unittest
from unittest.mock import MagicMock, patch
from pii_redactor.redactor import PIIRedactor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TestPIIRedactor(unittest.TestCase):
    """
    Unit tests for the PIIRedactor class to validate PDF redaction functionality.
    """

    @patch("fitz.open")
    def test_redact_pdf_no_pii_detected(self, mock_fitz_open):
        """
        Test redaction when no PII is detected in the PDF.
        Inputs: Mocked PDF file with no PII.
        Outputs: Asserts that no redaction is performed and the process succeeds.
        """
        # Mock dependencies
        mock_logger = MagicMock()
        mock_pdf_processor = MagicMock()
        mock_pii_detector = MagicMock()
        mock_pii_detector.detect_pii.return_value = []  # No PII detected

        # Mock PDF document
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Instantiate PIIRedactor
        redactor = PIIRedactor(logger=mock_logger, openai_api_key=os.getenv("OPENAI_API_KEY"))
        redactor.pdf_processor = mock_pdf_processor
        redactor.pii_detector = mock_pii_detector

        # Call redact_pdf
        result = redactor.redact_pdf("input.pdf", "output.pdf")

        # Assertions
        self.assertTrue(result)  # Ensure the process succeeds
        mock_logger.info.assert_any_call("No PII detected.")  # Log message for no PII
        mock_doc.save.assert_not_called()  # Ensure no save operation is performed

    @patch("fitz.open")
    def test_redact_pdf_with_pii(self, mock_fitz_open):
        """
        Test redaction when PII is detected in the PDF.
        Inputs: Mocked PDF file with PII.
        Outputs: Asserts that redaction is performed and the output file is saved.
        """
        # Mock dependencies
        mock_logger = MagicMock()
        mock_pdf_processor = MagicMock()
        mock_pii_detector = MagicMock()
        mock_pii_detector.detect_pii.return_value = [{"text": "John Doe"}]  # Mock detected PII

        # Mock PDF document and page
        mock_page = MagicMock()
        mock_page.search_for.return_value = [MagicMock()]  # Mock matches for PII
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]  # Mock document iterator
        mock_fitz_open.return_value = mock_doc

        # Instantiate PIIRedactor
        redactor = PIIRedactor(logger=mock_logger, openai_api_key=os.getenv("OPENAI_API_KEY"))
        redactor.pdf_processor = mock_pdf_processor
        redactor.pii_detector = mock_pii_detector

        # Call redact_pdf
        result = redactor.redact_pdf("input.pdf", "output.pdf")

        # Assertions
        self.assertTrue(result)  # Ensure the process succeeds
        mock_logger.info.assert_any_call("Successfully redacted: output.pdf")  # Log success message
        mock_page.add_redact_annot.assert_called()  # Ensure redaction annotations are added
        mock_page.apply_redactions.assert_called()  # Ensure redactions are applied
        self.assertEqual(mock_doc.save.call_args[0][0], "output.pdf")  # Ensure the correct file is saved
        mock_doc.save.assert_called_with("output.pdf", garbage=4, deflate=True, clean=True, pretty=True, incremental=False)

    @patch("fitz.open")
    def test_redact_pdf_error_handling(self, mock_fitz_open):
        """
        Test error handling during the redaction process.
        Inputs: Mocked PDF file that raises an exception during PII detection.
        Outputs: Asserts that the exception is logged and the process fails.
        """
        # Mock dependencies
        mock_logger = MagicMock()
        mock_pdf_processor = MagicMock()
        mock_pii_detector = MagicMock()
        mock_pii_detector.detect_pii.side_effect = Exception("PII detection failed")  # Mock exception

        # Mock PDF document
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc

        # Instantiate PIIRedactor
        redactor = PIIRedactor(logger=mock_logger, openai_api_key=os.getenv("OPENAI_API_KEY"))
        redactor.pdf_processor = mock_pdf_processor
        redactor.pii_detector = mock_pii_detector

        # Call redact_pdf
        result = redactor.redact_pdf("input.pdf", "output.pdf")

        # Assertions
        self.assertFalse(result)  # Ensure the process fails
        mock_logger.exception.assert_called_with("Redaction failed")  # Log the exception

    def test_find_pii_matches_on_page_match(self):
        """
        Test finding full matches for PII text on a PDF page.
        Inputs: Mocked PDF page with full matches for PII text.
        Outputs: Asserts that all matches are correctly identified.
        """
        # Mock dependencies
        mock_logger = MagicMock()
        mock_page = MagicMock()
        mock_page.search_for.return_value = ["match1", "match2"]  # Mock full matches

        # Instantiate PIIRedactor
        redactor = PIIRedactor(logger=mock_logger, openai_api_key=os.getenv("OPENAI_API_KEY"))

        # Call find_pii_matches_on_page
        matches = redactor.find_pii_matches_on_page(mock_page, "John Doe")

        # Assertions
        self.assertEqual(matches, ["match1", "match2"])  # Ensure matches are correct
        mock_page.search_for.assert_called_with("John Doe", quads=False)  # Ensure correct search call

if __name__ == "__main__":
    unittest.main()  # Run the unit tests