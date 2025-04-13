import argparse
import json
from pathlib import Path
from difflib import SequenceMatcher
import re
from typing import Dict, List

import fitz  # PyMuPDF
from rich import print
from rich.table import Table


def load_ground_truth(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pii"]


def extract_pdf_text_by_page(pdf_path: Path) -> str:
    """
    Extracts and concatenates text from all pages of a PDF into a single string.

    Args:
        pdf_path (Path): Path to the PDF file.

    Returns:
        str: Full concatenated text from all pages.
    """
    doc = fitz.open(pdf_path)
    full_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text.append(page.get_text())
    return "\n".join(full_text)


def normalize(text):
    return text.lower().strip().replace("\n", " ")


def match_score(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def evaluate_redaction(original_text: str, ground_truth_pii: List[Dict], redacted_text: str) -> Dict:
    """
    Evaluate the accuracy of PII redaction by comparing ground truth PII with the redacted text and the original text.
    
    Args:
        original_text (str): The original text extracted from the input PDF (before redaction).
        ground_truth_pii (List[Dict]): List of PII items with information like text and page numbers.
        redacted_text (str): The text extracted from the redacted PDF.

    Returns:
        Dict: Evaluation metrics containing TP, FN, FP, Precision, Recall, F1-Score, and lists of missed or wrongly redacted items.
    """
    true_positives = 0
    false_negatives = 0
    false_positives = 0
    missed = []
    wrongly_redacted = []

    # Normalize texts for comparison
    normalized_redacted = normalize(redacted_text)
    normalized_original = normalize(original_text)
    
    # Check each PII item in ground truth
    for pii in ground_truth_pii:
        pii_text = normalize(pii["text"])
        page = pii.get("page", "unknown")
        
        # Check if PII text exists in the original
        if pii_text not in normalized_original:
            continue  # Skip if PII wasn't in original text (shouldn't happen)
            
        # If PII is found in redacted text, it wasn't properly redacted (false negative)
        if pii_text in normalized_redacted:
            false_negatives += 1
            missed.append({"page": page, "text": pii["text"]})
        else:
            true_positives += 1
    
    # Find potential false positives by comparing significant differences between the original and redacted text
    # that are not related to our known PII
    
    # Create a list of known PII terms that should be redacted
    pii_terms = []
    for pii in ground_truth_pii:
        # Add the full PII text
        pii_terms.append(normalize(pii["text"]))
        # Add individual words from multi-word PII
        for word in normalize(pii["text"]).split():
            if len(word) > 3:  # Only add meaningful words
                pii_terms.append(word)
    
    # Extract all words from the original text
    original_words = set(re.findall(r'\b\w+\b', normalized_original))
    redacted_words = set(re.findall(r'\b\w+\b', normalized_redacted))
    
    # Words that were in original but are missing from redacted
    potentially_redacted_words = original_words - redacted_words
    
    # Check if any significant word was redacted but wasn't in our ground truth
    for word in potentially_redacted_words:
        if len(word) > 3:  # Only consider meaningful words
            # Skip words that are part of known PII
            if not any(word.lower() in pii_term.lower() for pii_term in pii_terms):
                false_positives += 1
                wrongly_redacted.append({"text": word})
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "missed": missed,
        "wrongly_redacted": wrongly_redacted
    }


def print_results(results):
    table = Table(title="📊 PII Redaction Evaluation")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="magenta")

    table.add_row("True Positives", str(results["true_positives"]))
    table.add_row("False Negatives", str(results["false_negatives"]))
    table.add_row("False Positives", str(results["false_positives"]))
    table.add_row("Precision", f"{results['precision']:.4f}")
    table.add_row("Recall", f"{results['recall']:.4f}")
    table.add_row("F1-Score", f"{results['f1_score']:.4f}")

    print(table)

    if results["missed"]:
        print("\n[bold red]❌ Missed Entities (Not Redacted):[/bold red]")
        for m in results["missed"]:
            print(f"  - Page {m['page']}: '{m['text']}'")
    
    if results["wrongly_redacted"]:
        print("\n[bold yellow]⚠️ Wrongly Redacted (False Positives):[/bold yellow]")
        for w in results["wrongly_redacted"]:
            print(f"  - '{w['text']}'")

def evaluate(input_path, output_path, ground_truth):
    """Evaluate the PII redaction results by comparing the original and redacted PDFs with the ground truth."""

    ground_truth = load_ground_truth(Path(ground_truth))
    original_text = extract_pdf_text_by_page(Path(input_path))
    redacted_text = extract_pdf_text_by_page(Path(output_path))
    results = evaluate_redaction(original_text, ground_truth, redacted_text)
    print_results(results)
    return results

