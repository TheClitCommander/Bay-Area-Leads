#!/usr/bin/env python3
"""
Lead Management Tool

This tool allows you to view, update, and manage your leads, including adding notes
and changing lead status. Use this after running the lead generation pipeline.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Import lead management utilities
from src.utils.lead_management import LeadManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LeadManager")

def print_lead_details(lead: Dict[str, Any], show_history: bool = False) -> None:
    """
    Print detailed information about a lead.
    
    Args:
        lead: Lead dictionary
        show_history: Whether to show interaction history
    """
    print("\n" + "-"*60)
    print(f"🏠 Property: {lead.get('property_address', 'Unknown Address')}")
    print(f"📍 {lead.get('property_city', '')}, {lead.get('property_state', '')} {lead.get('property_zip', '')}")
    print(f"📝 Status: {lead.get('lead_status', 'New')}")
    print(f"📊 Score: {lead.get('lead_score', 'N/A')}")
    
    # Display auction date and timeline info if available
    if lead.get('auction_date'):
        print(f"📅 Auction Date: {lead.get('auction_date')}")
        if lead.get('days_until_auction') is not None:
            print(f"⏱️ Days Until Auction: {lead.get('days_until_auction')}")
    
    if lead.get('redemption_deadline'):
        print(f"🔄 Redemption Deadline: {lead.get('redemption_deadline')}")
        if lead.get('days_until_redemption') is not None:
            print(f"⏱️ Days Until Redemption: {lead.get('days_until_redemption')}")
    
    if lead.get('urgency_level'):
        urgency = lead.get('urgency_level')
        urgency_emoji = '🔴' if urgency == 'Critical' else '🟠' if urgency == 'High' else '🟡' if urgency == 'Medium' else '🟢'
        print(f"{urgency_emoji} Urgency: {urgency}")
    print(f"👤 Owner: {lead.get('owner_name', 'Unknown')}")
    print(f"📮 Mailing: {lead.get('owner_address', '')}, {lead.get('owner_city', '')}, {lead.get('owner_state', '')} {lead.get('owner_zip', '')}")
    
    if lead.get('owner_occupied') is not None:
        print(f"🏡 Owner Occupied: {'Yes' if lead.get('owner_occupied') else 'No'}")
    
    if lead.get('equity_percentage') is not None:
        print(f"💰 Equity: {lead.get('equity_percentage', 0):.1f}%")
    
    if lead.get('assessed_value'):
        print(f"💵 Assessed Value: ${lead.get('assessed_value', 0):,}")
    
    if lead.get('estimated_value'):
        print(f"🔍 Estimated Value: ${lead.get('estimated_value', 0):,}")
    
    print("\n📋 Notes:")
    if lead.get('notes'):
        print(lead.get('notes'))
    else:
        print("(No notes)")
    
    if show_history and lead.get('interaction_history'):
        print("\n📅 Interaction History:")
        for interaction in lead.get('interaction_history', []):
            timestamp = interaction.get('timestamp', '').split('T')[0]  # Just get the date
            action = interaction.get('action', '')
            print(f"  - {timestamp}: {action}")
    
    print("-"*60)

def list_leads(leads: List[Dict[str, Any]], status_filter: Optional[str] = None, urgency_filter: Optional[str] = None) -> None:
    """
    Print a table of leads, optionally filtered by status or urgency.
    
    Args:
        leads: List of lead dictionaries
        status_filter: Status to filter by (if any)
        urgency_filter: Urgency level to filter by (if any)
    """
    # Apply filters
    filtered_leads = leads
    filter_msg = []
    
    if status_filter:
        filtered_leads = [lead for lead in filtered_leads if lead.get('lead_status') == status_filter]
        if not filtered_leads:
            print(f"No leads found with status '{status_filter}'")
            return
        filter_msg.append(f"status '{status_filter}'")
    
    if urgency_filter:
        filtered_leads = [lead for lead in filtered_leads if lead.get('urgency_level') == urgency_filter]
        if not filtered_leads:
            print(f"No leads found with urgency level '{urgency_filter}'")
            return
        filter_msg.append(f"urgency level '{urgency_filter}'")
    
    status_msg = f" with {' and '.join(filter_msg)}" if filter_msg else ""
    
    print(f"\nFound {len(filtered_leads)} leads{status_msg}:")
    
    # Check if any leads have auction dates or urgency levels
    has_auction_dates = any(lead.get('auction_date') for lead in filtered_leads)
    has_urgency = any(lead.get('urgency_level') for lead in filtered_leads)
    
    # Create header based on available data
    header = f"{'ID':<12} {'Status':<15} {'Score':<7} {'Owner':<20} {'Address':<35}"
    separator_length = 90
    
    if has_auction_dates:
        header += f" {'Auction':<10}"
        separator_length += 10
    
    if has_urgency:
        header += f" {'Urgency':<10}"
        separator_length += 10
    
    print(header)
    print("-" * separator_length)
    
    for lead in filtered_leads:
        lead_id = lead.get('property_id', 'Unknown')[:10]
        status = lead.get('lead_status', 'New')
        score = f"{lead.get('lead_score', 'N/A')}"
        owner = lead.get('owner_name', 'Unknown')[:18]
        address = lead.get('property_address', 'Unknown Address')[:33]
        
        line = f"{lead_id:<12} {status:<15} {score:<7} {owner:<20} {address:<35}"
        
        if has_auction_dates:
            auction_date = lead.get('auction_date', '')[:10]
            line += f" {auction_date:<10}"
        
        if has_urgency:
            urgency = lead.get('urgency_level', '')
            urgency_emoji = '🔴' if urgency == 'Critical' else '🟠' if urgency == 'High' else '🟡' if urgency == 'Medium' else '🟢' if urgency == 'Low' else ''
            line += f" {urgency_emoji} {urgency:<8}"
        
        print(line)

def main():
    """Run the lead management tool"""
    parser = argparse.ArgumentParser(description="Manage lead notes and status")
    
    # Main command groups
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List leads command
    list_parser = subparsers.add_parser("list", help="List all leads")
    list_parser.add_argument("--status", type=str, help="Filter by status")
    list_parser.add_argument("--urgency", type=str, choices=['Critical', 'High', 'Medium', 'Low'], 
                           help="Filter by urgency level (Critical, High, Medium, Low)")
    
    # View lead command
    view_parser = subparsers.add_parser("view", help="View lead details")
    view_parser.add_argument("lead_id", type=str, help="Lead ID to view")
    view_parser.add_argument("--history", action="store_true", help="Show interaction history")
    
    # Add note command
    note_parser = subparsers.add_parser("note", help="Add a note to a lead")
    note_parser.add_argument("lead_id", type=str, help="Lead ID to add note to")
    note_parser.add_argument("note_text", type=str, help="Note text to add")
    
    # Update status command
    status_parser = subparsers.add_parser("status", help="Update lead status")
    status_parser.add_argument("lead_id", type=str, help="Lead ID to update status for")
    status_parser.add_argument("new_status", type=str, help="New status value")
    
    # View statuses command
    status_list_parser = subparsers.add_parser("statuses", help="List valid status values")
    
    args = parser.parse_args()
    
    # Initialize lead manager
    lead_manager = LeadManager()
    
    # Load all leads
    all_leads = lead_manager.load_all_leads()
    
    if not all_leads:
        data_path = Path(project_root) / 'data' / 'leads'
        recent_files = list(project_root.glob('combined_fsbo_leads_*.json'))
        
        if recent_files:
            # Sort by modification time, newest first
            recent_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            most_recent = recent_files[0]
            
            try:
                print(f"No leads found in database. Loading from most recent file: {most_recent}")
                with open(most_recent, 'r') as f:
                    all_leads = json.load(f)
                
                # Save leads to database
                lead_manager.save_all_leads(all_leads)
                print(f"Imported {len(all_leads)} leads to database")
            except Exception as e:
                print(f"Error loading leads from file: {e}")
                return 1
        else:
            print("No leads found. Run the lead generation pipeline first.")
            return 1
    
    # Execute command
    if args.command == "list":
        list_leads(all_leads, args.status, args.urgency)
    
    elif args.command == "view":
        lead = lead_manager._get_lead(args.lead_id)
        if lead:
            print_lead_details(lead, args.history)
        else:
            print(f"Lead not found: {args.lead_id}")
    
    elif args.command == "note":
        success = lead_manager.add_lead_note(args.lead_id, args.note_text)
        if success:
            print(f"Added note to lead {args.lead_id}")
            # Show updated lead
            lead = lead_manager._get_lead(args.lead_id)
            print_lead_details(lead)
        else:
            print(f"Failed to add note to lead {args.lead_id}")
    
    elif args.command == "status":
        if args.new_status not in lead_manager.VALID_STATUSES:
            print(f"Invalid status: {args.new_status}")
            print(f"Valid statuses: {', '.join(lead_manager.VALID_STATUSES)}")
            return 1
        
        success = lead_manager.update_lead_status(args.lead_id, args.new_status)
        if success:
            print(f"Updated lead {args.lead_id} status to '{args.new_status}'")
            # Show updated lead
            lead = lead_manager._get_lead(args.lead_id)
            print_lead_details(lead)
        else:
            print(f"Failed to update lead {args.lead_id} status")
    
    elif args.command == "statuses":
        print("\nValid lead status values:")
        for status in lead_manager.VALID_STATUSES:
            print(f"  - {status}")
        print("\nUse these values with the 'status' command to update lead status.")
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
