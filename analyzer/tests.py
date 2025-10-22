import requests
import json

BASE_URL = 'http://localhost:8000'

def print_response(response):
    """Pretty print response"""
    print(f"Status: {response.status_code}")
    if response.content:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    print("-" * 80)

def run_tests():
    """Run comprehensive API tests"""
    
    print("=" * 80)
    print("STRING ANALYZER SERVICE - API TESTS")
    print("=" * 80)
    
    # Test 1: Create a palindrome
    print("\n1. CREATE PALINDROME 'racecar'")
    response = requests.post(
        f'{BASE_URL}/strings',
        json={'value': 'racecar'},
        headers={'Content-Type': 'application/json'}
    )
    print_response(response)
    assert response.status_code == 201, "Should return 201"
    data = response.json()
    assert data['properties']['is_palindrome'] == True, "Should be palindrome"
    assert data['properties']['length'] == 7, "Length should be 7"
    assert data['properties']['word_count'] == 1, "Word count should be 1"
    print("✅ Test 1 PASSED\n")
    
    # Test 2: Create non-palindrome
    print("\n2. CREATE NON-PALINDROME 'hello world'")
    response = requests.post(
        f'{BASE_URL}/strings',
        json={'value': 'hello world'},
        headers={'Content-Type': 'application/json'}
    )
    print_response(response)
    assert response.status_code == 201, "Should return 201"
    data = response.json()
    assert data['properties']['is_palindrome'] == False, "Should not be palindrome"
    assert data['properties']['word_count'] == 2, "Word count should be 2"
    print("✅ Test 2 PASSED\n")
    
    # Test 3: Try to create duplicate
    print("\n3. TRY TO CREATE DUPLICATE 'racecar'")
    response = requests.post(
        f'{BASE_URL}/strings',
        json={'value': 'racecar'},
        headers={'Content-Type': 'application/json'}
    )
    print_response(response)
    assert response.status_code == 409, "Should return 409 Conflict"
    print("✅ Test 3 PASSED\n")
    
    # Test 4: Get specific string
    print("\n4. GET SPECIFIC STRING 'racecar'")
    response = requests.get(f'{BASE_URL}/strings/racecar')
    print_response(response)
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data['value'] == 'racecar', "Should return correct string"
    print("✅ Test 4 PASSED\n")
    
    # Test 5: Get non-existent string
    print("\n5. GET NON-EXISTENT STRING")
    response = requests.get(f'{BASE_URL}/strings/nonexistent')
    print_response(response)
    assert response.status_code == 404, "Should return 404"
    print("✅ Test 5 PASSED\n")
    
    # Test 6: Get all strings with filter (palindromes)
    print("\n6. GET ALL PALINDROMES")
    response = requests.get(f'{BASE_URL}/strings?is_palindrome=true')
    print_response(response)
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data['count'] >= 1, "Should have at least 1 palindrome"
    assert 'filters_applied' in data, "Should include filters_applied"
    print("✅ Test 6 PASSED\n")
    
    # Test 7: Get with multiple filters
    print("\n7. GET WITH MULTIPLE FILTERS")
    response = requests.get(f'{BASE_URL}/strings?is_palindrome=true&word_count=1&min_length=5')
    print_response(response)
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert 'filters_applied' in data, "Should include filters_applied"
    print("✅ Test 7 PASSED\n")
    
    # Test 8: Natural language query
    print("\n8. NATURAL LANGUAGE QUERY - 'single word palindromic strings'")
    response = requests.get(
        f'{BASE_URL}/strings/filter-by-natural-language',
        params={'query': 'single word palindromic strings'}
    )
    print_response(response)
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert 'interpreted_query' in data, "Should include interpreted_query"
    assert data['interpreted_query']['parsed_filters']['word_count'] == 1, "Should parse word_count"
    assert data['interpreted_query']['parsed_filters']['is_palindrome'] == True, "Should parse is_palindrome"
    print("✅ Test 8 PASSED\n")
    
    # Test 9: Natural language query - longer than
    print("\n9. NATURAL LANGUAGE QUERY - 'strings longer than 5 characters'")
    response = requests.get(
        f'{BASE_URL}/strings/filter-by-natural-language',
        params={'query': 'strings longer than 5 characters'}
    )
    print_response(response)
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert 'min_length' in data['interpreted_query']['parsed_filters'], "Should parse min_length"
    print("✅ Test 9")