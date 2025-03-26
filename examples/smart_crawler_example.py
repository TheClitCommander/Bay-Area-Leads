"""
Example usage of the SmartCrawler
"""
import asyncio
import json
from src.collectors.smart_crawler import SmartCrawler
import logging
import os

async def crawl_website(start_url: str, output_dir: str):
    """
    Crawl a website and extract all available data
    """
    # Configure the crawler
    config = {
        'max_depth': 3,           # How deep to crawl
        'max_pages': 100,         # Maximum pages to process
        'use_selenium': True,     # Use Selenium for JavaScript rendering
        'cache_dir': 'cache',     # Where to store cache
    }
    
    # Initialize crawler
    async with SmartCrawler(config) as crawler:
        # Start crawling
        pages_data = await crawler.crawl(start_url)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Export data
        crawler.export_data(output_dir)
        
        # Save detailed page data
        with open(os.path.join(output_dir, 'pages_data.json'), 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            serializable_data = {}
            for url, page_data in pages_data.items():
                page_dict = {
                    'url': page_data.url,
                    'title': page_data.title,
                    'content_type': page_data.content_type,
                    'features': {
                        'has_tables': page_data.features.has_tables,
                        'has_forms': page_data.features.has_forms,
                        'has_maps': page_data.features.has_maps,
                        'has_downloads': page_data.features.has_downloads,
                        'has_search': page_data.features.has_search,
                        'has_pagination': page_data.features.has_pagination,
                        'has_api_endpoints': page_data.features.has_api_endpoints,
                        'interactive_elements': page_data.features.interactive_elements,
                        'frameworks_detected': page_data.features.frameworks_detected
                    },
                    'extracted_data': page_data.extracted_data,
                    'related_pages': page_data.related_pages,
                    'timestamp': page_data.timestamp.isoformat(),
                    'metadata': page_data.metadata
                }
                serializable_data[url] = page_dict
            json.dump(serializable_data, f, indent=2)
            
        # Print summary
        print(f"\nCrawl Summary:")
        print(f"Pages processed: {len(pages_data)}")
        print(f"Output directory: {output_dir}")
        print("\nFeatures found:")
        features_count = {
            'Tables': sum(1 for p in pages_data.values() if p.features.has_tables),
            'Forms': sum(1 for p in pages_data.values() if p.features.has_forms),
            'Maps': sum(1 for p in pages_data.values() if p.features.has_maps),
            'Downloads': sum(1 for p in pages_data.values() if p.features.has_downloads),
            'Search': sum(1 for p in pages_data.values() if p.features.has_search),
            'API Endpoints': sum(1 for p in pages_data.values() if p.features.has_api_endpoints)
        }
        for feature, count in features_count.items():
            print(f"- {feature}: {count}")

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Example URLs to crawl
    examples = {
        'tax_maps': 'https://www.brunswickme.gov/DocumentCenter/View/10542',
        'property_data': 'https://gis.vgsi.com/brunswickme/Search.aspx',
        'school_data': 'https://www.maine.gov/doe/dashboard',
        'census_data': 'https://www.census.gov/quickfacts/brunswickcdpmaine'
    }
    
    # Select which site to crawl
    site_type = 'tax_maps'  # Change this to crawl different sites
    start_url = examples[site_type]
    output_dir = f'output/{site_type}'
    
    # Run the crawler
    asyncio.run(crawl_website(start_url, output_dir))

if __name__ == "__main__":
    main()
