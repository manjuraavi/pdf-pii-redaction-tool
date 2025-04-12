from datetime import datetime
import re
import json
from typing import List, Dict
from langdetect import detect
import openai

class PIIDetector:
    def __init__(self, openai_api_key: str, model: str = "gpt-4o", logger=None):
        """
        Initializes the PIIDetector class with OpenAI API key, model, and optional logger.
        Inputs:
            - openai_api_key: API key for OpenAI
            - model: OpenAI model to use (default: "gpt-4o")
            - logger: Optional logger for logging errors and information
        """
        if not openai_api_key:
            raise ValueError("OpenAI API key must be provided")

        self.model = model
        self.logger = logger

        try:
            openai.api_key = openai_api_key
            self.client = openai.OpenAI()  # Initialize OpenAI client
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

        # Define regex patterns for detecting specific types of PII
        self.PII_PATTERNS = {
            "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
            "phone": re.compile(r"\+?\d[\d\s\-]{7,}\d"),
            "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
            "date_of_birth": re.compile(r"\b(?:(?:0?[1-9]|1[0-2])[\/\-\.](0?[1-9]|[12][0-9]|3[01])[\/\-\.](?:19|20)\d{2}|(?:19|20)\d{2}[\/\-\.](0?[1-9]|1[0-2])[\/\-\.](0?[1-9]|[12][0-9]|3[01]))\b"),
        }

    def detect_pii(self, text: str) -> List[Dict[str, str]]:
        """
        Detects PII in the given text using regex and LLM validation.
        Inputs:
            - text: The input text to analyze
        Outputs:
            - List of detected PII entities with their type and text
        """
        try:
            if not isinstance(text, str):
                raise TypeError("Input must be a string")

            # Detect the language of the input text
            language = self.detect_language(text)
            if self.logger:
                self.logger.info(f"Detected language: {language}")

            # Detect PII using regex patterns
            regex_entities = self.detect_with_regex(text)

            # Validate and expand PII detection using LLM
            final_entities = self.llm_verify_and_expand(text, regex_entities, language)
            return final_entities

        except Exception as e:
            if self.logger:
                self.logger.error(f"PII detection failed: {e}")
            return []

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the given text.
        Inputs:
            - text: The input text
        Outputs:
            - Detected language as a string
        """
        try:
            return detect(text)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Language detection failed, defaulting to 'unknown': {e}")
            return "unknown"

    def detect_with_regex(self, text: str) -> List[Dict[str, str]]:
        """
        Detects PII in the text using predefined regex patterns.
        Inputs:
            - text: The input text
        Outputs:
            - List of detected PII entities with their type and text
        """
        matches = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            for match in pattern.finditer(text):
                matched_text = match.group().strip()

                # Validate specific PII types
                if pii_type == "credit_card":
                    if not self.validate_credit_card(matched_text):
                        continue
                elif pii_type == "phone":
                    if not self.validate_phone_number(matched_text):
                        continue
                elif pii_type == "email":
                    if not self.validate_email(matched_text):
                        continue
                elif pii_type == "date_of_birth":
                    if not self.validate_dob(matched_text):
                        continue

                matches.append({"type": pii_type, "text": matched_text})
        return matches

    def validate_credit_card(self, card_number: str) -> bool:
        """
        Validates a credit card number using the Luhn algorithm.
        Inputs:
            - card_number: The credit card number as a string
        Outputs:
            - True if valid, False otherwise
        """
        card_number = re.sub(r"[^\d]", "", card_number)  # Remove non-digit characters
        if not 13 <= len(card_number) <= 19:
            return False
        total = 0
        reverse_digits = card_number[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:  # Double every second digit
                n *= 2
                if n > 9:  # Subtract 9 if the result is greater than 9
                    n -= 9
            total += n
        return total % 10 == 0

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validates a phone number based on length and digit count.
        Inputs:
            - phone_number: The phone number as a string
        Outputs:
            - True if valid, False otherwise
        """
        digits = re.sub(r"[^\d]", "", phone_number)  # Remove non-digit characters
        return 10 <= len(digits) <= 15  # Typical phone numbers have 10 to 15 digits

    def validate_email(self, email: str) -> bool:
        """
        Validates an email address using a regex pattern.
        Inputs:
            - email: The email address as a string
        Outputs:
            - True if valid, False otherwise
        """
        email_regex = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        return bool(email_regex.match(email))
    
    def validate_dob(self, date_str: str) -> bool:
        """
        Validates a date of birth string in multiple formats.
        Inputs:
            - date_str: The date string to validate
        Outputs:
            - True if valid, False otherwise
        """
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",  # ISO, US, EU
            "%Y.%m.%d", "%d-%m-%Y", "%m-%d-%Y",   # Other separators
            "%Y%m%d",                             # Compact
            "%d %B %Y", "%B %d %Y"                # Textual (15 May 1990)
        ]
        
        for fmt in formats:
            try:
                dob = datetime.strptime(date_str, fmt)
                # Check if the year is reasonable and not in the future
                if dob.year < 1900 or dob > datetime.now():
                    return False
                return True
            except ValueError:
                continue
        return False

    def llm_verify_and_expand(self, text: str, regex_results: List[Dict[str, str]], language: str) -> List[Dict[str, str]]:
        """
        Validates and expands PII detection using an LLM.
        Inputs:
            - text: The input text
            - regex_results: List of PII detected using regex
            - language: Detected language of the text
        Outputs:
            - List of validated and expanded PII entities
        """
        prompt = f"""
            You are a multilingual privacy assistant. The document is in language {language}.
            Given the document text and a list of PII detected using regex, your task is to:

            1. Validate each regex-detected item and determine if it's truly personally identifiable information (PII) of a specific individual.
            2. Identify ALL additional PII that was missed by the regex detection, including:

            DIRECT PII:
            - Full names, first names only, last names only, nicknames, or initials that can identify a person
            - Email addresses, phone numbers, fax numbers
            - Physical addresses (full or partial, including postal codes) of individuals
            - Social security numbers, national ID numbers, passport numbers
            - Driver's license numbers, tax identification numbers for individuals
            - Date of birth (full or partial), age, place of birth
            - Financial information (credit card numbers, personal bank account details)
            - Biometric data references (fingerprint, retina scan, etc.)
            - Images or descriptions that identify a specific person
            - Social media handles, usernames, or personal URLs

            INDIRECT PII:
            - Booking/reservation codes tied to an individual
            - Order numbers, customer IDs of individuals
            - Invoice/transaction IDs or reference numbers connected to a specific person
            - Patient/student/employee ID numbers
            - Personal membership or loyalty program numbers
            - IP addresses, device identifiers, cookies that can identify an individual
            - Job titles when they can identify a specific person
            - Unique personal characteristics or circumstances
            - Vehicle registration/license plate numbers of individuals
            - Educational institutions when connected to a specific person
            - Workplace/employer information that can identify a specific individual
            - Unique combinations of data that could identify a specific person
            - Travel itinerary details of individuals (flight numbers with dates)
            - Location data that could be tied to a specific individual

            Focus ONLY on information that identifies individual persons. DO NOT include general business information, organization names, or generic business contact details unless they explicitly identify a specific individual.

            Return a JSON list of ALL valid individual PII with each item including:
            - "type": specific type of the PII (be precise)
            - "text": the exact matched text string

            Text:
            {text}

            Language:
            {language}

            Regex-detected PII:
            {json.dumps(regex_results, indent=2)}

            PII:
            """
        try:
            # Send the prompt to the LLM for validation and expansion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2
            )
            reply = response.choices[0].message.content.strip()
            return self.extract_json_from_llm_response(reply)

        except Exception as e:
            if self.logger:
                self.logger.error(f"LLM validation and expansion failed: {e}")
            return regex_results

    def extract_json_from_llm_response(self, reply: str) -> List[Dict[str, str]]:
        """
        Extracts JSON data from the LLM response.
        Inputs:
            - reply: The LLM response as a string
        Outputs:
            - List of PII entities extracted from the JSON response
        """
        cleaned = re.sub(r"^```(?:json)?|```$", "", reply.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            if self.logger:
                self.logger.warning("Falling back to regex parsing for JSON decode error")

            # Fallback to regex-based JSON extraction
            matches = re.findall(r'"type"\s*:\s*"([^"]+)",\s*"text"\s*:\s*"([^"]+)"', cleaned)
            return [{"type": t, "text": txt} for t, txt in matches]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to extract LLM response: {e}")
            return []