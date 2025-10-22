from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from analyzer.models import AnalyzedString
from .serializers import AnalyzedStringSerializer
import re


class StringListCreateView(generics.ListCreateAPIView):
    """
    GET /strings - List all strings (with optional filters)
    POST /strings - Analyze and save a new string
    """
    serializer_class = AnalyzedStringSerializer
    queryset = AnalyzedString.objects.all()

    def get_queryset(self):
        """Apply query parameter filters to the queryset."""
        queryset = AnalyzedString.objects.all()
        params = self.request.query_params

        # Extract filter parameters
        is_palindrome = params.get('is_palindrome')
        min_length = params.get('min_length')
        max_length = params.get('max_length')
        word_count = params.get('word_count')
        contains_character = params.get('contains_character')

        try:
            # Palindrome filter
            if is_palindrome is not None:
                is_palindrome_lower = is_palindrome.lower()
                if is_palindrome_lower in ['true', '1']:
                    queryset = queryset.filter(is_palindrome=True)
                elif is_palindrome_lower in ['false', '0']:
                    queryset = queryset.filter(is_palindrome=False)
                else:
                    raise serializers.ValidationError("Invalid value for 'is_palindrome'. Use 'true' or 'false'.")

            # Length filters
            if min_length:
                queryset = queryset.filter(length__gte=int(min_length))
            if max_length:
                queryset = queryset.filter(length__lte=int(max_length))
            
            # Word count filter
            if word_count:
                queryset = queryset.filter(word_count=int(word_count))
            
            # Character contains filter
            if contains_character:
                if len(contains_character) != 1:
                    raise serializers.ValidationError("'contains_character' must be a single character.")
                queryset = queryset.filter(value__icontains=contains_character)

        except ValueError as e:
            raise serializers.ValidationError(f"Invalid query parameter type: {str(e)}")

        return queryset

    def list(self, request, *args, **kwargs):
        """Handle GET request with filters."""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                "data": serializer.data,
                "count": queryset.count(),
                "filters_applied": request.query_params.dict()
            }, status=status.HTTP_200_OK)
            
        except serializers.ValidationError as e:
            return Response(
                {"detail": str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        """Handle POST request to create a new analyzed string."""
        # Validate request body structure
        if not isinstance(request.data, dict):
            return Response(
                {"detail": "Invalid request body. Expected JSON object."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for required 'value' field
        if "value" not in request.data:
            return Response(
                {"detail": "Missing required field: 'value'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that value is a string (not number, null, etc.)
        value = request.data.get("value")
        if not isinstance(value, str):
            return Response(
                {"detail": "Invalid data type for 'value'. Must be a string."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Serialize and validate
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        except serializers.ValidationError as e:
            # Extract error message
            error_detail = e.detail
            if isinstance(error_detail, dict):
                error_text = str(error_detail.get('value', error_detail))
            else:
                error_text = str(error_detail)

            error_text_lower = error_text.lower()

            # Handle specific error cases
            if "already exists" in error_text_lower or "unique" in error_text_lower:
                return Response(
                    {"detail": "String with this value already exists."},
                    status=status.HTTP_409_CONFLICT
                )
            elif "cannot be empty" in error_text_lower or "blank" in error_text_lower:
                return Response(
                    {"detail": "Value cannot be empty or blank."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"detail": error_text},
                    status=status.HTTP_400_BAD_REQUEST
                )


class StringDetailView(APIView):
    """
    GET /strings/{string_value} - Retrieve a specific analyzed string
    DELETE /strings/{string_value} - Delete a specific analyzed string
    """

    def get(self, request, string_value):
        """Retrieve a single string by its value."""
        try:
            obj = get_object_or_404(AnalyzedString, value=string_value)
            serializer = AnalyzedStringSerializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"detail": "String not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, string_value):
        """Delete a string by its value."""
        try:
            obj = get_object_or_404(AnalyzedString, value=string_value)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {"detail": "String not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class NaturalLanguageFilterView(APIView):
    """
    GET /strings/filter-by-natural-language
    
    Accepts a natural language query and interprets it to filter strings.
    Example: ?query=all single word palindromic strings
    """

    def get(self, request):
        """Parse natural language query and return filtered results."""
        query = request.query_params.get('query')
        
        if not query:
            return Response(
                {"detail": "Missing required parameter: 'query'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_lower = query.lower()
        filters = {}

        try:
            # Parse palindrome keywords
            if any(keyword in query_lower for keyword in ["palindrome", "palindromic"]):
                filters["is_palindrome"] = True

            # Parse word count keywords
            if any(phrase in query_lower for phrase in ["single word", "one word", "1 word"]):
                filters["word_count"] = 1
            elif any(phrase in query_lower for phrase in ["two word", "2 word"]):
                filters["word_count"] = 2

            # Parse length requirements
            longer_match = re.search(r"longer than (\d+)", query_lower)
            if longer_match:
                filters["min_length"] = int(longer_match.group(1)) + 1

            shorter_match = re.search(r"shorter than (\d+)", query_lower)
            if shorter_match:
                filters["max_length"] = int(shorter_match.group(1)) - 1

            # Parse character contains requirements
            letter_match = re.search(r"containing (?:the )?(?:letter |character )?['\"]?([a-z])['\"]?", query_lower)
            if letter_match:
                filters["contains_character"] = letter_match.group(1)

            # Special cases for vowels
            if any(phrase in query_lower for phrase in ["first vowel", "vowel a", "letter a"]):
                filters["contains_character"] = "a"

            # If no filters were detected, return error
            if not filters:
                return Response(
                    {"detail": "Unable to parse natural language query. No recognizable filters found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"detail": f"Error parsing query: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Apply parsed filters to queryset
        queryset = AnalyzedString.objects.all()

        if filters.get("is_palindrome") is not None:
            queryset = queryset.filter(is_palindrome=filters["is_palindrome"])
        
        if filters.get("word_count") is not None:
            queryset = queryset.filter(word_count=filters["word_count"])
        
        if filters.get("min_length") is not None:
            queryset = queryset.filter(length__gte=filters["min_length"])
        
        if filters.get("max_length") is not None:
            queryset = queryset.filter(length__lte=filters["max_length"])
        
        if filters.get("contains_character"):
            queryset = queryset.filter(value__icontains=filters["contains_character"])

        # Serialize and return results
        serializer = AnalyzedStringSerializer(queryset, many=True)
        
        return Response({
            "data": serializer.data,
            "count": queryset.count(),
            "interpreted_query": {
                "original": query,
                "parsed_filters": filters
            }
        }, status=status.HTTP_200_OK)