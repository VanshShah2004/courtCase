"""
Example usage script for Indian eCourts Automated Case Scraper
Demonstrates different ways to use the scraper
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from automated_scraper import AutomatedECourtsScraper


def example_single_case():
    """Example: Scrape a single case with visible browser"""
    print("🔍 Example: Single Case Scraping")
    print("="*50)
    
    # Initialize scraper with visible browser
    scraper = AutomatedECourtsScraper(headless=False)
    
    try:
        # Example CNR (Gujarat High Court)
        cnr = "GJAH010053852024"
        
        print(f"Scraping CNR: {cnr}")
        
        # Scrape the case
        result = scraper.scrape_case_with_retry(cnr)
        
        # Print result
        print(f"\nResult: {result['status']}")
        if result['status'] == 'found':
            print(f"Case Number: {result.get('case_number', 'N/A')}")
            print(f"Court: {result.get('court_name', 'N/A')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        scraper.close()


def example_batch_processing():
    """Example: Process multiple CNR numbers"""
    print("\n📋 Example: Batch Processing")
    print("="*50)
    
    # List of CNR numbers to process
    cnr_list = [
        "GJAH010053852024",  # Gujarat High Court
        "DL01HC001234567",   # Delhi High Court
        "MH01DC005678901",   # Maharashtra District Court
    ]
    
    # Initialize scraper
    scraper = AutomatedECourtsScraper(headless=False)
    
    try:
        results = []
        for i, cnr in enumerate(cnr_list, 1):
            print(f"\nProcessing {i}/{len(cnr_list)}: {cnr}")
            
            result = scraper.scrape_case_with_retry(cnr)
            results.append(result)
            
            print(f"Status: {result['status']}")
            if result['status'] == 'found':
                print(f"✅ Case found: {result.get('case_number', 'N/A')}")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'found')
        print(f"\n📊 Summary: {successful}/{len(results)} cases found successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        scraper.close()


def example_context_manager():
    """Example: Using context manager for automatic cleanup"""
    print("\n🧹 Example: Context Manager Usage")
    print("="*50)
    
    # Using context manager ensures proper cleanup
    with AutomatedECourtsScraper(headless=False) as scraper:
        cnr = "GJAH010053852024"
        
        print(f"Scraping CNR: {cnr}")
        
        result = scraper.scrape_case_with_retry(cnr)
        
        print(f"Result: {result['status']}")
        
        # Browser will be automatically closed when exiting the context


def example_cnr_validation():
    """Example: CNR validation and court detection"""
    print("\n✅ Example: CNR Validation")
    print("="*50)
    
    scraper = AutomatedECourtsScraper(headless=True)  # No browser needed for validation
    
    test_cnrs = [
        "GJAH010053852024",  # Valid
        "INVALID1234567890", # Invalid
        "GJAH0100538520245", # Too long
        "GJAH01005385202",   # Too short
    ]
    
    for cnr in test_cnrs:
        print(f"\nTesting CNR: {cnr}")
        
        # Validate CNR
        is_valid = scraper.validate_cnr(cnr)
        print(f"Valid: {is_valid}")
        
        if is_valid:
            try:
                # Detect court type
                court_info = scraper.detect_court_type(cnr)
                print(f"State: {court_info['state_name']}")
                print(f"Court Type: {court_info['court_type']}")
            except ValueError as e:
                print(f"Error: {e}")
        else:
            print("❌ Invalid CNR format")


def main():
    """Run all examples"""
    print("🏛️  Indian eCourts Scraper - Usage Examples")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Run examples
    example_cnr_validation()
    example_single_case()
    example_batch_processing()
    example_context_manager()
    
    print("\n✅ All examples completed!")
    print("\nTo run the interactive scraper:")
    print("  python run_interactive.py")
    print("\nTo run batch processing:")
    print("  python run_batch.py")


if __name__ == "__main__":
    main()
