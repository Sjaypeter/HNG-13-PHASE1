# api/serializers.py
from rest_framework import serializers
from .models import AnalyzedString
from .utils import analyze_string

class AnalyzedStringSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='sha256_hash', read_only=True)  # present id as sha256_hash

    class Meta:
        model = AnalyzedString
        fields = [
            'id',
            'value',
            'length',
            'is_palindrome',
            'unique_characters',
            'word_count',
            'sha256_hash',
            'character_frequency_map',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'sha256_hash',
            'length',
            'is_palindrome',
            'unique_characters',
            'word_count',
            'character_frequency_map',
            'created_at',
        ]

    def validate_value(self, value):
        # Missing/empty check handled by required field; here we enforce type
        if not isinstance(value, str):
            raise serializers.ValidationError("Value must be a string.")
        if not value.strip():
            raise serializers.ValidationError("Value cannot be empty or whitespace.")
        return value

    def create(self, validated_data):
        value = validated_data.get("value")
        analysis = analyze_string(value)

        # Duplicate check: if sha256 already exists, raise ValidationError (view maps this to 409)
        if AnalyzedString.objects.filter(sha256_hash=analysis["sha256_hash"]).exists():
            # Raise with this exact message so view can identify it
            raise serializers.ValidationError("String already exists in the system.")

        return AnalyzedString.objects.create(
            value=value,
            sha256_hash=analysis["sha256_hash"],
            length=analysis["length"],
            is_palindrome=analysis["is_palindrome"],
            unique_characters=analysis["unique_characters"],
            word_count=analysis["word_count"],
            character_frequency_map=analysis["character_frequency_map"],
        )