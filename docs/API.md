# MidcoastLeads API Documentation

## Core Components

### LeadProcessor

The main interface for the lead generation system.

#### Methods

##### `process_leads(raw_data: List[Dict]) -> Dict`
Process raw lead data through all components.

Parameters:
- `raw_data`: List of dictionaries containing raw property data
  ```python
  {
      'property_id': str,
      'address': str,
      'owner': str,
      'tax_data': Dict,
      'permits': List[Dict],
      'utilities': Dict,
      'description': str
  }
  ```

Returns:
```python
{
    'processed_data': List[Dict],  # Cleaned and enriched property data
    'analysis_results': Dict,      # Analysis results
    'predictions': Dict,           # Predictions
    'visualizations': Dict,        # Generated visualizations
    'summary': Dict,              # Summary of results
    'recommendations': List[Dict], # Action recommendations
    'metadata': Dict              # Processing metadata
}
```

##### `update_leads(new_data: List[Dict]) -> Dict`
Update existing processed leads with new data.

Parameters:
- `new_data`: List of dictionaries containing new property data

Returns: Same structure as `process_leads()`

##### `get_top_opportunities(filters: Dict = None, limit: int = 10) -> List[Dict]`
Get top investment opportunities.

Parameters:
- `filters`: Optional dictionary of filters
  ```python
  {
      'min_value': float,
      'max_value': float,
      'property_types': List[str],
      'locations': List[str],
      'min_score': float
  }
  ```
- `limit`: Maximum number of opportunities to return

Returns:
```python
[{
    'property_id': str,
    'total_score': float,
    'opportunity_type': str,
    'property_data': Dict,
    'analysis': Dict,
    'predictions': Dict,
    'visualizations': Dict
}]
```

### DataEnricher

Enriches property data with additional context and derived metrics.

#### Methods

##### `enrich_property(property_data: Dict) -> Dict`
Enrich a single property with additional data.

Parameters:
- `property_data`: Dictionary containing property data

Returns:
```python
{
    'property_id': str,
    'enriched_data': {
        'derived_metrics': Dict,
        'market_context': Dict,
        'geographic_context': Dict,
        'temporal_context': Dict
    }
}
```

### InvestmentAnalyzer

Analyzes investment patterns and opportunities.

#### Methods

##### `analyze_investments(properties: List[Dict]) -> Dict`
Analyze investment patterns across properties.

Returns:
```python
{
    'patterns': {
        'value_patterns': Dict,
        'temporal_patterns': Dict,
        'geographic_patterns': Dict,
        'property_type_patterns': Dict
    },
    'opportunities': List[Dict],
    'risks': List[Dict],
    'recommendations': List[Dict]
}
```

### NetworkAnalyzer

Analyzes networks between properties, owners, and market activities.

#### Methods

##### `analyze_owner_networks(properties: List[Dict]) -> Dict`
Analyze networks between property owners.

Returns:
```python
{
    'network_stats': Dict,
    'communities': List[Dict],
    'patterns': Dict,
    'key_players': List[Dict],
    'relationships': List[Dict]
}
```

### TextAnalyzer

Analyzes text data from property descriptions and documents.

#### Methods

##### `analyze_property_descriptions(properties: List[Dict]) -> Dict`
Analyze property descriptions for insights.

Returns:
```python
{
    'features': Dict,
    'sentiments': List[Dict],
    'similarities': List[Dict],
    'conditions': Dict,
    'summaries': List[str]
}
```

## Data Models

### Property
```python
{
    'property_id': str,
    'address': {
        'street': str,
        'city': str,
        'state': str,
        'zip': str,
        'coordinates': {
            'latitude': float,
            'longitude': float
        }
    },
    'owner': {
        'name': str,
        'contact': Dict,
        'ownership_history': List[Dict]
    },
    'assessment': {
        'land_value': float,
        'building_value': float,
        'total_value': float,
        'assessment_year': int
    },
    'characteristics': {
        'property_type': str,
        'year_built': int,
        'square_feet': float,
        'bedrooms': int,
        'bathrooms': float,
        'lot_size': float
    },
    'transactions': List[Dict],
    'permits': List[Dict],
    'utilities': Dict,
    'description': str,
    'metadata': Dict
}
```

### Market
```python
{
    'market_id': str,
    'location': {
        'city': str,
        'state': str,
        'boundaries': Dict
    },
    'metrics': {
        'median_price': float,
        'price_per_sqft': float,
        'days_on_market': int,
        'inventory_level': int
    },
    'trends': {
        'price_trends': List[Dict],
        'volume_trends': List[Dict],
        'seasonal_patterns': Dict
    },
    'segments': {
        'property_types': Dict,
        'price_ranges': Dict,
        'locations': Dict
    }
}
```

## Configuration

### Environment Variables
```bash
# API Keys
PROPERTY_API_KEY=your_api_key
TAX_API_KEY=your_api_key
PERMIT_API_KEY=your_api_key

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=midcoast_leads
DB_USER=user
DB_PASSWORD=password

# Processing
MAX_WORKERS=4
BATCH_SIZE=100
CACHE_DIR=/path/to/cache

# Analysis
MIN_CONFIDENCE_SCORE=0.7
MAX_CLUSTER_DISTANCE=0.5
SIMILARITY_THRESHOLD=0.8
```

### Component Configuration
```python
{
    'cleaner_config': {
        'remove_duplicates': bool,
        'fill_missing': bool,
        'validation_rules': Dict
    },
    'standardizer_config': {
        'address_format': str,
        'phone_format': str,
        'date_format': str
    },
    'merger_config': {
        'match_threshold': float,
        'merge_strategy': str
    },
    'enricher_config': {
        'data_sources': List[str],
        'cache_ttl': int
    },
    'analyzer_config': {
        'min_confidence': float,
        'max_distance': float
    }
}
```

## Error Handling

### Error Types
1. `DataValidationError`: Invalid or missing data
2. `ProcessingError`: Error during data processing
3. `AnalysisError`: Error during analysis
4. `PredictionError`: Error during prediction
5. `VisualizationError`: Error generating visualizations

### Error Response Format
```python
{
    'error': {
        'type': str,
        'message': str,
        'details': Dict,
        'timestamp': str
    }
}
```

## Best Practices

1. Data Collection
   - Always validate raw data
   - Handle rate limits gracefully
   - Cache responses when possible
   - Log collection errors

2. Data Processing
   - Process in batches
   - Use parallel processing
   - Validate intermediate results
   - Handle missing data appropriately

3. Analysis
   - Set confidence thresholds
   - Validate assumptions
   - Handle outliers
   - Document limitations

4. Visualization
   - Use consistent styling
   - Include legends and labels
   - Make visualizations interactive
   - Optimize for different devices

5. Error Handling
   - Log all errors
   - Provide meaningful messages
   - Include error context
   - Handle gracefully

## Examples

### Basic Usage
```python
from src.processors.lead_processor import LeadProcessor

# Initialize processor
processor = LeadProcessor()

# Process leads
results = processor.process_leads(raw_data)

# Get top opportunities
opportunities = processor.get_top_opportunities(
    filters={
        'min_value': 200000,
        'property_types': ['residential'],
        'min_score': 0.8
    },
    limit=10
)

# Generate reports
reports = processor.generate_reports(
    property_ids=['prop1', 'prop2'],
    report_type='full'
)
```

### Advanced Usage
```python
# Custom analysis
analysis_results = processor.analyze_data(
    properties,
    analysis_types=['investment', 'network', 'text']
)

# Market analysis
market_analysis = processor.analyze_market(market_data)

# Update data
updated_results = processor.update_leads(new_data)

# Generate visualizations
visualizations = processor.visualization_generator.create_visualizations(
    data=analysis_results,
    types=['map', 'network', 'trends']
)
```
