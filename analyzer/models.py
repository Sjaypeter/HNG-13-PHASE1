from django.db import models
import hashlib
import json

class AnalyzedString(models.Model):
    value = models.TextField(unique=True)  # The actual string provided by user
    sha256_hash = models.CharField(max_length=64, unique=True)  # Unique ID for the string

    # Computed properties
    length = models.IntegerField()
    is_palindrome = models.BooleanField()
    unique_characters = models.IntegerField()
    word_count = models.IntegerField()
    character_frequency_map = models.JSONField()  # Stores dictionary of character frequencies

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.value[:30]}..." if len(self.value) > 30 else self.value

    def save(self, *args, **kwargs):
        # Ensure SHA256 hash is generated before saving
        if not self.sha256_hash:
            self.sha256_hash = hashlib.sha256(self.value.encode()).hexdigest()
        super().save(*args, **kwargs)
