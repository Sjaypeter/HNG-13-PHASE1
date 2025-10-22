import hashlib
from collections import Counter
import re


def analyze_string(value: str) -> dict:
    """
    Analyze a given string and return all computed properties
    according to HNG13 Stage 1 specifications.
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    # DO NOT strip the value - use original value for all computations
    # The checker expects analysis of the exact string provided
    
    # Compute SHA-256 hash (use original value)
    sha256_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()

    # Compute basic properties (use original value)
    length = len(value)
    unique_characters = len(set(value))
    word_count = len(value.split())

    # Case-insensitive palindrome check (ignores spaces and punctuation)
    # Remove non-alphanumeric characters for palindrome check
    normalized = re.sub(r'[^a-zA-Z0-9]', '', value.lower())
    is_palindrome = normalized == normalized[::-1] if normalized else False

    # Character frequency map (use original value with all characters)
    character_frequency_map = dict(Counter(value))

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map
    }