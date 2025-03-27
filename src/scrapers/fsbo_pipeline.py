"""
FSBO Lead Pipeline Integrator

This module integrates multiple FSBO scrapers (Craigslist, Facebook) and
processes the leads through the scoring and reporting pipeline.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import scrapers
from src.scrapers.scraper_base import ScraperBase
from src.scrapers.fsbo_scraper import CraigslistScraper
from src.scrapers.facebook_marketplace_scraper import FacebookMarketplaceScraper
from src.scrapers.preforeclosure_scraper import PreForeclosureScraper
from src.scrapers.lead_pipeline_integrator import LeadPipelineIntegrator

# Import utilities
from src.utils.property_enrichment import PropertyEnricher
from src.utils.fsbo_filters import FSBOFilterer
from src.utils.lead_exporter import LeadExporter
from src.utils.lead_management import LeadManager
from src.utils.lead_alerts import LeadAlertSystem
from src.utils.pdf_date_extractor import PdfDateExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LeadGenerationPipeline")


class LeadGenerationPipeline:
    """
    Integrates multiple lead source scrapers and processes leads through the pipeline
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        facebook_credentials_file: Optional[str] = None,
        facebook_headless: bool = True,
        county: str = "Cumberland",
        state: str = "ME"
    ):
        """
        Initialize the Lead Generation Pipeline
        
        Args:
            output_dir: Directory for output files
            facebook_credentials_file: Path to Facebook credentials file
            facebook_headless: Whether to run Facebook scraper in headless mode
            county: County to search for pre-foreclosures
            state: State to search for pre-foreclosures
        """
        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = project_root / 'data' / 'leads' / 'fsbo'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize scrapers
        self.craigslist_scraper = CraigslistScraper(
            cache_dir=str(project_root / 'data' / 'cache' / 'craigslist')
        )
        
        self.facebook_scraper = FacebookMarketplaceScraper(
            credentials_file=facebook_credentials_file,
            sessions_dir=str(project_root / 'data' / 'cache' / 'facebook_sessions'),
            headless=facebook_headless,
            cache_dir=str(project_root / 'data' / 'cache' / 'facebook')
        )
        
        # Initialize pre-foreclosure scraper
        self.preforeclosure_scraper = PreForeclosureScraper(
            county=county,
            state=state,
            cache_dir=str(project_root / 'data' / 'cache' / 'preforeclosure')
        )
        
        # Initialize lead pipeline integrator
        self.lead_integrator = LeadPipelineIntegrator(
            output_dir=str(self.output_dir)
        )
        
        # Initialize property enricher for adding valuable flags
        self.property_enricher = PropertyEnricher()
        
        # Initialize FSBO filterer to exclude rentals and spam
        self.fsbo_filterer = FSBOFilterer()
        
        # Initialize lead exporter for CSV/Excel exports
        exports_dir = project_root / 'exports'
        self.lead_exporter = LeadExporter(output_dir=str(exports_dir))
        
        # Initialize lead manager for status and notes tracking
        leads_dir = project_root / 'data' / 'leads'
        self.lead_manager = LeadManager(data_dir=str(leads_dir))
        
        # Initialize lead alert system for high-value lead notifications
        self.lead_alert_system = LeadAlertSystem()
        
        # Initialize PDF date extractor for pre-foreclosure notices
        self.pdf_date_extractor = PdfDateExtractor()
        
        logger.info("Initialized Lead Generation Pipeline")
    
    def run_pipeline(
        self,
        run_craigslist: bool = True,
        run_facebook: bool = True,
        run_preforeclosure: bool = True,
        max_listings: int = 50,
        generate_reports: bool = True,
        report_format: str = "pdf",
        filter_rentals: bool = True,
        filter_spam: bool = True,
        export_csv: bool = False,
        export_excel: bool = False,
        export_min_score: float = 0.0,
        export_include_owner_occupied: bool = True,
        export_min_equity: Optional[float] = None,
        enable_alerts: bool = True,
        alert_threshold: float = 85.0,
        extract_auction_dates: bool = True
    ) -> Dict:
        """
        Run the FSBO pipeline
        
        Args:
            run_craigslist: Whether to run Craigslist scraper
            run_facebook: Whether to run Facebook scraper
            max_listings: Maximum number of listings to scrape from each source
            generate_reports: Whether to generate reports
            report_format: Format for reports ("pdf", "csv", "json")
            
        Returns:
            Dict with pipeline results
        """
        # Track results
        results = {
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "leads": {
                "total": 0,
                "by_source": {},
                "high_quality": 0
            },
            "reports": {
                "generated": 0,
                "paths": []
            }
        }
        
        # Combined leads from all sources
        all_leads = []
        
        # Configure FSBO filterer
        self.fsbo_filterer.enable_rental_filter = filter_rentals
        self.fsbo_filterer.enable_spam_filter = filter_spam
        
        if filter_rentals or filter_spam:
            logger.info(f"FSBO filtering enabled: rentals={filter_rentals}, spam={filter_spam}")
        else:
            logger.info("FSBO filtering disabled")
        
        # Run Craigslist scraper
        if run_craigslist:
            logger.info("Running Craigslist FSBO scraper")
            try:
                cl_leads = self.craigslist_scraper.run(max_pages=5, max_listings=max_listings)
                
                if cl_leads:
                    initial_count = len(cl_leads)
                    logger.info(f"Found {initial_count} leads from Craigslist")
                    
                    # Apply FSBO filters if enabled
                    if filter_rentals or filter_spam:
                        cl_leads = self.fsbo_filterer.filter_listings(cl_leads)
                        filtered_count = initial_count - len(cl_leads)
                        logger.info(f"Filtered out {filtered_count} Craigslist listings ({filtered_count/initial_count:.1%})")
                    
                    all_leads.extend(cl_leads)
                    
                    results["sources"].append("craigslist")
                    results["leads"]["by_source"]["craigslist"] = len(cl_leads)
                    if filter_rentals or filter_spam:
                        results["leads"]["filtered"] = results["leads"].get("filtered", {})
                        results["leads"]["filtered"]["craigslist"] = initial_count - len(cl_leads)
                else:
                    logger.warning("No leads found from Craigslist")
            
            except Exception as e:
                logger.error(f"Error running Craigslist scraper: {e}")
        
        # Run Facebook scraper
        if run_facebook:
            logger.info("Running Facebook Marketplace FSBO scraper")
            try:
                fb_leads = self.facebook_scraper.run(max_listings=max_listings)
                
                if fb_leads:
                    initial_count = len(fb_leads)
                    logger.info(f"Found {initial_count} leads from Facebook Marketplace")
                    
                    # Apply FSBO filters if enabled
                    if filter_rentals or filter_spam:
                        fb_leads = self.fsbo_filterer.filter_listings(fb_leads)
                        filtered_count = initial_count - len(fb_leads)
                        logger.info(f"Filtered out {filtered_count} Facebook listings ({filtered_count/initial_count:.1%})")
                    
                    all_leads.extend(fb_leads)
                    
                    results["sources"].append("facebook")
                    results["leads"]["by_source"]["facebook"] = len(fb_leads)
                    if filter_rentals or filter_spam:
                        results["leads"]["filtered"] = results["leads"].get("filtered", {})
                        results["leads"]["filtered"]["facebook"] = initial_count - len(fb_leads)
                else:
                    logger.warning("No leads found from Facebook Marketplace")
            
            except Exception as e:
                logger.error(f"Error running Facebook scraper: {e}")
        
        # Run Pre-Foreclosure scraper
        if run_preforeclosure:
            logger.info("Running Pre-Foreclosure scraper")
            try:
                pf_leads = self.preforeclosure_scraper.run()
                
                if pf_leads:
                    logger.info(f"Found {len(pf_leads)} leads from Pre-Foreclosure sources")
                    
                    # Extract auction dates from PDFs if enabled
                    if extract_auction_dates:
                        logger.info(f"Extracting auction dates from pre-foreclosure PDFs")
                        dates_extracted = 0
                        pdfs_processed = 0
                        
                        for lead in pf_leads:
                            # Check if this lead has associated PDFs
                            pdf_path = lead.get('pdf_path')
                            if pdf_path and os.path.exists(pdf_path):
                                pdfs_processed += 1
                                # Extract dates from the PDF and update the lead
                                updated_lead = self.pdf_date_extractor.update_lead_with_dates(lead, pdf_path)
                                
                                # Check if dates were extracted
                                if updated_lead.get('auction_date') or updated_lead.get('redemption_deadline'):
                                    dates_extracted += 1
                                    
                                    # Log important date information
                                    property_id = updated_lead.get('property_id', 'Unknown')
                                    if updated_lead.get('auction_date'):
                                        logger.info(f"Extracted auction date for {property_id}: {updated_lead['auction_date']}")
                                    if updated_lead.get('redemption_deadline'):
                                        logger.info(f"Extracted redemption deadline for {property_id}: {updated_lead['redemption_deadline']}")
                                    if updated_lead.get('urgency_level'):
                                        logger.info(f"Urgency level for {property_id}: {updated_lead['urgency_level']}")
                        
                        logger.info(f"Processed {pdfs_processed} PDFs, extracted dates from {dates_extracted} pre-foreclosure leads")
                        results["date_extraction"] = {
                            "pdfs_processed": pdfs_processed,
                            "dates_extracted": dates_extracted
                        }
                    
                    all_leads.extend(pf_leads)
                    
                    results["sources"].append("preforeclosure")
                    results["leads"]["by_source"]["preforeclosure"] = len(pf_leads)
                else:
                    logger.warning("No leads found from Pre-Foreclosure sources")
            
            except Exception as e:
                logger.error(f"Error running Pre-Foreclosure scraper: {e}")
        
        # Update lead counts
        results["leads"]["total"] = len(all_leads)
        
        # Calculate total filtered count if filtering was enabled
        if filter_rentals or filter_spam:
            total_filtered = sum(results["leads"].get("filtered", {}).values())
            results["leads"]["total_filtered"] = total_filtered
            logger.info(f"Total filtered listings: {total_filtered}")
        
        # If we have leads, run them through the pipeline
        if all_leads:
            # Enrich leads with owner occupancy information and equity estimates
            logger.info("Enriching leads with owner occupancy flags and equity estimates")
            try:
                # Add owner occupancy flag
                all_leads = self.property_enricher.add_owner_occupancy_flag(all_leads)
                
                # Add equity estimate
                all_leads = self.property_enricher.add_equity_estimate(all_leads)
                
                # Initialize lead status and notes fields
                all_leads = self.lead_manager.initialize_leads(all_leads)
                
                # Process high-value lead alerts if enabled
                if enable_alerts:
                    logger.info(f"Checking for high-value leads (threshold: {alert_threshold})")
                    alerts_sent, errors = self.lead_alert_system.process_leads_for_alerts(all_leads)
                    
                    if alerts_sent > 0:
                        results["alerts"] = {
                            "sent": alerts_sent,
                            "threshold": alert_threshold
                        }
                        logger.info(f"Sent {alerts_sent} alerts for high-value leads")
                    
                    if errors:
                        logger.warning(f"Alert errors: {errors}")
                
                # Count non-owner occupied properties
                non_owner_occupied = sum(1 for lead in all_leads if lead.get('owner_occupied') is False)
                logger.info(f"Found {non_owner_occupied} non-owner occupied properties ({non_owner_occupied/len(all_leads):.1%} of total)")
                
                # Track in results
                results["leads"]["non_owner_occupied"] = non_owner_occupied
                
            except Exception as e:
                logger.error(f"Error enriching leads: {e}")
            
            # Save combined leads to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            combined_file = self.output_dir / f"combined_fsbo_leads_{timestamp}.json"
            
            try:
                # Save each lead individually for tracking
                self.lead_manager.save_all_leads(all_leads)
                
                # Also save combined file for convenience
                with open(combined_file, 'w') as f:
                    json.dump(all_leads, f, indent=2)
                logger.info(f"Saved {len(all_leads)} combined leads to {combined_file}")
            except Exception as e:
                logger.error(f"Error saving combined leads: {e}")
            
            # Process through lead integrator
            if generate_reports:
                logger.info(f"Processing {len(all_leads)} leads through pipeline")
                
                try:
                    pipeline_results = self.lead_integrator.process_leads(
                        leads=all_leads,
                        generate_reports=True,
                        report_format=report_format
                    )
                    
                    # Update results
                    if "high_quality_leads" in pipeline_results:
                        results["leads"]["high_quality"] = len(pipeline_results["high_quality_leads"])
                    
                    if "reports" in pipeline_results:
                        results["reports"]["generated"] = len(pipeline_results["reports"])
                        results["reports"]["paths"] = pipeline_results["reports"]
                    
                    logger.info(f"Generated {results['reports']['generated']} reports")
                
                except Exception as e:
                    logger.error(f"Error processing leads through pipeline: {e}")
        else:
            logger.warning("No leads found from any source")
        
        # Export leads to CSV/Excel if requested
        if export_csv or export_excel:
            logger.info("Exporting leads to CSV/Excel")
            
            export_files = []
            
            try:
                # Export to CSV
                if export_csv:
                    csv_path = self.lead_exporter.export_to_csv(
                        leads=all_leads,
                        min_score=export_min_score,
                        include_owner_occupied=export_include_owner_occupied,
                        min_equity_percentage=export_min_equity
                    )
                    if csv_path:
                        export_files.append(csv_path)
                        results["exports"] = results.get("exports", {"csv": [], "excel": []})
                        results["exports"]["csv"] = [csv_path]
                        logger.info(f"Exported leads to CSV: {csv_path}")
                
                # Export to Excel
                if export_excel:
                    excel_path = self.lead_exporter.export_to_excel(
                        leads=all_leads,
                        min_score=export_min_score,
                        include_owner_occupied=export_include_owner_occupied,
                        min_equity_percentage=export_min_equity
                    )
                    if excel_path:
                        export_files.append(excel_path)
                        results["exports"] = results.get("exports", {"csv": [], "excel": []})
                        results["exports"]["excel"] = [excel_path]
                        logger.info(f"Exported leads to Excel: {excel_path}")
            
            except Exception as e:
                logger.error(f"Error exporting leads: {e}")
        
        return results


def main():
    """Run the Lead Generation pipeline from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Lead Generation Pipeline")
    parser.add_argument("--output-dir", type=str, help="Directory for output files")
    parser.add_argument("--no-craigslist", action="store_true", help="Skip Craigslist scraper")
    parser.add_argument("--no-facebook", action="store_true", help="Skip Facebook scraper")
    parser.add_argument("--no-preforeclosure", action="store_true", help="Skip Pre-Foreclosure scraper")
    parser.add_argument("--facebook-credentials", type=str, help="Path to Facebook credentials file")
    parser.add_argument("--facebook-visible", action="store_true", help="Run Facebook scraper with visible browser")
    parser.add_argument("--county", type=str, default="Cumberland", help="County for pre-foreclosure search")
    parser.add_argument("--state", type=str, default="ME", help="State for pre-foreclosure search")
    parser.add_argument("--max-listings", type=int, default=50, help="Maximum listings per source")
    parser.add_argument("--no-reports", action="store_true", help="Skip report generation")
    parser.add_argument("--report-format", type=str, default="pdf", choices=["pdf", "csv", "json"], help="Report format")
    
    # FSBO filter options
    parser.add_argument("--no-filter", action="store_true", help="Disable all FSBO filtering")
    parser.add_argument("--no-rental-filter", action="store_true", help="Disable rental filtering")
    parser.add_argument("--no-spam-filter", action="store_true", help="Disable spam filtering")
    
    # Export options
    parser.add_argument("--export-csv", action="store_true", help="Export leads to CSV for direct mail")
    parser.add_argument("--export-excel", action="store_true", help="Export leads to Excel spreadsheet")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum lead score for export (0-100)")
    parser.add_argument("--exclude-owner-occupied", action="store_true", help="Exclude owner-occupied properties from export")
    parser.add_argument("--min-equity", type=float, help="Minimum equity percentage for export (0-100)")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LeadGenerationPipeline(
        output_dir=args.output_dir,
        facebook_credentials_file=args.facebook_credentials,
        facebook_headless=not args.facebook_visible,
        county=args.county,
        state=args.state
    )
    
    # Run pipeline
    results = pipeline.run_pipeline(
        run_craigslist=not args.no_craigslist,
        run_facebook=not args.no_facebook,
        run_preforeclosure=not args.no_preforeclosure,
        max_listings=args.max_listings,
        generate_reports=not args.no_reports,
        report_format=args.report_format,
        filter_rentals=not (args.no_filter or args.no_rental_filter),
        filter_spam=not (args.no_filter or args.no_spam_filter),
        export_csv=args.export_csv,
        export_excel=args.export_excel,
        export_min_score=args.min_score,
        export_include_owner_occupied=not args.exclude_owner_occupied,
        export_min_equity=args.min_equity
    )
    
    # Print summary
    print("\n===== Lead Generation Pipeline Results =====")
    print(f"Total leads: {results['leads']['total']}")
    for source, count in results['leads']['by_source'].items():
        print(f"  - {source}: {count} leads")
    print(f"High quality leads: {results['leads']['high_quality']}")
    
    # Print export summary if applicable
    if results.get('exports'):
        print("\n----- Export Summary -----")
        if results['exports'].get('csv'):
            print(f"CSV Export: {results['exports']['csv'][0]}")
        if results['exports'].get('excel'):
            print(f"Excel Export: {results['exports']['excel'][0]}")
    print(f"Reports generated: {results['reports']['generated']}")
    print("=========================================\n")


if __name__ == "__main__":
    main()
