"""
Test script for VGSI collector
"""
"""Test script for VGSI collector"""
import logging
import sys
import traceback
from src.collectors.vgsi_collector import VGSICollector

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_vgsi_collector():
    """Test VGSI collector with a small sample"""
    collector = None
    try:
        print("\n=== Starting VGSI Collector Test ===")
        print("1. Initializing collector...")
        collector = VGSICollector()
        
        print("\n2. Testing browser setup...")
        collector.driver.get(collector.base_url)
        print("   ✓ Browser initialized successfully")
        
        print("\n3. Collecting sample properties (max: 2)...")
        data = collector.collect(max_properties=2)
        
        print("\n4. Collection Results:")
        total = data['metadata']['total_collected']
        print(f"   Total properties collected: {total}")
        
        if data['properties']:
            print("\n5. Sample Property Data:")
            for i, prop in enumerate(data['properties'], 1):
                print(f"\n   Property {i}:")
                for key, value in prop.items():
                    print(f"   {key}: {value}")
        else:
            print("\n   No properties collected - Check for website changes or blocking")
            
    except Exception as e:
        print("\n=== Error in VGSI Collector Test ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        
    finally:
        if collector:
            print("\n6. Cleaning up resources...")
            collector.cleanup()
            print("   ✓ Resources cleaned up")

if __name__ == "__main__":
    try:
        test_vgsi_collector()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
