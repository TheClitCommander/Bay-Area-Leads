"""
Generate sample reports using test data
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.reporting.brunswick_enhanced_reporter import BrunswickEnhancedReporter
from src.storage.brunswick_data_manager import BrunswickDataManager
from src.storage.brunswick_data_store import BrunswickDataStore
from tests.sample_data import TEST_DATA

class SampleReportGenerator:
    def __init__(self):
        # Initialize data store with a persistent database
        db_path = project_root / "data" / "brunswick.db"
        db_path.parent.mkdir(exist_ok=True)
        store = BrunswickDataStore(db_path=str(db_path))
        self.data_manager = BrunswickDataManager(store=store)
        self.reporter = BrunswickEnhancedReporter(self.data_manager)
        self.report_dir = project_root / "reports"
        self.report_dir.mkdir(exist_ok=True)
        
        # Load sample data
        self._load_sample_data()
        
    def _load_sample_data(self):
        """Load sample data into data manager"""
        # Drop existing tables
        with self.data_manager.store.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS licenses")
            cursor.execute("DROP TABLE IF EXISTS businesses")
            cursor.execute("DROP TABLE IF EXISTS properties")
            conn.commit()
            
        # Initialize tables
        self.data_manager.store.initialize_tables()
        
        # Insert test data
        for business in TEST_DATA['businesses']:
            self.data_manager.store.insert('businesses', business)
            
        for property in TEST_DATA['properties']:
            self.data_manager.store.insert('properties', property)
            
        for license in TEST_DATA['licenses']:
            self.data_manager.store.insert('licenses', license)
        
    def generate_all_reports(self):
        """Generate all sample reports"""
        self.generate_market_analysis()
        self.generate_trend_report()
        self.generate_business_report()
        self.generate_property_report()
        self.generate_development_report()
        
    def generate_market_analysis(self):
        """Generate market analysis report"""
        print("Generating market analysis report...")
        
        # Get market analysis
        analysis = self.reporter.generate_market_analysis(period="last_month")
        
        # Create report directory
        report_path = self.report_dir / "market_analysis"
        report_path.mkdir(exist_ok=True)
        
        # Save report data
        with open(report_path / "market_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
            
        # Generate visualizations
        self._create_market_visualizations(analysis, report_path)
        
        print(f"Market analysis report saved to {report_path}")
        
    def generate_trend_report(self):
        """Generate trend analysis report"""
        print("Generating trend report...")
        
        # Get trend analysis
        trends = self.reporter.generate_trend_report(periods=12)
        
        # Create report directory
        report_path = self.report_dir / "trends"
        report_path.mkdir(exist_ok=True)
        
        # Save report data
        with open(report_path / "trend_analysis.json", "w") as f:
            json.dump(trends, f, indent=2)
            
        # Generate visualizations
        self._create_trend_visualizations(trends, report_path)
        
        print(f"Trend report saved to {report_path}")
        
    def generate_business_report(self):
        """Generate business-focused report"""
        print("Generating business report...")
        
        # Create business metrics
        metrics = {
            'total_businesses': len(TEST_DATA['businesses']),
            'license_status': {
                'active': sum(1 for b in TEST_DATA['businesses'] if b['license_status'] == 'ACTIVE'),
                'other': sum(1 for b in TEST_DATA['businesses'] if b['license_status'] != 'ACTIVE')
            },
            'business_types': {},
            'neighborhood_distribution': {}
        }
        
        # Calculate distributions
        for business in TEST_DATA['businesses']:
            # Business types
            btype = business['type']
            metrics['business_types'][btype] = metrics['business_types'].get(btype, 0) + 1
            
            # Neighborhood distribution
            hood = business['neighborhood']
            metrics['neighborhood_distribution'][hood] = metrics['neighborhood_distribution'].get(hood, 0) + 1
            
        # Create report directory
        report_path = self.report_dir / "business"
        report_path.mkdir(exist_ok=True)
        
        # Save metrics
        with open(report_path / "business_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        # Generate visualizations
        self._create_business_visualizations(metrics, report_path)
        
        print(f"Business report saved to {report_path}")
        
    def generate_property_report(self):
        """Generate property-focused report"""
        print("Generating property report...")
        
        # Create property metrics
        metrics = {
            'total_properties': len(TEST_DATA['properties']),
            'average_assessment': sum(p['assessment'] for p in TEST_DATA['properties']) / len(TEST_DATA['properties']),
            'zoning_distribution': {},
            'property_types': {},
            'permit_types': {}
        }
        
        # Calculate distributions
        for property in TEST_DATA['properties']:
            # Zoning distribution
            zone = property['zoning']
            metrics['zoning_distribution'][zone] = metrics['zoning_distribution'].get(zone, 0) + 1
            
            # Property types
            ptype = property['type']
            metrics['property_types'][ptype] = metrics['property_types'].get(ptype, 0) + 1
            
            # Permit types
            permit = property['permit_type']
            metrics['permit_types'][permit] = metrics['permit_types'].get(permit, 0) + 1
            
        # Create report directory
        report_path = self.report_dir / "property"
        report_path.mkdir(exist_ok=True)
        
        # Save metrics
        with open(report_path / "property_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        # Generate visualizations
        self._create_property_visualizations(metrics, report_path)
        
        print(f"Property report saved to {report_path}")
        
    def generate_development_report(self):
        """Generate development activity report"""
        print("Generating development report...")
        
        # Create development metrics
        metrics = {
            'total_permits': len(TEST_DATA['properties']),
            'total_value': sum(p['permit_value'] for p in TEST_DATA['properties']),
            'permit_types': {},
            'neighborhood_activity': {}
        }
        
        # Calculate distributions
        for property in TEST_DATA['properties']:
            # Permit types
            ptype = property['permit_type']
            if ptype not in metrics['permit_types']:
                metrics['permit_types'][ptype] = {
                    'count': 0,
                    'value': 0
                }
            metrics['permit_types'][ptype]['count'] += 1
            metrics['permit_types'][ptype]['value'] += property['permit_value']
            
            # Neighborhood activity
            hood = property['neighborhood']
            if hood not in metrics['neighborhood_activity']:
                metrics['neighborhood_activity'][hood] = {
                    'permits': 0,
                    'value': 0
                }
            metrics['neighborhood_activity'][hood]['permits'] += 1
            metrics['neighborhood_activity'][hood]['value'] += property['permit_value']
            
        # Create report directory
        report_path = self.report_dir / "development"
        report_path.mkdir(exist_ok=True)
        
        # Save metrics
        with open(report_path / "development_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        # Generate visualizations
        self._create_development_visualizations(metrics, report_path)
        
        print(f"Development report saved to {report_path}")
        
    def _create_market_visualizations(self, analysis, path):
        """Create visualizations for market analysis"""
        # Business type distribution
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(analysis['business_metrics']['business_types'].keys()),
                   y=list(analysis['business_metrics']['business_types'].values()))
        plt.title('Business Type Distribution')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path / "business_types.png")
        plt.close()
        
        # Property value distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(data=[p['assessment'] for p in TEST_DATA['properties']], bins=10)
        plt.title('Property Value Distribution')
        plt.xlabel('Assessment Value')
        plt.tight_layout()
        plt.savefig(path / "property_values.png")
        plt.close()
        
    def _create_trend_visualizations(self, trends, path):
        """Create visualizations for trend analysis"""
        # Business growth trend
        plt.figure(figsize=(12, 6))
        plt.plot(['Month {}'.format(i+1) for i in range(12)], 
                [trends['market_indicators']['business_growth']] * 12)
        plt.title('Business Growth Trend')
        plt.xlabel('Period')
        plt.ylabel('Total Businesses')
        plt.tight_layout()
        plt.savefig(path / "business_growth.png")
        plt.close()
        
        # Property value trend
        plt.figure(figsize=(12, 6))
        plt.plot(['Month {}'.format(i+1) for i in range(12)], 
                [trends['market_indicators']['property_value']] * 12)
        plt.title('Property Value Trend')
        plt.xlabel('Period')
        plt.ylabel('Total Property Value')
        plt.tight_layout()
        plt.savefig(path / "property_values.png")
        plt.close()
        
    def _create_business_visualizations(self, metrics, path):
        """Create visualizations for business report"""
        # Business type distribution
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(metrics['business_types'].keys()),
                   y=list(metrics['business_types'].values()))
        plt.title('Business Types')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path / "business_types.png")
        plt.close()
        
        # License status
        plt.figure(figsize=(8, 8))
        plt.pie(metrics['license_status'].values(),
                labels=metrics['license_status'].keys(),
                autopct='%1.1f%%')
        plt.title('License Status Distribution')
        plt.tight_layout()
        plt.savefig(path / "license_status.png")
        plt.close()
        
    def _create_property_visualizations(self, metrics, path):
        """Create visualizations for property report"""
        # Zoning distribution
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(metrics['zoning_distribution'].keys()),
                   y=list(metrics['zoning_distribution'].values()))
        plt.title('Zoning Distribution')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path / "zoning_distribution.png")
        plt.close()
        
        # Property types
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(metrics['property_types'].keys()),
                   y=list(metrics['property_types'].values()))
        plt.title('Property Types')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path / "property_types.png")
        plt.close()
        
    def _create_development_visualizations(self, metrics, path):
        """Create visualizations for development report"""
        # Permit type distribution
        plt.figure(figsize=(10, 6))
        permit_types = metrics['permit_types']
        sns.barplot(x=list(permit_types.keys()),
                   y=[p['count'] for p in permit_types.values()])
        plt.title('Permit Type Distribution')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(path / "permit_types.png")
        plt.close()
        
        # Permit values by type
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(permit_types.keys()),
                   y=[p['value'] for p in permit_types.values()])
        plt.title('Permit Values by Type')
        plt.xticks(rotation=45)
        plt.ylabel('Total Value')
        plt.tight_layout()
        plt.savefig(path / "permit_values.png")
        plt.close()

if __name__ == "__main__":
    generator = SampleReportGenerator()
    generator.generate_all_reports()
