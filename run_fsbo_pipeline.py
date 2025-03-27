#!/usr/bin/env python3
"""
Comprehensive Lead Pipeline Runner

This script runs the unified lead generation pipeline that scrapes Craigslist and Facebook
Marketplace for FSBO listings, public records for pre-foreclosures, scores all leads,
and generates investor-grade reports.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Import the lead generation pipeline
from src.scrapers.fsbo_pipeline import LeadGenerationPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'logs' / f'fsbo_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("LeadPipelineRunner")


def main():
    """Run the lead generation pipeline from command line"""
    # Create logs directory if it doesn't exist
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Run Comprehensive Lead Generation Pipeline")
    parser.add_argument("--output-dir", type=str, help="Directory for output files")
    parser.add_argument("--craigslist-only", action="store_true", help="Only run Craigslist scraper")
    parser.add_argument("--facebook-only", action="store_true", help="Only run Facebook scraper")
    parser.add_argument("--preforeclosure-only", action="store_true", help="Only run Pre-Foreclosure scraper")
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
    
    # FSBO Filtering options
    parser.add_argument("--no-filter", action="store_true", help="Disable all FSBO filtering")
    parser.add_argument("--no-rental-filter", action="store_true", help="Disable rental filtering")
    parser.add_argument("--no-spam-filter", action="store_true", help="Disable spam filtering")
    
    # Export options for direct mail
    parser.add_argument("--export-csv", action="store_true", help="Export leads to CSV for direct mail campaigns")
    parser.add_argument("--export-excel", action="store_true", help="Export leads to Excel spreadsheet")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum lead score for export (0-100)")
    parser.add_argument("--exclude-owner-occupied", action="store_true", help="Exclude owner-occupied properties from export")
    parser.add_argument("--min-equity", type=float, help="Minimum equity percentage for export (0-100)")
    
    # Alert options for high-value leads
    parser.add_argument("--no-alerts", action="store_true", help="Disable high-value lead alerts")
    parser.add_argument("--alert-threshold", type=float, default=85.0, help="Score threshold for lead alerts (0-100)")
    
    # Auction date extraction options
    parser.add_argument("--no-extract-dates", action="store_true", help="Disable auction date extraction from PDFs")
    
    args = parser.parse_args()
    
    # Determine which scrapers to run
    run_craigslist = True
    run_facebook = True
    run_preforeclosure = True
    
    if args.craigslist_only:
        run_facebook = False
        run_preforeclosure = False
    elif args.facebook_only:
        run_craigslist = False
        run_preforeclosure = False
    elif args.preforeclosure_only:
        run_craigslist = False
        run_facebook = False
    
    # Individual toggles override the "only" flags
    if args.no_craigslist:
        run_craigslist = False
    if args.no_facebook:
        run_facebook = False
    if args.no_preforeclosure:
        run_preforeclosure = False
    
    # Validate Facebook options
    if run_facebook and not args.facebook_credentials:
        # Check for credentials in default location
        default_credentials = project_root / 'config' / 'facebook_credentials.json'
        if not default_credentials.exists():
            logger.warning("No Facebook credentials file specified and none found in default location.")
            logger.warning("A template will be created for you to fill in.")
    
    # Initialize pipeline
    try:
        pipeline = LeadGenerationPipeline(
            output_dir=args.output_dir,
            facebook_credentials_file=args.facebook_credentials,
            facebook_headless=not args.facebook_visible,
            county=args.county,
            state=args.state
        )
        
        # Print startup message
        print("\n===== MidcoastLeads Lead Generation Pipeline =====")
        
        # Determine which sources are active
        active_sources = []
        if run_craigslist:
            active_sources.append("Craigslist")
        if run_facebook:
            active_sources.append("Facebook")
        if run_preforeclosure:
            active_sources.append("Pre-Foreclosure")
            
        print(f"Running {', '.join(active_sources)} scrapers")
        print(f"Maximum listings per source: {args.max_listings}")
        print(f"Generating reports: {'No' if args.no_reports else 'Yes'}")
        if not args.no_reports:
            print(f"Report format: {args.report_format}")
            
        # Display export settings
        if args.export_csv or args.export_excel:
            export_format = []
            if args.export_csv:
                export_format.append("CSV")
            if args.export_excel:
                export_format.append("Excel")
                
            print(f"\nExporting leads to: {', '.join(export_format)}")
            print(f"  - Min score: {args.min_score}")
            print(f"  - Include owner-occupied: {'No' if args.exclude_owner_occupied else 'Yes'}")
            if args.min_equity is not None:
                print(f"  - Min equity: {args.min_equity}%")
        
        # Display alert settings
        if not args.no_alerts:
            print(f"\nHigh-value lead alerts: Enabled")
            print(f"  - Alert threshold: {args.alert_threshold}")
            config_path = project_root / 'config' / 'email_config.json'
            if config_path.exists():
                print(f"  - Email config: {config_path}")
            else:
                print(f"  - Email config: Not configured (template will be created)")
        
        # Display auction date extraction settings
        if not args.no_extract_dates:
            print(f"\nAuction date extraction: Enabled")
            config_path = project_root / 'config' / 'pdf_extractor_config.json'
            if config_path.exists():
                print(f"  - PDF extractor config: {config_path}")
            else:
                print(f"  - PDF extractor config: Not configured (template will be created)")
        print("=====================================\n")
        
        # Set up filtering options
        filter_rentals = not (args.no_filter or args.no_rental_filter)
        filter_spam = not (args.no_filter or args.no_spam_filter)
        
        # Run pipeline
        results = pipeline.run_pipeline(
            run_craigslist=run_craigslist,
            run_facebook=run_facebook,
            run_preforeclosure=run_preforeclosure,
            max_listings=args.max_listings,
            generate_reports=not args.no_reports,
            report_format=args.report_format,
            filter_rentals=filter_rentals,
            filter_spam=filter_spam,
            export_csv=args.export_csv,
            export_excel=args.export_excel,
            export_min_score=args.min_score,
            export_include_owner_occupied=not args.exclude_owner_occupied,
            export_min_equity=args.min_equity,
            enable_alerts=not args.no_alerts,
            alert_threshold=args.alert_threshold,
            extract_auction_dates=not args.no_extract_dates
        )
        
        # Print summary
        print("\n===== Lead Generation Pipeline Results =====")
        print(f"Total leads found: {results['leads']['total']}")
        
        # Print filtering results if filtering was enabled
        if 'total_filtered' in results['leads']:
            print(f"Filtered out: {results['leads']['total_filtered']} listings")
            if 'filtered' in results['leads']:
                for source, count in results['leads']['filtered'].items():
                    print(f"  - {source}: {count} filtered")
        for source, count in results['leads']['by_source'].items():
            print(f"  - {source}: {count} leads")
        print(f"High quality leads: {results['leads']['high_quality']}")
        print(f"Reports generated: {results['reports']['generated']}")
        
        # Print paths to reports if any
        if results['reports']['generated'] > 0:
            print("\nReport locations:")
            for i, report_path in enumerate(results['reports']['paths'][:5]):
                print(f"  {i+1}. {report_path}")
            
            if len(results['reports']['paths']) > 5:
                print(f"  ... and {len(results['reports']['paths']) - 5} more")
        
        # Print export summary if applicable
        if 'exports' in results:
            print("\n----- Export Summary -----")
            if results['exports'].get('csv'):
                print(f"CSV Export: {results['exports']['csv'][0]}")
            if results['exports'].get('excel'):
                print(f"Excel Export: {results['exports']['excel'][0]}")
        
        # Print alert summary if applicable
        if 'alerts' in results:
            print("\n----- Alert Summary -----")
            print(f"Sent {results['alerts']['sent']} alerts for leads with scores >= {results['alerts']['threshold']}")
            print(f"Check your email for details on these high-value leads")
        
        # Print date extraction summary if applicable
        if 'date_extraction' in results:
            print("\n----- Date Extraction Summary -----")
            pdfs_processed = results['date_extraction'].get('pdfs_processed', 0)
            dates_extracted = results['date_extraction'].get('dates_extracted', 0)
            print(f"Processed {pdfs_processed} PDFs, extracted dates from {dates_extracted} leads")
            
            if dates_extracted > 0:
                print("\nThese leads now have auction dates and urgency levels!")
                print("Use 'python manage_leads.py list' to see all leads with their dates")
        
        print("=========================================\n")
        
        # Return success
        return 0
    
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"Error running pipeline: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
