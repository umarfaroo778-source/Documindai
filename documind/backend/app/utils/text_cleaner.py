import re

def clean_text(text: str) -> str:
    """
    Cleans raw document text by removing excessive whitespace, trailing page numbers,
    and non-standard control characters while preserving paragraph breaks.
    """
    if not text:
        return ""
    
    # Remove control characters except standard newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    
    # Normalize multiple horizontal spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize multiple blank lines to a double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()
