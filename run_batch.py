"""
Batch processing script for Indian eCourts Automated Case Scraper
Processes multiple CNR numbers from a file or command line
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from automated_scraper import AutomatedECourtsScraper
from config import ERROR_MESSAGES, SUCCESS_MESSAGES, RESULTS_DIR, BATCH_FILE_PREFIX

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles batch processing of multiple CNR numbers"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.scraper = None
        self.results = []
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'captcha_encountered': 0,
            'invalid_cnr': 0,
            'case_not_found': 0,
            'start_time': None,
            'end_time': None
        }
    
    def load_cnr_list_from_file(self, filepath: str) -> List[str]:
        """Load CNR numbers from a text file"""
        cnr_list = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    cnr = line.strip().upper()
                    if cnr and not cnr.startswith('#'):  # Skip empty lines and comments
                        if len(cnr) == 16:
                            cnr_list.append(cnr)
                        else:
                            logger.warning(f"Invalid CNR format in line {line_num}: {cnr}")
            
            logger.info(f"Loaded {len(cnr_list)} valid CNR numbers from {filepath}")
            return cnr_list
            
        except FileNotFoundError:
            logger.error(f"CNR file not found: {filepath}")
            return []
        except Exception as e:
            logger.error(f"Error loading CNR file: {str(e)}")
            return []
    
    def load_cnr_list_from_input(self) -> List[str]:
        """Load CNR numbers from user input"""
        cnr_list = []
        print("Enter CNR numbers (one per line). Press Enter twice when done:")
        
        while True:
            cnr = input().strip().upper()
            if not cnr:
                break
            if len(cnr) == 16:
                cnr_list.append(cnr)
            else:
                print(f"❌ Invalid CNR format: {cnr} (must be 16 characters)")
        
        logger.info(f"Loaded {len(cnr_list)} CNR numbers from user input")
        return cnr_list
    
    def save_batch_summary(self):
        """Save batch processing summary"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{BATCH_FILE_PREFIX}{timestamp}.json"
            filepath = Path(RESULTS_DIR) / filename
            
            summary = {
                'batch_info': {
                    'timestamp': timestamp,
                    'total_cases': self.stats['total'],
                    'successful': self.stats['successful'],
                    'failed': self.stats['failed'],
                    'captcha_encountered': self.stats['captcha_encountered'],
                    'invalid_cnr': self.stats['invalid_cnr'],
                    'case_not_found': self.stats['case_not_found'],
                    'start_time': self.stats['start_time'],
                    'end_time': self.stats['end_time'],
                    'duration_seconds': (self.stats['end_time'] - self.stats['start_time']).total_seconds() if self.stats['start_time'] and self.stats['end_time'] else None
                },
                'results': self.results
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Batch summary saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving batch summary: {str(e)}")
            return ""
    
    def print_progress(self, current: int, total: int, cnr: str, status: str):
        """Print progress information"""
        percentage = (current / total) * 100
        progress_bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
        
        print(f"\r[{progress_bar}] {percentage:.1f}% ({current}/{total}) | {cnr} | {status}", end="", flush=True)
    
    def print_final_stats(self):
        """Print final processing statistics"""
        print(f"\n\n{'='*60}")
        print("📊 BATCH PROCESSING COMPLETED")
        print(f"{'='*60}")
        print(f"Total Cases: {self.stats['total']}")
        print(f"✅ Successful: {self.stats['successful']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"🤖 CAPTCHA Encountered: {self.stats['captcha_encountered']}")
        print(f"⚠️  Invalid CNR: {self.stats['invalid_cnr']}")
        print(f"🔍 Case Not Found: {self.stats['case_not_found']}")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"⏱️  Total Duration: {duration}")
            print(f"📈 Average Time per Case: {duration.total_seconds() / self.stats['total']:.2f} seconds")
        
        success_rate = (self.stats['successful'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        print(f"{'='*60}\n")
    
    def process_batch(self, cnr_list: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of CNR numbers"""
        if not cnr_list:
            logger.error("No CNR numbers to process")
            return []
        
        self.stats['total'] = len(cnr_list)
        self.stats['start_time'] = datetime.now()
        
        print(f"\n🚀 Starting batch processing of {len(cnr_list)} cases...")
        print(f"🌐 Browser will be {'hidden' if self.headless else 'visible'}")
        
        # Initialize scraper
        self.scraper = AutomatedECourtsScraper(headless=self.headless)
        
        try:
            for i, cnr in enumerate(cnr_list, 1):
                self.print_progress(i, len(cnr_list), cnr, "Processing...")
                
                # Scrape the case
                result = self.scraper.scrape_case_with_retry(cnr)
                self.results.append(result)
                
                # Update statistics
                if result['status'] == 'found':
                    self.stats['successful'] += 1
                    status = "✅ Found"
                elif result['status'] == 'captcha_detected':
                    self.stats['captcha_encountered'] += 1
                    self.stats['failed'] += 1
                    status = "🤖 CAPTCHA"
                elif result['status'] == 'invalid_cnr':
                    self.stats['invalid_cnr'] += 1
                    self.stats['failed'] += 1
                    status = "❌ Invalid"
                elif result['status'] == 'case_not_found':
                    self.stats['case_not_found'] += 1
                    self.stats['failed'] += 1
                    status = "🔍 Not Found"
                else:
                    self.stats['failed'] += 1
                    status = "❌ Error"
                
                self.print_progress(i, len(cnr_list), cnr, status)
            
            self.stats['end_time'] = datetime.now()
            
            # Save batch summary
            summary_file = self.save_batch_summary()
            
            # Print final statistics
            self.print_final_stats()
            
            if summary_file:
                print(f"📁 Batch summary saved to: {summary_file}")
            
            return self.results
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Batch processing interrupted by user.")
            self.stats['end_time'] = datetime.now()
            return self.results
        except Exception as e:
            logger.error(f"Unexpected error in batch processing: {str(e)}")
            self.stats['end_time'] = datetime.now()
            return self.results
        finally:
            if self.scraper:
                self.scraper.close()


def main():
    """Main batch processing function"""
    print("\n" + "="*60)
    print("🏛️  Indian eCourts Automated Case Scraper - Batch Mode")
    print("="*60)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        cnr_file = sys.argv[1]
        headless = '--headless' in sys.argv
        
        if not Path(cnr_file).exists():
            print(f"❌ CNR file not found: {cnr_file}")
            return
        
        processor = BatchProcessor(headless=headless)
        cnr_list = processor.load_cnr_list_from_file(cnr_file)
        
        if cnr_list:
            processor.process_batch(cnr_list)
        else:
            print("❌ No valid CNR numbers found in file")
    
    else:
        # Interactive mode
        print("Choose input method:")
        print("1. Load from file")
        print("2. Enter manually")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            filepath = input("Enter path to CNR file: ").strip()
            headless = input("Run in headless mode? (y/n): ").strip().lower() == 'y'
            
            processor = BatchProcessor(headless=headless)
            cnr_list = processor.load_cnr_list_from_file(filepath)
            
            if cnr_list:
                processor.process_batch(cnr_list)
            else:
                print("❌ No valid CNR numbers found in file")
        
        elif choice == '2':
            headless = input("Run in headless mode? (y/n): ").strip().lower() == 'y'
            
            processor = BatchProcessor(headless=headless)
            cnr_list = processor.load_cnr_list_from_input()
            
            if cnr_list:
                processor.process_batch(cnr_list)
            else:
                print("❌ No CNR numbers entered")
        
        elif choice == '3':
            print("👋 Goodbye!")
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
