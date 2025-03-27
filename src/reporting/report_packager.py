"""
Report Packager Module for Brunswick Lead System

This module handles batch generation and packaging of property reports,
allowing for efficient distribution of multiple reports to clients.
"""

import os
import sys
import shutil
import logging
import zipfile
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import concurrent.futures

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.reporting.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReportPackager")

class ReportPackager:
    """
    Package and distribute multiple property reports
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        template: str = "investor_report",
        branding: str = "midcoast_leads",
        logo_path: Optional[str] = None,
        brand_colors: Optional[Dict] = None,
        max_workers: int = 4
    ):
        """
        Initialize the Report Packager
        
        Args:
            output_dir: Directory for output files (default: project_root/reports)
            template: Report template to use
            branding: Branding template to use
            logo_path: Path to logo file
            brand_colors: Dictionary of brand colors
            max_workers: Maximum number of concurrent report generation workers
        """
        self.template = template
        self.branding = branding
        self.logo_path = logo_path
        self.brand_colors = brand_colors
        self.max_workers = max_workers
        
        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = project_root / 'reports' / f'batch_{timestamp}'
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory set to: {self.output_dir}")
        
        # Initialize the report generator
        self.report_generator = ReportGenerator(
            template=template,
            branding=branding
        )
        
        # Initialize batch metadata
        self.batch_metadata = {
            'batch_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'template': template,
            'branding': branding,
            'reports': []
        }
    
    def generate_batch(
        self,
        properties: List[Dict],
        metrics: Optional[Dict[str, Dict]] = None,
        comparables: Optional[Dict[str, List[Dict]]] = None,
        charts: Optional[Dict[str, Dict[str, str]]] = None,
        concurrent: bool = True
    ) -> str:
        """
        Generate a batch of reports for multiple properties
        
        Args:
            properties: List of property data dictionaries
            metrics: Dict of metrics keyed by property ID
            comparables: Dict of comparable properties keyed by property ID
            charts: Dict of chart paths keyed by property ID
            concurrent: Whether to generate reports concurrently
            
        Returns:
            Path to the generated batch package
        """
        logger.info(f"Generating batch of {len(properties)} reports")
        
        # Create a reports subdirectory
        reports_dir = self.output_dir / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Process each property
        report_paths = []
        
        if concurrent and len(properties) > 1:
            # Generate reports concurrently
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Prepare arguments for each report
                future_to_property = {}
                
                for property_data in properties:
                    property_id = self._get_property_id(property_data)
                    
                    # Get property-specific data
                    property_metrics = metrics.get(property_id, {}) if metrics else {}
                    property_comparables = comparables.get(property_id, []) if comparables else []
                    property_charts = charts.get(property_id, {}) if charts else {}
                    
                    # Set output file path
                    output_file = reports_dir / f"{property_id}_report.pdf"
                    
                    # Submit task
                    future = executor.submit(
                        self._generate_single_report,
                        property_data,
                        property_metrics,
                        property_comparables,
                        property_charts,
                        output_file
                    )
                    future_to_property[future] = property_id
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_property):
                    property_id = future_to_property[future]
                    try:
                        report_path = future.result()
                        report_paths.append(report_path)
                        
                        # Update metadata
                        self._add_report_to_metadata(property_id, report_path)
                        logger.info(f"Generated report for property {property_id}")
                    except Exception as e:
                        logger.error(f"Error generating report for property {property_id}: {e}")
        else:
            # Generate reports sequentially
            for property_data in properties:
                property_id = self._get_property_id(property_data)
                
                # Get property-specific data
                property_metrics = metrics.get(property_id, {}) if metrics else {}
                property_comparables = comparables.get(property_id, []) if comparables else []
                property_charts = charts.get(property_id, {}) if charts else {}
                
                # Set output file path
                output_file = reports_dir / f"{property_id}_report.pdf"
                
                try:
                    # Generate report
                    report_path = self._generate_single_report(
                        property_data,
                        property_metrics,
                        property_comparables,
                        property_charts,
                        output_file
                    )
                    report_paths.append(report_path)
                    
                    # Update metadata
                    self._add_report_to_metadata(property_id, report_path)
                    logger.info(f"Generated report for property {property_id}")
                except Exception as e:
                    logger.error(f"Error generating report for property {property_id}: {e}")
        
        # Save batch metadata
        metadata_path = self.output_dir / 'batch_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(self.batch_metadata, f, indent=2)
        
        # Create a zip package of all reports
        package_path = self._create_package(report_paths)
        
        return package_path
    
    def _generate_single_report(
        self,
        property_data: Dict,
        metrics: Dict,
        comparables: List[Dict],
        charts: Dict[str, str],
        output_file: Path
    ) -> str:
        """Generate a single property report"""
        return self.report_generator.generate_report(
            property_data=property_data,
            metrics=metrics,
            comparables=comparables,
            charts=charts,
            output_file=str(output_file)
        )
    
    def _create_package(self, report_paths: List[str]) -> str:
        """Create a zip package of all reports"""
        # Create a descriptive package name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        num_reports = len(report_paths)
        package_name = f"property_reports_{num_reports}_{timestamp}.zip"
        package_path = self.output_dir / package_name
        
        # Create the zip file
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add each report to the zip
            for report_path in report_paths:
                arcname = os.path.basename(report_path)
                zipf.write(report_path, arcname)
            
            # Add metadata
            metadata_path = self.output_dir / 'batch_metadata.json'
            if metadata_path.exists():
                zipf.write(metadata_path, 'batch_metadata.json')
        
        logger.info(f"Created package: {package_path}")
        return str(package_path)
    
    def _get_property_id(self, property_data: Dict) -> str:
        """Extract a unique identifier for the property"""
        # Try different possible ID fields
        for id_field in ['property_id', 'id', 'account_number', 'parcel_id']:
            if id_field in property_data and property_data[id_field]:
                return str(property_data[id_field])
        
        # If no ID found, use address as fallback
        address = property_data.get('location', '')
        if address:
            # Clean address for use in filename
            clean_address = address.replace(' ', '_').replace(',', '').replace('/', '_')
            if len(clean_address) > 50:
                clean_address = clean_address[:50]
            return clean_address
        
        # Last resort - use a UUID
        return str(uuid.uuid4())
    
    def _add_report_to_metadata(self, property_id: str, report_path: str) -> None:
        """Add a report to the batch metadata"""
        report_info = {
            'property_id': property_id,
            'file_path': os.path.basename(report_path),
            'generated_at': datetime.now().isoformat()
        }
        self.batch_metadata['reports'].append(report_info)

    def generate_index_html(self) -> str:
        """Generate an HTML index of all reports in the batch"""
        index_path = self.output_dir / 'index.html'
        
        # Basic HTML template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Report Batch {self.batch_metadata['batch_id']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        h1 {{
            margin: 0;
        }}
        .batch-info {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .download-btn {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 8px 15px;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }}
        .download-btn:hover {{
            background-color: #2980b9;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Property Report Batch</h1>
        <p>Generated on {datetime.fromisoformat(self.batch_metadata['timestamp']).strftime('%Y-%m-%d at %H:%M:%S')}</p>
    </header>
    
    <div class="batch-info">
        <p><strong>Batch ID:</strong> {self.batch_metadata['batch_id']}</p>
        <p><strong>Template:</strong> {self.batch_metadata['template']}</p>
        <p><strong>Branding:</strong> {self.batch_metadata['branding']}</p>
        <p><strong>Total Reports:</strong> {len(self.batch_metadata['reports'])}</p>
        <p><a href="property_reports_{len(self.batch_metadata['reports'])}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip" class="download-btn">Download All Reports (ZIP)</a></p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Property ID</th>
                <th>Generated At</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # Add rows for each report
        for i, report in enumerate(self.batch_metadata['reports'], 1):
            property_id = report['property_id']
            file_path = report['file_path']
            generated_at = datetime.fromisoformat(report['generated_at']).strftime('%Y-%m-%d %H:%M:%S')
            
            html_content += f"""
            <tr>
                <td>{i}</td>
                <td>{property_id}</td>
                <td>{generated_at}</td>
                <td><a href="reports/{file_path}" class="download-btn">View Report</a></td>
            </tr>"""
        
        # Close the HTML
        html_content += """
        </tbody>
    </table>
    
    <footer>
        <p>Midcoast Property Intelligence | Generated with ML-enhanced analytics</p>
    </footer>
</body>
</html>
"""
        
        # Write the HTML file
        with open(index_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML index at: {index_path}")
        return str(index_path)


def main():
    """Run the Report Packager as a standalone script"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Generate batch property reports')
    parser.add_argument('--properties-file', required=True, help='JSON file with list of properties')
    parser.add_argument('--metrics-file', help='JSON file with metrics for properties')
    parser.add_argument('--output-dir', help='Output directory for reports')
    parser.add_argument('--template', default='investor_report', help='Report template')
    parser.add_argument('--branding', default='midcoast_leads', help='Branding template')
    parser.add_argument('--logo', help='Path to logo file')
    parser.add_argument('--concurrent', action='store_true', help='Generate reports concurrently')
    args = parser.parse_args()
    
    # Load properties data
    with open(args.properties_file, 'r') as f:
        properties = json.load(f)
    
    # Load metrics data if available
    metrics = {}
    if args.metrics_file:
        with open(args.metrics_file, 'r') as f:
            metrics_data = json.load(f)
        
        # Convert to dict keyed by property ID
        for property_id, property_metrics in metrics_data.items():
            metrics[property_id] = property_metrics
    
    # Initialize packager
    packager = ReportPackager(
        output_dir=args.output_dir,
        template=args.template,
        branding=args.branding,
        logo_path=args.logo
    )
    
    # Generate batch of reports
    package_path = packager.generate_batch(
        properties=properties,
        metrics=metrics,
        concurrent=args.concurrent
    )
    
    # Generate HTML index
    index_path = packager.generate_index_html()
    
    print(f"Generated report package: {package_path}")
    print(f"HTML index: {index_path}")


if __name__ == "__main__":
    main()
