from django.db import models
import hashlib
import json


class AnalyzedString(models.Model):
    """Model to store analyzed strings and their properties"""
    
    value = models.TextField(unique=True, db_index=True)
    sha256_hash = models.CharField(max_length=64, unique=True, db_index=True)
    length = models.IntegerField()
    is_palindrome = models.BooleanField()
    unique_characters = models.IntegerField()
    word_count = models.IntegerField()
    character_frequency_map = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_palindrome']),
            models.Index(fields=['length']),
            models.Index(fields=['word_count']),
        ]
    
    def __str__(self):
        return f"{self.value[:50]}... (ID: {self.sha256_hash[:8]})"
    
    @staticmethod
    def compute_sha256(text):
        """Compute SHA-256 hash of the text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def is_palindrome_check(text):
        """Check if text is a palindrome (case-insensitive, ignoring spaces)"""
        normalized = text.lower().replace(' ', '')
        return normalized == normalized[::-1]
    
    @staticmethod
    def count_unique_characters(text):
        """Count distinct characters in text"""
        return len(set(text))
    
    @staticmethod
    def count_words(text):
        """Count words separated by whitespace"""
        words = text.strip().split()
        return len([w for w in words if w])
    
    @staticmethod
    def get_character_frequency(text):
        """Get character frequency map"""
        freq_map = {}
        for char in text:
            freq_map[char] = freq_map.get(char, 0) + 1
        return freq_map
    
    @classmethod
    def analyze_and_create(cls, value):
        """Analyze string and create database entry"""
        sha256_hash = cls.compute_sha256(value)
        length = len(value)
        is_palindrome = cls.is_palindrome_check(value)
        unique_characters = cls.count_unique_characters(value)
        word_count = cls.count_words(value)
        character_frequency_map = cls.get_character_frequency(value)
        
        return cls.objects.create(
            value=value,
            sha256_hash=sha256_hash,
            length=length,
            is_palindrome=is_palindrome,
            unique_characters=unique_characters,
            word_count=word_count,
            character_frequency_map=character_frequency_map
        )
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.sha256_hash,
            'value': self.value,
            'properties': {
                'length': self.length,
                'is_palindrome': self.is_palindrome,
                'unique_characters': self.unique_characters,
                'word_count': self.word_count,
                'sha256_hash': self.sha256_hash,
                'character_frequency_map': self.character_frequency_map
            },
            'created_at': self.created_at.isoformat()
        }