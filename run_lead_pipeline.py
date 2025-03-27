#!/usr/bin/env python
"""
Run Lead Pipeline

A simple command-line script to run the entire Midcoast Leads pipeline
from lead scraping to report generation.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.scrapers.lead_pipeline_integrator import LeadPipelineIntegrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RunLeadPipeline")

def main():
    """Run the lead generation pipeline"""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Run the Midcoast Leads pipeline from lead scraping to report generation'
    )
    
    # Config and output options
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output-dir', help='Directory for output files')
    
    # Pipeline components
    parser.add_argument('--skip-fsbo', action='store_true', help='Skip FSBO scraper')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip lead analysis')
    parser.add_argument('--skip-reporting', action='store_true', help='Skip report generation')
    
    # Input options
    parser.add_argument('--lead-files', nargs='+', help='Process existing lead files instead of scraping')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Ensure logs directory exists
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    
    # Log start
    logger.info("Starting Midcoast Leads Pipeline")
    
    try:
        # Initialize the pipeline integrator
        integrator = LeadPipelineIntegrator(
            config_path=args.config,
            output_dir=args.output_dir
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
        print("\n" + "="*50)
        print("MIDCOAST LEADS PIPELINE RESULTS")
        print("="*50)
        print(f"Total leads processed: {results['leads']['total']}")
        print(f"FSBO leads: {len(results['leads']['fsbo'])}")
        
        if results['analysis']['high_potential_leads']:
            print(f"High potential leads: {len(results['analysis']['high_potential_leads'])}")
            
            # Print top 3 leads
            print("\nTop leads:")
            for i, lead in enumerate(results['analysis']['high_potential_leads'][:3], 1):
                print(f"  {i}. {lead.get('address', 'Unknown')} - ML Score: {lead.get('ml_score', 0):.2f}, "
                      f"Price: ${lead.get('price', 0):,.0f}")
        
        if results['reporting']['reports_generated'] > 0:
            print(f"\nReports generated: {results['reporting']['reports_generated']}")
            print(f"Report package: {results['reporting']['package_path']}")
            print(f"Report index: {results['reporting']['index_path']}")
            
            # Open the report in the browser if available
            if results['reporting'].get('index_path'):
                print("\nTo view reports in your browser, run:")
                print(f"open {results['reporting']['index_path']}")
        
        print("="*50)
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Error running pipeline: {e}", exc_info=True)
        print(f"\nError running pipeline: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
