"""
Quality reporting utilities for property data extraction
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class QualityReporter:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, quality_metrics: Dict, timestamp: str = None) -> str:
        """Generate a comprehensive quality report"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Create report directory
        report_dir = self.output_dir / timestamp
        report_dir.mkdir(exist_ok=True)
        
        # Generate metrics file
        metrics_file = report_dir / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(quality_metrics, f, indent=2)
            
        # Generate CSV reports
        self._generate_csv_reports(quality_metrics, report_dir)
        
        # Generate visualizations
        self._generate_visualizations(quality_metrics, report_dir)
        
        # Generate summary report
        summary = self._generate_summary(quality_metrics)
        summary_file = report_dir / "summary.txt"
        with open(summary_file, "w") as f:
            f.write(summary)
            
        return str(report_dir)
        
    def _generate_csv_reports(self, metrics: Dict, report_dir: Path):
        """Generate detailed CSV reports"""
        # Validation issues
        validation_df = pd.DataFrame([{
            'issue_type': k,
            'count': v
        } for k, v in metrics['validation_issues'].items()])
        validation_df.to_csv(report_dir / "validation_issues.csv", index=False)
        
        # Extraction success
        extraction_df = pd.DataFrame([{
            'component': k,
            'success_count': v
        } for k, v in metrics['extraction_success'].items()])
        extraction_df.to_csv(report_dir / "extraction_success.csv", index=False)
        
    def _generate_visualizations(self, metrics: Dict, report_dir: Path):
        """Generate visualization plots"""
        # Validation issues pie chart
        plt.figure(figsize=(10, 6))
        plt.pie(
            metrics['validation_issues'].values(),
            labels=metrics['validation_issues'].keys(),
            autopct='%1.1f%%'
        )
        plt.title("Validation Issues Distribution")
        plt.savefig(report_dir / "validation_issues_pie.png")
        plt.close()
        
        # Extraction success bar chart
        plt.figure(figsize=(10, 6))
        components = list(metrics['extraction_success'].keys())
        success_counts = list(metrics['extraction_success'].values())
        plt.bar(components, success_counts)
        plt.title("Extraction Success by Component")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(report_dir / "extraction_success_bar.png")
        plt.close()
        
    def _generate_summary(self, metrics: Dict) -> str:
        """Generate text summary of quality metrics"""
        total_props = metrics['total_properties']
        total_issues = sum(metrics['validation_issues'].values())
        
        summary = [
            "Property Data Quality Report",
            "=" * 30,
            f"\nOverall Statistics:",
            f"Total Properties Processed: {total_props}",
            f"Properties with Errors: {metrics['properties_with_errors']}",
            f"Properties with Warnings: {metrics['properties_with_warnings']}",
            f"Total Validation Issues: {total_issues}",
            
            "\nExtraction Success Rates:",
        ]
        
        for component, count in metrics['extraction_success'].items():
            rate = (count / total_props * 100) if total_props > 0 else 0
            summary.append(f"{component}: {rate:.1f}% ({count}/{total_props})")
            
        summary.extend([
            "\nValidation Issues Breakdown:",
        ])
        
        for issue, count in metrics['validation_issues'].items():
            rate = (count / total_props * 100) if total_props > 0 else 0
            summary.append(f"{issue}: {count} ({rate:.1f}%)")
            
        return "\n".join(summary)
