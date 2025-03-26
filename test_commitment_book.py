"""
Test script for Commitment Book collector and Data Manager
"""
import logging
from pathlib import Path
from src.collectors.commitment_book_collector import CommitmentBookCollector
from src.utils.data_manager import DataManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_data_manager():
    """Test data manager functionality"""
    print("\n=== Testing Data Manager ===")
    dm = DataManager()
    
    # Test directory structure
    print("\n1. Checking directory structure...")
    base_dir = Path(dm.base_dir)
    for category in ['raw', 'processed', 'temp']:
        dir_path = base_dir / category
        exists = dir_path.exists()
        print(f"   {'✓' if exists else '✗'} {category} directory: {dir_path}")
        
    # List any existing files
    print("\n2. Existing files in structure:")
    for category in dm.structure:
        files = dm.list_files(category)
        if files:
            print(f"\n   {category}:")
            for file_info in files:
                print(f"   - {Path(file_info['path']).name}")
                
def test_commitment_book_collector():
    """Test commitment book collector"""
    print("\n=== Testing Commitment Book Collector ===")
    collector = CommitmentBookCollector()
    
    print("\n1. Downloading commitment book...")
    data = collector.collect()
    
    print("\n2. Collection Results:")
    total = len(data['properties'])
    print(f"   Total properties collected: {total}")
    
    if data['properties']:
        print("\n3. Sample Property Data (first 5):")
        for i, prop in enumerate(data['properties'][:5], 1):
            print(f"\n   Property {i}:")
            print(f"   Raw Text:\n   {'-' * 80}")
            raw_text = prop.get('raw_text', '')
            lines = raw_text.split('\n')
            for line in lines:
                print(f"   {line}")
            print(f"   {'-' * 80}")
            print("   Extracted Data:")
            # Sort keys for consistent output
            sorted_keys = sorted(prop.keys())
            for key in sorted_keys:
                if key != 'raw_text':
                    print(f"   {key:20}: {prop[key]}")
    else:
        print("\n   No properties collected - Check PDF format")

if __name__ == "__main__":
    try:
        test_data_manager()
        test_commitment_book_collector()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    finally:
        print("\nTest complete")
