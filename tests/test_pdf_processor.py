import unittest
from unittest.mock import patch, MagicMock
from pii_redactor.pdf_processor import PdfProcessor

class TestPdfProcessor(unittest.TestCase):
    """
    Unit tests for the PdfProcessor class to validate PDF text extraction functionality.
    """

    @patch('fitz.open')
    def test_extract_text_single_page(self, mock_fitz_open):
        """
        Test extracting text from a single-page PDF.
        Inputs: Mocked PDF file with one page.
        Outputs: Asserts that the extracted text matches the mock data.
        """
        # Mocking a single-page PDF
        mock_document = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text on page 1"  # Mock text for the page
        mock_document.__iter__.return_value = [mock_page]  # Mock document iterator
        mock_fitz_open.return_value = mock_document  # Mock fitz.open to return the mock document

        pdf_processor = PdfProcessor()
        result = pdf_processor.extract_text("dummy_path.pdf")  # Call the method under test

        # Assertions to validate the extracted text
        self.assertEqual(len(result), 1)  # Ensure only one page is processed
        self.assertEqual(result[0]['page_num'], 0)  # Validate the page number
        self.assertEqual(result[0]['text'], "Sample text on page 1")  # Validate the extracted text
        mock_document.close.assert_called_once()  # Ensure the document is closed

    @patch('fitz.open')
    def test_extract_text_multiple_pages(self, mock_fitz_open):
        """
        Test extracting text from a multi-page PDF.
        Inputs: Mocked PDF file with multiple pages.
        Outputs: Asserts that the extracted text matches the mock data for all pages.
        """
        # Mocking a multi-page PDF
        mock_document = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Text on page 1"  # Mock text for page 1
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Text on page 2"  # Mock text for page 2
        mock_document.__iter__.return_value = [mock_page1, mock_page2]  # Mock document iterator
        mock_fitz_open.return_value = mock_document  # Mock fitz.open to return the mock document

        pdf_processor = PdfProcessor()
        result = pdf_processor.extract_text("dummy_path.pdf")  # Call the method under test

        # Assertions to validate the extracted text
        self.assertEqual(len(result), 2)  # Ensure two pages are processed
        self.assertEqual(result[0]['page_num'], 0)  # Validate the page number for page 1
        self.assertEqual(result[0]['text'], "Text on page 1")  # Validate the extracted text for page 1
        self.assertEqual(result[1]['page_num'], 1)  # Validate the page number for page 2
        self.assertEqual(result[1]['text'], "Text on page 2")  # Validate the extracted text for page 2
        mock_document.close.assert_called_once()  # Ensure the document is closed

    @patch('fitz.open')
    def test_extract_text_empty_pdf(self, mock_fitz_open):
        """
        Test extracting text from an empty PDF.
        Inputs: Mocked empty PDF file.
        Outputs: Asserts that no text is extracted.
        """
        # Mocking an empty PDF
        mock_document = MagicMock()
        mock_document.__iter__.return_value = []  # Mock document iterator with no pages
        mock_fitz_open.return_value = mock_document  # Mock fitz.open to return the mock document

        pdf_processor = PdfProcessor()
        result = pdf_processor.extract_text("dummy_path.pdf")  # Call the method under test

        # Assertions to validate the extracted text
        self.assertEqual(len(result), 0)  # Ensure no pages are processed
        mock_document.close.assert_called_once()  # Ensure the document is closed

    @patch('fitz.open')
    def test_extract_text_exception_handling(self, mock_fitz_open):
        """
        Test exception handling during PDF text extraction.
        Inputs: Mocked PDF file that raises an exception.
        Outputs: Asserts that the exception is raised and handled correctly.
        """
        # Mocking an exception during PDF processing
        mock_fitz_open.side_effect = Exception("Error opening PDF")  # Mock fitz.open to raise an exception

        pdf_processor = PdfProcessor()
        with self.assertRaises(Exception) as context:  # Assert that an exception is raised
            pdf_processor.extract_text("dummy_path.pdf")  # Call the method under test

        # Assertions to validate the exception message
        self.assertEqual(str(context.exception), "Error opening PDF")  # Validate the exception message

if __name__ == '__main__':
    unittest.main()  # Run the unit tests