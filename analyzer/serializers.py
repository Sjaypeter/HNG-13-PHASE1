# api/serializers.py
from rest_framework import serializers
from .models import AnalyzedString
from .utils import analyze_string

class AnalyzedStringSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='sha256_hash', read_only=True)

    class Meta:
        model = AnalyzedString
        fields = [
            'id',
            'value',
            'length',
            'is_palindrome',
            'unique_characters',
            'word_count',
            'character_frequency_map',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'length',
            'is_palindrome',
            'unique_characters',
            'word_count',
            'character_frequency_map',
            'created_at',
        ]

    def validate_value(self, value):
        # Type validation
        if not isinstance(value, str):
            raise serializers.ValidationError("Value must be a string.")
        
        # Empty/whitespace validation
        if not value or not value.strip():
            raise serializers.ValidationError("Value cannot be empty or whitespace.")
        
        return value

    def create(self, validated_data):
        value = validated_data.get("value")
        
        # Analyze the string
        analysis = analyze_string(value)
        
        # Check for duplicate - let the view handle 409 response
        sha256_hash = analysis["sha256_hash"]
        if AnalyzedString.objects.filter(sha256_hash=sha256_hash).exists():
            raise serializers.ValidationError({
                "value": "A string with this value already exists."
            })
        
        # Create the object
        return AnalyzedString.objects.create(
            value=value,
            sha256_hash=sha256_hash,
            length=analysis["length"],
            is_palindrome=analysis["is_palindrome"],
            unique_characters=analysis["unique_characters"],
            word_count=analysis["word_count"],
            character_frequency_map=analysis["character_frequency_map"],
        )