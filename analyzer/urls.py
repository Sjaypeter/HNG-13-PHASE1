from django.urls import path
from .views import (
    StringListCreateView,
    StringDetailView,
    NaturalLanguageFilterView,
)

urlpatterns = [
    # Natural language filter MUST come first to avoid being caught by the detail view
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='natural-language-filter'),
    
    # List and create endpoint
    path('strings', StringListCreateView.as_view(), name='list-create-strings'),
    
    # Detail and delete endpoint (by SHA256 hash ID)
    path('strings/<str:string_value>', StringDetailView.as_view(), name='string-detail'),
]