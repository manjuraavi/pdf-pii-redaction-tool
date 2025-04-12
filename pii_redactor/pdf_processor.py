import fitz  # PyMuPDF

class PdfProcessor:
    """Basic PDF processing functionality"""

    def extract_text(self, pdf_path):
        """
        Extract text content from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            list: List of dictionaries with page number and text content
        """
        document = fitz.open(pdf_path)
        pages_content = []

        for page_num, page in enumerate(document):
            text = page.get_text()
            pages_content.append({
                'page_num': page_num,
                'text': text
            })

        document.close()
        return pages_content

    