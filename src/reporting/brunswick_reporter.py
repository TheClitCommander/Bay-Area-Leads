"""
Advanced reporting and visualization for Brunswick data
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Union, Tuple
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pdfkit
import jinja2
import markdown2
from datetime import datetime
import json
import logging
from ..storage.brunswick_data_manager import BrunswickDataManager

class BrunswickReporter:
    def __init__(self, data_manager: BrunswickDataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.report_dir = Path("reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up plotting styles
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
        # Initialize Jinja2 environment
        self.template_dir = Path("templates")
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )
        
    def generate_business_report(
        self,
        time_period: str = "last_month",
        formats: List[str] = ["pdf", "html", "md"]
    ) -> Dict[str, str]:
        """Generate comprehensive business report"""
        # Gather data
        businesses = self.data_manager.search(
            query=self._get_time_filter(time_period),
            item_type="businesses"
        )
        
        # Create visualizations
        figures = self._create_business_visualizations(businesses)
        
        # Generate metrics
        metrics = self._calculate_business_metrics(businesses)
        
        # Create report context
        context = {
            "title": "Brunswick Business Report",
            "period": time_period,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "metrics": metrics,
            "figures": figures
        }
        
        # Generate reports in different formats
        return self._export_report(context, "business_report", formats)
        
    def generate_property_report(
        self,
        time_period: str = "last_month",
        formats: List[str] = ["pdf", "html", "md"]
    ) -> Dict[str, str]:
        """Generate property market report"""
        # Gather data
        properties = self.data_manager.search(
            query=self._get_time_filter(time_period),
            item_type="properties"
        )
        
        # Create visualizations
        figures = self._create_property_visualizations(properties)
        
        # Generate metrics
        metrics = self._calculate_property_metrics(properties)
        
        # Create report context
        context = {
            "title": "Brunswick Property Report",
            "period": time_period,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "metrics": metrics,
            "figures": figures
        }
        
        # Generate reports in different formats
        return self._export_report(context, "property_report", formats)
        
    def export_interactive_dashboard(
        self,
        data: List[Dict],
        filename: str
    ) -> str:
        """Create interactive Plotly dashboard"""
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create figure with subplots
        fig = go.Figure()
        
        # Add business categories distribution
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            fig.add_trace(
                go.Bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    name="Business Categories"
                )
            )
            
        # Add time series of new businesses
        if 'founding_date' in df.columns:
            df['founding_date'] = pd.to_datetime(df['founding_date'])
            monthly_counts = df.resample('M', on='founding_date').size()
            fig.add_trace(
                go.Scatter(
                    x=monthly_counts.index,
                    y=monthly_counts.values,
                    name="New Businesses"
                )
            )
            
        # Update layout
        fig.update_layout(
            title="Brunswick Business Dashboard",
            height=800,
            showlegend=True,
            template="plotly_white"
        )
        
        # Save to HTML
        dashboard_path = self.report_dir / f"{filename}.html"
        fig.write_html(str(dashboard_path))
        
        return str(dashboard_path)
        
    def export_geojson(self, data: List[Dict], filename: str) -> str:
        """Export data as GeoJSON for mapping"""
        features = []
        
        for item in data:
            if 'latitude' in item and 'longitude' in item:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(item['longitude']),
                            float(item['latitude'])
                        ]
                    },
                    "properties": {k: v for k, v in item.items()
                                 if k not in ['latitude', 'longitude']}
                }
                features.append(feature)
                
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        filepath = self.report_dir / f"{filename}.geojson"
        with open(filepath, 'w') as f:
            json.dump(geojson, f)
            
        return str(filepath)
        
    def export_kml(self, data: List[Dict], filename: str) -> str:
        """Export data as KML for Google Earth"""
        kml_template = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document>
            <name>Brunswick Data</name>
            {% for item in items %}
            <Placemark>
              <name>{{ item.name }}</name>
              <description>{{ item.description }}</description>
              <Point>
                <coordinates>{{ item.longitude }},{{ item.latitude }},0</coordinates>
              </Point>
            </Placemark>
            {% endfor %}
          </Document>
        </kml>
        """
        
        template = jinja2.Template(kml_template)
        kml_content = template.render(items=data)
        
        filepath = self.report_dir / f"{filename}.kml"
        with open(filepath, 'w') as f:
            f.write(kml_content)
            
        return str(filepath)
        
    def _create_business_visualizations(
        self,
        data: List[Dict]
    ) -> Dict[str, plt.Figure]:
        """Create business-related visualizations"""
        df = pd.DataFrame(data)
        figures = {}
        
        # Business categories distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        df['category'].value_counts().plot(kind='bar', ax=ax)
        ax.set_title('Business Categories Distribution')
        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        plt.xticks(rotation=45)
        figures['categories'] = fig
        
        # Business age distribution
        if 'founding_date' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            df['founding_date'] = pd.to_datetime(df['founding_date'])
            df['age'] = (datetime.now() - df['founding_date']).dt.days / 365.25
            sns.histplot(data=df, x='age', bins=20, ax=ax)
            ax.set_title('Business Age Distribution')
            ax.set_xlabel('Age (years)')
            figures['age_dist'] = fig
            
        # Geographic distribution
        if all(col in df.columns for col in ['latitude', 'longitude']):
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.scatter(df['longitude'], df['latitude'], alpha=0.5)
            ax.set_title('Business Locations')
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            figures['locations'] = fig
            
        return figures
        
    def _create_property_visualizations(
        self,
        data: List[Dict]
    ) -> Dict[str, plt.Figure]:
        """Create property-related visualizations"""
        df = pd.DataFrame(data)
        figures = {}
        
        # Assessment value distribution
        if 'assessment' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(data=df, x='assessment', bins=20, ax=ax)
            ax.set_title('Property Assessment Distribution')
            ax.set_xlabel('Assessment Value ($)')
            figures['assessments'] = fig
            
        # Zoning distribution
        if 'zoning' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            df['zoning'].value_counts().plot(kind='bar', ax=ax)
            ax.set_title('Property Zoning Distribution')
            ax.set_xlabel('Zoning Type')
            ax.set_ylabel('Count')
            plt.xticks(rotation=45)
            figures['zoning'] = fig
            
        return figures
        
    def _calculate_business_metrics(self, data: List[Dict]) -> Dict:
        """Calculate business-related metrics"""
        df = pd.DataFrame(data)
        metrics = {
            "total_businesses": len(df),
            "categories": df['category'].value_counts().to_dict(),
            "avg_age": None,
            "new_businesses_30d": None
        }
        
        if 'founding_date' in df.columns:
            df['founding_date'] = pd.to_datetime(df['founding_date'])
            metrics.update({
                "avg_age": (
                    datetime.now() - df['founding_date']
                ).dt.days.mean() / 365.25,
                "new_businesses_30d": len(
                    df[
                        df['founding_date'] > datetime.now() - timedelta(days=30)
                    ]
                )
            })
            
        return metrics
        
    def _calculate_property_metrics(self, data: List[Dict]) -> Dict:
        """Calculate property-related metrics"""
        df = pd.DataFrame(data)
        metrics = {
            "total_properties": len(df),
            "zoning_distribution": None,
            "avg_assessment": None,
            "recent_transfers": None
        }
        
        if 'zoning' in df.columns:
            metrics["zoning_distribution"] = (
                df['zoning'].value_counts().to_dict()
            )
            
        if 'assessment' in df.columns:
            metrics["avg_assessment"] = df['assessment'].mean()
            
        if 'transfer_date' in df.columns:
            df['transfer_date'] = pd.to_datetime(df['transfer_date'])
            metrics["recent_transfers"] = len(
                df[df['transfer_date'] > datetime.now() - timedelta(days=30)]
            )
            
        return metrics
        
    def _export_report(
        self,
        context: Dict,
        base_filename: str,
        formats: List[str]
    ) -> Dict[str, str]:
        """Export report in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}"
        outputs = {}
        
        for fmt in formats:
            if fmt == "pdf":
                outputs["pdf"] = self._export_pdf(context, filename)
            elif fmt == "html":
                outputs["html"] = self._export_html(context, filename)
            elif fmt == "md":
                outputs["md"] = self._export_markdown(context, filename)
                
        return outputs
        
    def _export_pdf(self, context: Dict, filename: str) -> str:
        """Export report as PDF"""
        # First generate HTML
        html_content = self._render_template("report.html", context)
        
        # Convert HTML to PDF
        pdf_path = self.report_dir / f"{filename}.pdf"
        pdfkit.from_string(html_content, str(pdf_path))
        
        return str(pdf_path)
        
    def _export_html(self, context: Dict, filename: str) -> str:
        """Export report as HTML"""
        html_content = self._render_template("report.html", context)
        html_path = self.report_dir / f"{filename}.html"
        
        with open(html_path, 'w') as f:
            f.write(html_content)
            
        return str(html_path)
        
    def _export_markdown(self, context: Dict, filename: str) -> str:
        """Export report as Markdown"""
        md_content = self._render_template("report.md", context)
        md_path = self.report_dir / f"{filename}.md"
        
        with open(md_path, 'w') as f:
            f.write(md_content)
            
        return str(md_path)
        
    def _render_template(self, template_name: str, context: Dict) -> str:
        """Render Jinja2 template"""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
        
    def _get_time_filter(self, time_period: str) -> Dict:
        """Convert time period to query filter"""
        now = datetime.now()
        
        if time_period == "last_month":
            start_date = now - timedelta(days=30)
        elif time_period == "last_quarter":
            start_date = now - timedelta(days=90)
        elif time_period == "last_year":
            start_date = now - timedelta(days=365)
        else:
            raise ValueError(f"Unsupported time period: {time_period}")
            
        return {
            "last_updated": {
                "gte": start_date.isoformat()
            }
        }
