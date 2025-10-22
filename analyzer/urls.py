from django.urls import path
from .views import (
    StringListCreateView,
    StringDetailView,
    NaturalLanguageFilterView,
)

urlpatterns = [
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='natural-language-filter'),
    path('strings', StringListCreateView.as_view(), name='list-create-strings'),
    # Detail & delete endpoint
    path('strings/<path:string_value>', StringDetailView.as_view(), name='string-detail'),
]