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

    # Normalize input
    stripped_value = value.strip()

    # Compute SHA-256 hash
    sha256_hash = hashlib.sha256(stripped_value.encode('utf-8')).hexdigest()

    # Compute basic properties
    length = len(stripped_value)
    unique_characters = len(set(stripped_value))
    word_count = len(stripped_value.split())

    # Case-insensitive palindrome check (ignores spaces)
    normalized = re.sub(r'\s+', '', stripped_value.lower())  # remove all whitespace
    is_palindrome = normalized == normalized[::-1]

    # Character frequency map
    character_frequency_map = dict(Counter(stripped_value))

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map
    }