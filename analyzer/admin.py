from django.contrib import admin
from .models import AnalyzedString


@admin.register(AnalyzedString)
class AnalyzedStringAdmin(admin.ModelAdmin):
    list_display = ['value_preview', 'sha256_hash_preview', 'length', 'is_palindrome', 'word_count', 'created_at']
    list_filter = ['is_palindrome', 'word_count', 'created_at']
    search_fields = ['value', 'sha256_hash']
    readonly_fields = ['sha256_hash', 'length', 'is_palindrome', 'unique_characters', 
                      'word_count', 'character_frequency_map', 'created_at']
    
    def value_preview(self, obj):
        return obj.value[:50] + ('...' if len(obj.value) > 50 else '')
    value_preview.short_description = 'Value'
    
    def sha256_hash_preview(self, obj):
        return obj.sha256_hash[:16] + '...'
    sha256_hash_preview.short_description = 'Hash'