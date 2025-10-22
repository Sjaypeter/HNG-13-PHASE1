from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from .models import AnalyzedString
import re


class StringAnalyzerView(APIView):
    """
    POST /strings - Create and analyze a new string
    GET /strings - Get all strings with optional filtering
    """
    
    def post(self, request):
        """Create and analyze a new string"""
        value = request.data.get('value')
        
        # Validation
        if value is None:
            return Response(
                {'error': 'Missing "value" field'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(value, str):
            return Response(
                {'error': 'Invalid data type for "value" (must be string)'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Check if string already exists
        if AnalyzedString.objects.filter(value=value).exists():
            return Response(
                {'error': 'String already exists in the system'},
                status=status.HTTP_409_CONFLICT
            )
        
        try:
            # Analyze and create
            analyzed_string = AnalyzedString.analyze_and_create(value)
            return Response(
                analyzed_string.to_dict(),
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {'error': 'String already exists in the system'},
                status=status.HTTP_409_CONFLICT
            )
    
    def get(self, request):
        """Get all strings with optional filtering"""
        queryset = AnalyzedString.objects.all()
        filters_applied = {}
        
        try:
            # Apply filters
            is_palindrome = request.query_params.get('is_palindrome')
            if is_palindrome is not None:
                if is_palindrome.lower() == 'true':
                    queryset = queryset.filter(is_palindrome=True)
                    filters_applied['is_palindrome'] = True
                elif is_palindrome.lower() == 'false':
                    queryset = queryset.filter(is_palindrome=False)
                    filters_applied['is_palindrome'] = False
                else:
                    return Response(
                        {'error': 'Invalid is_palindrome parameter'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            min_length = request.query_params.get('min_length')
            if min_length is not None:
                try:
                    min_length = int(min_length)
                    queryset = queryset.filter(length__gte=min_length)
                    filters_applied['min_length'] = min_length
                except ValueError:
                    return Response(
                        {'error': 'Invalid min_length parameter'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            max_length = request.query_params.get('max_length')
            if max_length is not None:
                try:
                    max_length = int(max_length)
                    queryset = queryset.filter(length__lte=max_length)
                    filters_applied['max_length'] = max_length
                except ValueError:
                    return Response(
                        {'error': 'Invalid max_length parameter'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            word_count = request.query_params.get('word_count')
            if word_count is not None:
                try:
                    word_count = int(word_count)
                    queryset = queryset.filter(word_count=word_count)
                    filters_applied['word_count'] = word_count
                except ValueError:
                    return Response(
                        {'error': 'Invalid word_count parameter'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            contains_character = request.query_params.get('contains_character')
            if contains_character is not None:
                if len(contains_character) != 1:
                    return Response(
                        {'error': 'contains_character must be a single character'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(value__contains=contains_character)
                filters_applied['contains_character'] = contains_character
            
            # Prepare response
            data = [obj.to_dict() for obj in queryset]
            return Response({
                'data': data,
                'count': len(data),
                'filters_applied': filters_applied
            })
            
        except Exception as e:
            return Response(
                {'error': 'Invalid query parameter values or types'},
                status=status.HTTP_400_BAD_REQUEST
            )


class StringDetailView(APIView):
    """
    GET /strings/{string_value} - Get specific string
    DELETE /strings/{string_value} - Delete specific string
    """
    
    def get(self, request, string_value):
        """Get specific string by value"""
        try:
            analyzed_string = AnalyzedString.objects.get(value=string_value)
            return Response(analyzed_string.to_dict())
        except AnalyzedString.DoesNotExist:
            return Response(
                {'error': 'String does not exist in the system'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, string_value):
        """Delete specific string by value"""
        try:
            analyzed_string = AnalyzedString.objects.get(value=string_value)
            analyzed_string.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalyzedString.DoesNotExist:
            return Response(
                {'error': 'String does not exist in the system'},
                status=status.HTTP_404_NOT_FOUND
            )


class NaturalLanguageFilterView(APIView):
    """
    GET /strings/filter-by-natural-language - Filter strings using natural language
    """
    
    def parse_natural_language(self, query):
        """Parse natural language query into filters"""
        filters = {}
        query_lower = query.lower()
        
        # Check for palindrome
        if 'palindrom' in query_lower:
            filters['is_palindrome'] = True
        
        # Check for single word
        if 'single word' in query_lower:
            filters['word_count'] = 1
        
        # Check for length constraints
        longer_than_match = re.search(r'longer than (\d+)', query_lower)
        if longer_than_match:
            filters['min_length'] = int(longer_than_match.group(1)) + 1
        
        shorter_than_match = re.search(r'shorter than (\d+)', query_lower)
        if shorter_than_match:
            filters['max_length'] = int(shorter_than_match.group(1)) - 1
        
        # Check for contains character
        contains_match = re.search(r'contain(?:s|ing)?\s+(?:the\s+)?(?:letter\s+)?([a-z])', query_lower)
        if contains_match:
            filters['contains_character'] = contains_match.group(1)
        
        # Check for first vowel
        if 'first vowel' in query_lower:
            filters['contains_character'] = 'a'
        
        return filters
    
    def get(self, request):
        """Filter strings using natural language query"""
        query = request.query_params.get('query')
        
        if not query:
            return Response(
                {'error': 'Missing query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Parse natural language
            parsed_filters = self.parse_natural_language(query)
            
            # Apply filters
            queryset = AnalyzedString.objects.all()
            
            if 'is_palindrome' in parsed_filters:
                queryset = queryset.filter(is_palindrome=parsed_filters['is_palindrome'])
            
            if 'min_length' in parsed_filters:
                queryset = queryset.filter(length__gte=parsed_filters['min_length'])
            
            if 'max_length' in parsed_filters:
                queryset = queryset.filter(length__lte=parsed_filters['max_length'])
            
            if 'word_count' in parsed_filters:
                queryset = queryset.filter(word_count=parsed_filters['word_count'])
            
            if 'contains_character' in parsed_filters:
                queryset = queryset.filter(value__contains=parsed_filters['contains_character'])
            
            data = [obj.to_dict() for obj in queryset]
            
            return Response({
                'data': data,
                'count': len(data),
                'interpreted_query': {
                    'original': query,
                    'parsed_filters': parsed_filters
                }
            })
            
        except Exception as e:
            return Response(
                {'error': 'Unable to parse natural language query'},
                status=status.HTTP_400_BAD_REQUEST
            )