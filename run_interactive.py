"""
Interactive runner script for Indian eCourts Automated Case Scraper
Provides user-friendly interface for single case scraping
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from automated_scraper import AutomatedECourtsScraper
from config import ERROR_MESSAGES, SUCCESS_MESSAGES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("🏛️  Indian eCourts Automated Case Scraper")
    print("="*60)
    print("Interactive Mode - Single Case Processing")
    print("Browser will be visible for observation")
    print("="*60 + "\n")


def get_cnr_input():
    """Get CNR input from user with validation"""
    print("\nEnter CNR Number (16 characters):")
    print("Format: SSCCNNNNNNNNNNNN")
    print("Example: GJAH010053852024")
    print("Press Enter to use default CNR: GJAH010053852024")
    print("\nType 'quit' or 'exit' to stop the program")
    
    cnr = input("\nCNR: ").strip().upper()
    
    if cnr.lower() in ['quit', 'exit', 'q']:
        return None
    
    # Use default CNR if user just presses Enter
    if not cnr:
        cnr = "GJAH010053852024"
        print(f"Using default CNR: {cnr}")
    
    if len(cnr) != 16:
        print(f"❌ CNR must be exactly 16 characters. You entered {len(cnr)} characters.")
        return None
    
    # Basic format validation
    if not (cnr[:2].isalpha() and cnr[2:4].isalnum() and cnr[4:].isdigit()):
        print("❌ Invalid CNR format. Expected format: SSCCNNNNNNNNNNNN")
        return None
    
    return cnr


def print_court_info(scraper, cnr):
    """Print detected court information"""
    try:
        court_info = scraper.detect_court_type(cnr)
        print(f"\n📍 Detected Court Information:")
        print(f"   State: {court_info['state_name']} ({court_info['state_code']})")
        print(f"   Court Type: {court_info['court_type']}")
        print(f"   Court Code: {court_info['court_code']}")
        print(f"   Unique Number: {court_info['unique_number']}")
    except ValueError as e:
        print(f"❌ Error detecting court info: {e}")
        return False
    return True


def print_case_result(result):
    """Print formatted case result"""
    print(f"\n{'='*60}")
    print(f"📋 CASE RESULT FOR CNR: {result['cnr']}")
    print(f"{'='*60}")
    
    if result['status'] == 'found':
        print(f"✅ {SUCCESS_MESSAGES['case_found']}")
        print(f"\n📊 Case Details:")
        
        if result.get('case_number'):
            print(f"   Case Number: {result['case_number']}")
        if result.get('case_type'):
            print(f"   Case Type: {result['case_type']}")
        if result.get('filing_date'):
            print(f"   Filing Date: {result['filing_date']}")
        if result.get('registration_date'):
            print(f"   Registration Date: {result['registration_date']}")
        if result.get('court_name'):
            print(f"   Court Name: {result['court_name']}")
        if result.get('judge_name'):
            print(f"   Judge: {result['judge_name']}")
        if result.get('next_hearing_date'):
            print(f"   Next Hearing: {result['next_hearing_date']}")
        if result.get('case_stage'):
            print(f"   Case Stage: {result['case_stage']}")
        
        if result.get('petitioners'):
            print(f"   Petitioners: {', '.join(result['petitioners'])}")
        if result.get('respondents'):
            print(f"   Respondents: {', '.join(result['respondents'])}")
            
    elif result['status'] == 'captcha_detected':
        print(f"🤖 {ERROR_MESSAGES['captcha_detected']}")
        print("   The scraper detected a CAPTCHA on the website.")
        print("   This case was skipped to avoid automated solving.")
        
    elif result['status'] == 'case_not_found':
        print(f"❌ {ERROR_MESSAGES['case_not_found']}")
        print("   The CNR number was not found in the court database.")
        
    elif result['status'] == 'invalid_cnr':
        print(f"❌ {ERROR_MESSAGES['invalid_cnr']}")
        
    elif result['status'] == 'unsupported_state':
        print(f"❌ Unsupported state code in CNR")
        
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error occurred')}")
    
    print(f"\n⏰ Scraped at: {result.get('scraped_at', 'Unknown')}")
    
    if result.get('detected_court_info'):
        court_info = result['detected_court_info']
        print(f"🏛️  Court: {court_info['court_type']} - {court_info['state_name']}")


def main():
    """Main interactive function"""
    print_banner()
    
    # Initialize scraper with visible browser
    print("🚀 Initializing scraper with visible browser...")
    scraper = AutomatedECourtsScraper(headless=False)
    
    try:
        # Get CNR input
        cnr = get_cnr_input()
        if cnr is None:
            print("\n👋 Goodbye!")
            return
        
        print(f"\n🔍 Processing CNR: {cnr}")
        
        # Validate and show court info
        if not print_court_info(scraper, cnr):
            return
        
        # Confirm processing
        confirm = input(f"\n🤔 Proceed with scraping this case? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("⏭️  Scraping cancelled.")
            return
        
        print(f"\n⏳ Starting scraping process...")
        print("🌐 Browser window should be visible - you can observe the process")
        
        # Scrape the case
        result = scraper.scrape_case_with_retry(cnr)
        
        # Print results
        print_case_result(result)
        
        print("\n👋 Thank you for using the eCourts scraper!")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in main: {str(e)}")
    finally:
        # Clean up
        print("\n🧹 Cleaning up browser resources...")
        scraper.close()
        print("✅ Cleanup completed.")


if __name__ == "__main__":
    main()
