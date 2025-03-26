"""
Test configuration
"""

# Test URLs
TEST_URLS = {
    'property_api': 'https://api.example.com/properties',
    'tax_api': 'https://api.example.com/tax',
    'permit_api': 'https://api.example.com/permits',
    'utility_api': 'https://api.example.com/utilities'
}

# Test API Keys
TEST_API_KEYS = {
    'property_api': 'test_property_key',
    'tax_api': 'test_tax_key',
    'permit_api': 'test_permit_key',
    'utility_api': 'test_utility_key'
}

# Test Data
TEST_PROPERTIES = [
    {
        'property_id': 'P123',
        'address': '123 Main St',
        'owner': 'John Doe',
        'value': 300000,
        'sqft': 2000,
        'year_built': 1990,
        'property_type': 'residential',
        'description': 'Beautiful 3-bedroom home'
    },
    {
        'property_id': 'P456',
        'address': '456 Oak Ave',
        'owner': 'Jane Smith',
        'value': 400000,
        'sqft': 2500,
        'year_built': 1985,
        'property_type': 'residential',
        'description': 'Spacious 4-bedroom home'
    }
]

TEST_TAX_RECORDS = [
    {
        'parcel_id': 'T123',
        'address': '123 Main St',
        'owner': 'John Doe',
        'assessment': {
            'land_value': 100000,
            'building_value': 200000,
            'total_value': 300000,
            'assessment_year': 2024
        }
    },
    {
        'parcel_id': 'T456',
        'address': '456 Oak Ave',
        'owner': 'Jane Smith',
        'assessment': {
            'land_value': 150000,
            'building_value': 250000,
            'total_value': 400000,
            'assessment_year': 2024
        }
    }
]

TEST_PERMITS = [
    {
        'permit_id': 'B123',
        'address': '123 Main St',
        'type': 'building',
        'status': 'approved',
        'issue_date': '2025-01-15',
        'description': 'New roof installation'
    },
    {
        'permit_id': 'B456',
        'address': '456 Oak Ave',
        'type': 'building',
        'status': 'pending',
        'issue_date': '2025-01-16',
        'description': 'Kitchen renovation'
    }
]

TEST_UTILITIES = [
    {
        'property_id': 'P123',
        'address': '123 Main St',
        'utilities': {
            'electric': [
                {
                    'date': '2025-01',
                    'usage': 1000,
                    'cost': 150.00
                }
            ],
            'water': [
                {
                    'date': '2025-01',
                    'usage': 5000,
                    'cost': 75.00
                }
            ]
        }
    },
    {
        'property_id': 'P456',
        'address': '456 Oak Ave',
        'utilities': {
            'electric': [
                {
                    'date': '2025-01',
                    'usage': 1200,
                    'cost': 180.00
                }
            ],
            'water': [
                {
                    'date': '2025-01',
                    'usage': 6000,
                    'cost': 90.00
                }
            ]
        }
    }
]

# Test Parameters
TEST_PARAMS = {
    'max_workers': 2,
    'batch_size': 10,
    'cache_ttl': 300,
    'min_confidence': 0.7,
    'max_distance': 0.5,
    'similarity_threshold': 0.8
}

# Test Responses
TEST_RESPONSES = {
    'property_api': {
        'success': True,
        'data': TEST_PROPERTIES,
        'metadata': {
            'total': len(TEST_PROPERTIES),
            'timestamp': '2025-02-19T19:58:00-05:00'
        }
    },
    'tax_api': {
        'success': True,
        'data': TEST_TAX_RECORDS,
        'metadata': {
            'total': len(TEST_TAX_RECORDS),
            'timestamp': '2025-02-19T19:58:00-05:00'
        }
    },
    'permit_api': {
        'success': True,
        'data': TEST_PERMITS,
        'metadata': {
            'total': len(TEST_PERMITS),
            'timestamp': '2025-02-19T19:58:00-05:00'
        }
    },
    'utility_api': {
        'success': True,
        'data': TEST_UTILITIES,
        'metadata': {
            'total': len(TEST_UTILITIES),
            'timestamp': '2025-02-19T19:58:00-05:00'
        }
    }
}

# Test Error Responses
TEST_ERROR_RESPONSES = {
    'api_error': {
        'success': False,
        'error': {
            'code': 500,
            'message': 'Internal server error'
        }
    },
    'rate_limit': {
        'success': False,
        'error': {
            'code': 429,
            'message': 'Rate limit exceeded'
        }
    },
    'invalid_key': {
        'success': False,
        'error': {
            'code': 401,
            'message': 'Invalid API key'
        }
    },
    'not_found': {
        'success': False,
        'error': {
            'code': 404,
            'message': 'Resource not found'
        }
    }
}
