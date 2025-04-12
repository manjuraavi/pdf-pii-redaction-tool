import unittest
from unittest.mock import MagicMock, patch
from pii_redactor.pii_detector import PIIDetector
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class TestPIIDetector(unittest.TestCase):
    """
    Unit tests for the PIIDetector class to validate PII detection and validation functionality.
    """

    def setUp(self):
        """
        Set up the test environment by initializing the PIIDetector with a mock logger.
        Inputs: None.
        Outputs: None.
        """
        self.mock_logger = MagicMock()  # Mock logger for testing
        self.detector = PIIDetector(openai_api_key=os.getenv("OPENAI_API_KEY"), logger=self.mock_logger)

    def test_detect_with_regex_email(self):
        """
        Test detecting email addresses using regex.
        Inputs: Sample text containing an email address.
        Outputs: Asserts that the email is correctly detected.
        """
        text = "Contact me at test.email@example.com for details."
        result = self.detector.detect_with_regex(text)
        self.assertIn({"type": "email", "text": "test.email@example.com"}, result)

    def test_detect_with_regex_phone(self):
        """
        Test detecting phone numbers using regex.
        Inputs: Sample text containing phone numbers.
        Outputs: Asserts that the phone numbers are correctly detected.
        """
        text = "Call me at +1234567890 or 987-654-3210."
        result = self.detector.detect_with_regex(text)
        self.assertIn({"type": "phone", "text": "+1234567890"}, result)
        self.assertIn({"type": "phone", "text": "987-654-3210"}, result)

    def test_detect_with_regex_credit_card(self):
        """
        Test detecting credit card numbers using regex.
        Inputs: Sample text containing a credit card number.
        Outputs: Asserts that the credit card number is correctly detected.
        """
        text = "My credit card number is 4111 1111 1111 1111."
        result = self.detector.detect_with_regex(text)
        self.assertIn({"type": "credit_card", "text": "4111 1111 1111 1111"}, result)

    def test_detect_with_regex_date_of_birth(self):
        """
        Test detecting dates of birth using regex.
        Inputs: Sample text containing a date of birth.
        Outputs: Asserts that the date of birth is correctly detected.
        """
        text = "My date of birth is 1990-05-15."
        result = self.detector.detect_with_regex(text)
        self.assertIn({"type": "date_of_birth", "text": "1990-05-15"}, result)

    def test_validate_credit_card_valid(self):
        """
        Test validating a valid credit card number.
        Inputs: Valid credit card number.
        Outputs: Asserts that the validation passes.
        """
        card_number = "4111 1111 1111 1111"
        self.assertTrue(self.detector.validate_credit_card(card_number))

    def test_validate_credit_card_invalid(self):
        """
        Test validating an invalid credit card number.
        Inputs: Invalid credit card number.
        Outputs: Asserts that the validation fails.
        """
        card_number = "1234 5678 9012 3456"
        self.assertFalse(self.detector.validate_credit_card(card_number))

    def test_validate_phone_number_valid(self):
        """
        Test validating a valid phone number.
        Inputs: Valid phone number.
        Outputs: Asserts that the validation passes.
        """
        phone_number = "+1234567890"
        self.assertTrue(self.detector.validate_phone_number(phone_number))

    def test_validate_phone_number_invalid(self):
        """
        Test validating an invalid phone number.
        Inputs: Invalid phone number.
        Outputs: Asserts that the validation fails.
        """
        phone_number = "123"
        self.assertFalse(self.detector.validate_phone_number(phone_number))

    def test_validate_email_valid(self):
        """
        Test validating a valid email address.
        Inputs: Valid email address.
        Outputs: Asserts that the validation passes.
        """
        email = "test.email@example.com"
        self.assertTrue(self.detector.validate_email(email))

    def test_validate_email_invalid(self):
        """
        Test validating an invalid email address.
        Inputs: Invalid email address.
        Outputs: Asserts that the validation fails.
        """
        email = "invalid-email"
        self.assertFalse(self.detector.validate_email(email))

    def test_validate_dob_valid(self):
        """
        Test validating a valid date of birth.
        Inputs: Valid date of birth.
        Outputs: Asserts that the validation passes.
        """
        dob = "1990-05-15"
        self.assertTrue(self.detector.validate_dob(dob))

    def test_validate_dob_invalid(self):
        """
        Test validating an invalid date of birth.
        Inputs: Invalid date of birth.
        Outputs: Asserts that the validation fails.
        """
        dob = "3000-01-01"
        self.assertFalse(self.detector.validate_dob(dob))

    @patch("pii_redactor.pii_detector.openai.OpenAI")
    def test_llm_verify_and_expand(self, MockOpenAI):
        """
        Test verifying and expanding PII detection results using an LLM.
        Inputs: Mocked OpenAI client and sample text with regex results.
        Outputs: Asserts that the LLM correctly verifies and expands the results.
        """
        # Configure the mock OpenAI client
        mock_client = MockOpenAI.return_value
        mock_chat = mock_client.chat
        mock_completions = mock_chat.completions
        mock_completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='[{"type": "email", "text": "test.email@example.com"}]'))]
        )
        
        text = "Contact me at test.email@example.com."
        regex_results = [{"type": "email", "text": "test.email@example.com"}]
        result = self.detector.llm_verify_and_expand(text, regex_results, "en")
        self.assertEqual(result, [{"type": "email", "text": "test.email@example.com"}])

    def test_detect_language(self):
        """
        Test detecting the language of a given text.
        Inputs: Sample text.
        Outputs: Asserts that the detected language matches the expected result.
        """
        text = "This is a test."
        language = self.detector.detect_language(text)
        self.assertEqual(language, "en")

if __name__ == "__main__":
    unittest.main()  # Run the unit tests