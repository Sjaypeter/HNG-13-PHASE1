from django.contrib import admin
from django.urls import path, re_path
from .views import (
    StringAnalyzerView,
    StringDetailView,
    NaturalLanguageFilterView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Natural language filter MUST come before detail view to avoid route conflicts
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='natural-language-filter'),
    
    # String list and create
    path('strings', StringAnalyzerView.as_view(), name='string-list-create'),
    
    # String detail and delete (using re_path to capture everything after strings/)
    re_path(r'^strings/(?P<string_value>.+)$', StringDetailView.as_view(), name='string-detail'),
]