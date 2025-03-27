"""
Lead Pipeline Integrator

This module integrates scraped leads from various sources into the main
Midcoast Leads scoring pipeline and reporting system.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import scraper modules
from src.scrapers.fsbo_scraper import FSBOScraper
# Uncommment when implemented:
# from src.scrapers.preforeclosure_scraper import PreForeclosureScraper

# Import analyzer modules
from src.analyzers.lead_scoring_analyzer import LeadScoringAnalyzer
from src.utils.lead_prioritization import prioritize_leads

# Import reporting
from src.reporting.report_generator import ReportGenerator
from src.reporting.report_packager import ReportPackager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LeadPipelineIntegrator")


class LeadPipelineIntegrator:
    """
    Integrates scraped leads into the main Midcoast Leads pipeline
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        data_dir: Optional[str] = None
    ):
        """
        Initialize the Lead Pipeline Integrator
        
        Args:
            config_path: Path to configuration file
            output_dir: Directory for output files
            data_dir: Directory for data files
        """
        self.logger = logging.getLogger("LeadPipelineIntegrator")
        
        # Set up directories
        self.project_root = project_root
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = project_root / 'data' / 'pipeline_output'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = project_root / 'data'
        
        # Load configuration
        self.config_path = config_path or project_root / 'config' / 'lead_scoring_config.json'
        self.load_config()
        
        # Initialize components
        self.initialize_components()
        
        self.logger.info("Initialized Lead Pipeline Integrator")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
            self.config = {
                "scraping": {
                    "fsbo": {
                        "enabled": True,
                        "sources": ["craigslist"],
                        "search_radius": 25,
                        "max_listings": 100
                    },
                    "preforeclosure": {
                        "enabled": False,
                        "sources": ["court_records"],
                        "counties": ["Cumberland", "Sagadahoc"]
                    }
                },
                "analysis": {
                    "ml_score_threshold": 0.6,
                    "prioritize_by": ["ml_score", "urgency", "price"]
                },
                "reporting": {
                    "generate_reports": True,
                    "batch_size": 10,
                    "logo_path": None
                }
            }
    
    def initialize_components(self):
        """Initialize pipeline components"""
        # Initialize scrapers
        self.fsbo_scraper = None
        self.preforeclosure_scraper = None
        
        fsbo_config = self.config.get("scraping", {}).get("fsbo", {})
        if fsbo_config.get("enabled", True):
            self.fsbo_scraper = FSBOScraper(
                output_dir=str(self.output_dir / 'fsbo'),
                use_craigslist="craigslist" in fsbo_config.get("sources", ["craigslist"]),
                use_facebook="facebook" in fsbo_config.get("sources", []),
                config=fsbo_config
            )
        
        # Initialize analyzer
        self.analyzer = LeadScoringAnalyzer()
        
        # Initialize report generator (if needed)
        self.report_generator = None
        self.report_packager = None
        
        if self.config.get("reporting", {}).get("generate_reports", True):
            self.report_generator = ReportGenerator()
            self.report_packager = ReportPackager(
                output_dir=str(self.output_dir / 'reports'),
                logo_path=self.config.get("reporting", {}).get("logo_path")
            )
    
    def run_pipeline(
        self,
        run_fsbo: bool = True,
        run_preforeclosure: bool = False,
        run_analysis: bool = True,
        run_reporting: bool = True,
        lead_files: Optional[List[str]] = None
    ) -> Dict:
        """
        Run the complete lead pipeline
        
        Args:
            run_fsbo: Whether to run FSBO scraper
            run_preforeclosure: Whether to run pre-foreclosure scraper
            run_analysis: Whether to run analysis
            run_reporting: Whether to generate reports
            lead_files: Optional list of lead files to process instead of scraping
            
        Returns:
            Dictionary of pipeline results
        """
        self.logger.info("Starting lead pipeline")
        
        pipeline_results = {
            "leads": {
                "fsbo": [],
                "preforeclosure": [],
                "total": 0
            },
            "analysis": {
                "scored_leads": [],
                "high_potential_leads": []
            },
            "reporting": {
                "reports_generated": 0,
                "package_path": None
            }
        }
        
        # Step 1: Scrape leads
        all_leads = []
        
        if lead_files:
            # Load leads from files instead of scraping
            for file_path in lead_files:
                try:
                    with open(file_path, 'r') as f:
                        leads = json.load(f)
                        if isinstance(leads, list):
                            all_leads.extend(leads)
                            self.logger.info(f"Loaded {len(leads)} leads from {file_path}")
                        else:
                            self.logger.warning(f"Skipping {file_path}: not a list of leads")
                except Exception as e:
                    self.logger.error(f"Error loading leads from {file_path}: {e}")
        else:
            # Run scrapers
            if run_fsbo and self.fsbo_scraper:
                fsbo_leads = self.fsbo_scraper.run()
                
                # Flatten the dictionary of leads by source
                for source_leads in fsbo_leads.values():
                    all_leads.extend(source_leads)
                    pipeline_results["leads"]["fsbo"].extend(source_leads)
                
                self.logger.info(f"Collected {len(pipeline_results['leads']['fsbo'])} FSBO leads")
            
            if run_preforeclosure and self.preforeclosure_scraper:
                # When implemented
                pass
        
        pipeline_results["leads"]["total"] = len(all_leads)
        
        if not all_leads:
            self.logger.warning("No leads collected. Pipeline stopping.")
            return pipeline_results
        
        # Save all leads to a single file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        all_leads_path = self.output_dir / f"all_leads_{timestamp}.json"
        
        try:
            with open(all_leads_path, 'w') as f:
                json.dump(all_leads, f, indent=2)
            self.logger.info(f"Saved {len(all_leads)} leads to {all_leads_path}")
        except Exception as e:
            self.logger.error(f"Error saving all leads: {e}")
        
        # Step 2: Analyze leads
        scored_leads = []
        
        if run_analysis and all_leads:
            self.logger.info(f"Analyzing {len(all_leads)} leads")
            
            try:
                # Convert to format expected by analyzer
                analyzer_input = self._prepare_leads_for_analysis(all_leads)
                
                # Run analysis
                analysis_results = self.analyzer.analyze_leads(analyzer_input)
                
                # Process results
                scored_leads = self._process_analysis_results(all_leads, analysis_results)
                
                # Save scored leads
                scored_leads_path = self.output_dir / f"scored_leads_{timestamp}.json"
                with open(scored_leads_path, 'w') as f:
                    json.dump(scored_leads, f, indent=2)
                
                # Get high potential leads
                ml_threshold = self.config.get("analysis", {}).get("ml_score_threshold", 0.6)
                high_potential_leads = [
                    lead for lead in scored_leads 
                    if lead.get("ml_score", 0) >= ml_threshold
                ]
                
                # Prioritize leads
                prioritize_by = self.config.get("analysis", {}).get("prioritize_by", ["ml_score"])
                prioritized_leads = prioritize_leads(high_potential_leads, prioritize_by)
                
                pipeline_results["analysis"]["scored_leads"] = scored_leads
                pipeline_results["analysis"]["high_potential_leads"] = prioritized_leads
                
                self.logger.info(f"Analyzed {len(scored_leads)} leads, found {len(high_potential_leads)} high potential leads")
            
            except Exception as e:
                self.logger.error(f"Error in lead analysis: {e}")
                # Continue with unscored leads
                scored_leads = all_leads
        
        # Step 3: Generate reports
        if run_reporting and self.report_generator and self.report_packager:
            batch_size = self.config.get("reporting", {}).get("batch_size", 10)
            
            # Use high potential leads if available, otherwise use all leads
            leads_for_reports = (
                pipeline_results["analysis"]["high_potential_leads"] 
                if pipeline_results["analysis"]["high_potential_leads"] 
                else scored_leads
            )
            
            # Limit to batch size
            leads_for_reports = leads_for_reports[:batch_size]
            
            if leads_for_reports:
                self.logger.info(f"Generating reports for {len(leads_for_reports)} leads")
                
                try:
                    # Prepare data for reports
                    properties_data, metrics_data, comparables_data = self._prepare_data_for_reports(leads_for_reports)
                    
                    # Generate batch of reports
                    package_path = self.report_packager.generate_batch(
                        properties=properties_data,
                        metrics=metrics_data,
                        comparables=comparables_data
                    )
                    
                    # Generate HTML index
                    index_path = self.report_packager.generate_index_html()
                    
                    pipeline_results["reporting"]["reports_generated"] = len(leads_for_reports)
                    pipeline_results["reporting"]["package_path"] = package_path
                    pipeline_results["reporting"]["index_path"] = index_path
                    
                    self.logger.info(f"Generated {len(leads_for_reports)} reports, package at {package_path}")
                
                except Exception as e:
                    self.logger.error(f"Error generating reports: {e}")
        
        self.logger.info("Lead pipeline complete")
        return pipeline_results
    
    def _prepare_leads_for_analysis(self, leads: List[Dict]) -> List[Dict]:
        """
        Prepare leads for analysis by converting to the format expected by the analyzer
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of formatted lead dictionaries
        """
        formatted_leads = []
        
        for lead in leads:
            # Create basic property data dictionary
            property_data = {
                "property_id": lead.get("source_id", ""),
                "location": lead.get("address", ""),
                "city": lead.get("city", ""),
                "state": lead.get("state", "ME"),
                "zip_code": lead.get("zip_code", ""),
                "property_type": lead.get("property_type", "residential"),
                "year_built": lead.get("year_built"),
                "bedrooms": lead.get("bedrooms"),
                "bathrooms": lead.get("bathrooms"),
                "square_feet": lead.get("square_feet"),
                "lot_size": lead.get("lot_size"),
                "last_sale_price": lead.get("price"),
                "last_sale_date": lead.get("listing_date"),
                "description": lead.get("description", ""),
                "source": lead.get("source", "scraper"),
                "urgency": lead.get("urgency", 0)
            }
            
            # Add coordinates if available
            raw_data = lead.get("raw_data", {})
            coords = raw_data.get("coordinates", {})
            if coords and coords.get("latitude") and coords.get("longitude"):
                property_data["latitude"] = coords["latitude"]
                property_data["longitude"] = coords["longitude"]
            
            formatted_leads.append(property_data)
        
        return formatted_leads
    
    def _process_analysis_results(
        self, 
        original_leads: List[Dict], 
        analysis_results: Dict
    ) -> List[Dict]:
        """
        Process analysis results and merge with original lead data
        
        Args:
            original_leads: Original lead dictionaries
            analysis_results: Analysis results from the analyzer
            
        Returns:
            List of lead dictionaries with analysis results
        """
        # Create a mapping of property_id to original lead
        lead_map = {lead.get("source_id", ""): lead for lead in original_leads}
        
        # Get scored leads
        scored_leads = []
        
        for prop_id, metrics in analysis_results.get("property_metrics", {}).items():
            # Find the original lead
            original_lead = lead_map.get(prop_id)
            if not original_lead:
                continue
            
            # Create a copy of the original lead
            scored_lead = dict(original_lead)
            
            # Add analysis metrics
            scored_lead["ml_score"] = metrics.get("ml_score", 0)
            scored_lead["investment_signals"] = metrics.get("investment_signals", [])
            scored_lead["estimated_value"] = metrics.get("estimated_value")
            scored_lead["estimated_roi"] = metrics.get("estimated_roi")
            scored_lead["development_potential"] = metrics.get("development_potential", False)
            
            # Calculate a combined score (ML score + urgency)
            urgency = scored_lead.get("urgency", 0)
            ml_score = scored_lead.get("ml_score", 0)
            scored_lead["combined_score"] = (ml_score * 0.7) + (urgency / 10.0 * 0.3)
            
            scored_leads.append(scored_lead)
        
        return scored_leads
    
    def _prepare_data_for_reports(
        self, 
        leads: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, Dict], Dict[str, List[Dict]]]:
        """
        Prepare data for the report generator
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            Tuple of (properties_data, metrics_data, comparables_data)
        """
        properties_data = []
        metrics_data = {}
        comparables_data = {}
        
        for lead in leads:
            # Extract property ID
            property_id = lead.get("source_id", "")
            
            # Create property data
            property_data = {
                "property_id": property_id,
                "location": lead.get("address", ""),
                "city": lead.get("city", ""),
                "state": lead.get("state", "ME"),
                "zip_code": lead.get("zip_code", ""),
                "property_type": lead.get("property_type", "residential"),
                "year_built": lead.get("year_built"),
                "bedrooms": lead.get("bedrooms"),
                "bathrooms": lead.get("bathrooms"),
                "square_feet": lead.get("square_feet"),
                "lot_size": lead.get("lot_size"),
                "price": lead.get("price"),
                "image_urls": lead.get("images", []),
                "description": lead.get("description", "")
            }
            
            # Add coordinates if available
            raw_data = lead.get("raw_data", {})
            coords = raw_data.get("coordinates", {})
            if coords and coords.get("latitude") and coords.get("longitude"):
                property_data["latitude"] = coords.get("latitude")
                property_data["longitude"] = coords.get("longitude")
            
            properties_data.append(property_data)
            
            # Create metrics data
            metrics_data[property_id] = {
                "ml_score": lead.get("ml_score", 0),
                "investment_signals": lead.get("investment_signals", []),
                "estimated_value": lead.get("estimated_value"),
                "estimated_roi": lead.get("estimated_roi"),
                "development_potential": lead.get("development_potential", False),
                "urgency": lead.get("urgency", 0),
                "listing_date": lead.get("listing_date")
            }
            
            # TODO: Add comparable properties (would come from the analyzer)
            comparables_data[property_id] = []
        
        return properties_data, metrics_data, comparables_data


def main():
    """Run the Lead Pipeline Integrator as a standalone script"""
    parser = argparse.ArgumentParser(description='Integrate scraped leads into the Midcoast Leads pipeline')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output-dir', help='Directory for output files')
    parser.add_argument('--data-dir', help='Directory for data files')
    parser.add_argument('--lead-files', nargs='+', help='Paths to lead files to process instead of scraping')
    parser.add_argument('--skip-fsbo', action='store_true', help='Skip FSBO scraper')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip lead analysis')
    parser.add_argument('--skip-reporting', action='store_true', help='Skip report generation')
    args = parser.parse_args()
    
    # Initialize the pipeline integrator
    integrator = LeadPipelineIntegrator(
        config_path=args.config,
        output_dir=args.output_dir,
        data_dir=args.data_dir
    )
    
    # Run the pipeline
    results = integrator.run_pipeline(
        run_fsbo=not args.skip_fsbo,
        run_preforeclosure=False,  # Not implemented yet
        run_analysis=not args.skip_analysis,
        run_reporting=not args.skip_reporting,
        lead_files=args.lead_files
    )
    
    # Print summary
    print("\nPipeline Results Summary:")
    print(f"Total leads: {results['leads']['total']}")
    print(f"FSBO leads: {len(results['leads']['fsbo'])}")
    print(f"Pre-foreclosure leads: {len(results['leads']['preforeclosure'])}")
    print(f"High potential leads: {len(results['analysis']['high_potential_leads'])}")
    print(f"Reports generated: {results['reporting']['reports_generated']}")
    
    if results['reporting']['package_path']:
        print(f"Report package: {results['reporting']['package_path']}")
    
    if results['reporting']['index_path']:
        print(f"Report index: {results['reporting']['index_path']}")


if __name__ == "__main__":
    main()
