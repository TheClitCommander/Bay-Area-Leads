#!/usr/bin/env python3
"""
Test PDF Date Extraction

This script demonstrates the PDF date extraction functionality for
pre-foreclosure notices and legal documents.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Import the PDF date extractor
from src.utils.pdf_date_extractor import PdfDateExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PDFDateExtractor")

def print_date_info(date_info):
    """Print extracted date information in a readable format"""
    print("\n===== Extracted Date Information =====")
    
    # Auction date
    if date_info['auction_date']:
        print(f"Auction Date: {date_info['auction_date']}")
        if date_info['days_until_auction'] is not None:
            print(f"Days Until Auction: {date_info['days_until_auction']}")
    else:
        print("Auction Date: Not found")
    
    # Redemption deadline
    if date_info['redemption_deadline']:
        print(f"Redemption Deadline: {date_info['redemption_deadline']}")
        if date_info['days_until_redemption_deadline'] is not None:
            print(f"Days Until Redemption: {date_info['days_until_redemption_deadline']}")
    else:
        print("Redemption Deadline: Not found")
    
    # Notice date
    if date_info['notice_date']:
        print(f"Notice Date: {date_info['notice_date']}")
    else:
        print("Notice Date: Not found")
    
    # Urgency level
    print(f"Urgency Level: {date_info['urgency_level']}")
    
    # Confidence score
    print(f"Confidence Score: {date_info['confidence_score']:.2f}")
    
    # All dates
    if date_info['all_dates']:
        print("\nAll Dates Found:")
        for i, date in enumerate(date_info['all_dates'], 1):
            print(f"  {i}. {date['date_str']} at position {date['position']}")
    else:
        print("\nNo dates found in the document")
    
    print("=====================================")

def main():
    """Run the PDF date extraction test"""
    parser = argparse.ArgumentParser(description="Test PDF date extraction capabilities")
    parser.add_argument("pdf_path", help="Path to PDF file for date extraction", nargs="?")
    parser.add_argument("--batch", help="Process all PDFs in a directory", action="store_true")
    parser.add_argument("--dir", help="Directory containing PDFs to process")
    args = parser.parse_args()
    
    # Initialize PDF date extractor
    extractor = PdfDateExtractor()
    print(f"Initialized PDF Date Extractor")
    
    # If no args provided, use the sample data
    if not args.pdf_path and not args.dir:
        # Create sample data directory if needed
        sample_dir = project_root / 'test_data' / 'sample_pdfs'
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Let the user know they need to provide a PDF
        print("\n⚠️ No PDF file specified.")
        print(f"Please put sample foreclosure PDFs in the directory: {sample_dir}")
        print("Then run this script with the PDF file path:")
        print(f"  python {sys.argv[0]} /path/to/notice.pdf")
        print("\nOr process all PDFs in a directory:")
        print(f"  python {sys.argv[0]} --batch --dir /path/to/pdf/folder")
        return 1
    
    # Process single PDF file
    if args.pdf_path and not args.batch:
        pdf_path = args.pdf_path
        
        if not os.path.exists(pdf_path):
            print(f"\n⚠️ PDF file not found: {pdf_path}")
            return 1
        
        print(f"\nProcessing PDF: {pdf_path}")
        
        # Extract dates from PDF
        date_info = extractor.extract_dates_from_pdf(pdf_path)
        
        # Print extracted information
        print_date_info(date_info)
        
        # Show how this would affect a lead
        print("\nHow this would update a lead:")
        print("-----------------------------")
        print(f"auction_date: {date_info['auction_date']}")
        print(f"redemption_deadline: {date_info['redemption_deadline']}")
        print(f"days_until_auction: {date_info['days_until_auction']}")
        print(f"urgency_level: {date_info['urgency_level']}")
    
    # Process batch of PDFs
    elif args.batch and args.dir:
        pdf_dir = args.dir
        
        if not os.path.exists(pdf_dir) or not os.path.isdir(pdf_dir):
            print(f"\n⚠️ Directory not found: {pdf_dir}")
            return 1
        
        # Find all PDF files in the directory
        pdf_files = list(Path(pdf_dir).glob('*.pdf'))
        
        if not pdf_files:
            print(f"\n⚠️ No PDF files found in directory: {pdf_dir}")
            return 1
        
        print(f"\nProcessing {len(pdf_files)} PDFs in directory: {pdf_dir}")
        
        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            
            # Extract dates from PDF
            date_info = extractor.extract_dates_from_pdf(str(pdf_path))
            
            # Print extracted information
            print_date_info(date_info)
    
    else:
        print("\n⚠️ Invalid arguments. Please specify either a PDF file path or --batch --dir options.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
