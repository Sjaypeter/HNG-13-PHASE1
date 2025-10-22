from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import AnalyzedString
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
        queryset = AnalyzedString.objects.all()
        params = self.request.query_params

        # Filters
        is_palindrome = params.get('is_palindrome')
        min_length = params.get('min_length')
        max_length = params.get('max_length')
        word_count = params.get('word_count')
        contains_character = params.get('contains_character')

        try:
            if is_palindrome is not None:
                if is_palindrome.lower() in ['true', '1']:
                    queryset = queryset.filter(is_palindrome=True)
                elif is_palindrome.lower() in ['false', '0']:
                    queryset = queryset.filter(is_palindrome=False)
                else:
                    return queryset.none()

            if min_length:
                queryset = queryset.filter(length__gte=int(min_length))
            if max_length:
                queryset = queryset.filter(length__lte=int(max_length))
            if word_count:
                queryset = queryset.filter(word_count=int(word_count))
            if contains_character:
                if len(contains_character) != 1:
                    raise ValueError("contains_character must be a single character.")
                queryset = queryset.filter(value__icontains=contains_character)
        except ValueError:
            # If any invalid query param, raise 400
            raise serializers.ValidationError("Invalid query parameter values or types.")

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            filters_applied = request.query_params.dict()
            return Response({
                "data": serializer.data,
                "count": queryset.count(),
                "filters_applied": filters_applied
            }, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        # Handle missing or invalid body
        if not isinstance(request.data, dict):
            return Response({"detail": "Invalid request body."}, status=status.HTTP_400_BAD_REQUEST)

        if "value" not in request.data:
            return Response({"detail": "Missing 'value' field."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except serializers.ValidationError as e:
            error_text = str(e.detail)

            if "already exists" in error_text.lower():
                return Response({"detail": "String already exists in the system."}, status=status.HTTP_409_CONFLICT)
            elif "must be a string" in error_text.lower():
                return Response({"detail": "Invalid data type for 'value'. Must be a string."},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            elif "cannot be empty" in error_text.lower():
                return Response({"detail": "Value cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StringDetailView(APIView):
    """
    GET /strings/{string_value} - Retrieve one analyzed string
    DELETE /strings/{string_value} - Delete analyzed string
    """

    def get_object(self, string_value):
        return get_object_or_404(AnalyzedString, value=string_value)

    def get(self, request, string_value):
        try:
            obj = self.get_object(string_value)
            serializer = AnalyzedStringSerializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "String not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, string_value):
        obj = AnalyzedString.objects.filter(value=string_value).first()
        if not obj:
            return Response({"detail": "String not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NaturalLanguageFilterView(APIView):
    """
    GET /strings/filter-by-natural-language?query=all single word palindromic strings
    """

    def get(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({"detail": "Missing 'query' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        query = query.lower()
        filters = {}

        # Try to interpret the query
        try:
            if "palindromic" in query or "palindrome" in query:
                filters["is_palindrome"] = True
            if "single word" in query or "one word" in query:
                filters["word_count"] = 1
            match = re.search(r"longer than (\d+)", query)
            if match:
                filters["min_length"] = int(match.group(1)) + 1
            match = re.search(r"containing the letter ([a-z])", query)
            if match:
                filters["contains_character"] = match.group(1)
            if "contain the first vowel" in query or "contain the vowel a" in query:
                filters["contains_character"] = "a"

            if not filters:
                return Response({"detail": "Unable to parse natural language query."},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "Unable to parse natural language query."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Apply filters
        queryset = AnalyzedString.objects.all()
        if filters.get("is_palindrome"):
            queryset = queryset.filter(is_palindrome=True)
        if filters.get("word_count"):
            queryset = queryset.filter(word_count=filters["word_count"])
        if filters.get("min_length"):
            queryset = queryset.filter(length__gte=filters["min_length"])
        if filters.get("contains_character"):
            queryset = queryset.filter(value__icontains=filters["contains_character"])

        serializer = AnalyzedStringSerializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "count": queryset.count(),
            "interpreted_query": {
                "original": query,
                "parsed_filters": filters
            }
        }, status=status.HTTP_200_OK)