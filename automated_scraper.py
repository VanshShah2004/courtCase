"""
Indian eCourts Automated Case Scraper
Main scraper class with modular architecture
"""

import re
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from config import (
    HEADLESS, BROWSER_TIMEOUT, MAX_RETRIES, WINDOW_SIZE,
    MIN_DELAY_BETWEEN_REQUESTS, MAX_DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_CASES,
    HIGH_COURT_URL, DISTRICT_COURT_URL, USER_AGENTS, STATE_CODES,
    BROWSER_OPTIONS, CAPTCHA_KEYWORDS, CNR_PATTERN, CNR_LENGTH,
    ERROR_MESSAGES, SUCCESS_MESSAGES, RESULTS_DIR, CASE_FILE_PREFIX,
    get_random_user_agent, get_random_delay, validate_state_code,
    get_state_name, is_high_court_code
)


class CNRValidator:
    """Handles CNR validation and parsing logic"""
    
    @staticmethod
    def validate_cnr(cnr: str) -> bool:
        """Validate 16-character CNR format"""
        if not cnr or len(cnr) != CNR_LENGTH:
            return False
        
        # Check if CNR matches the pattern SSCCNNNNNNNNNNNN
        if not re.match(CNR_PATTERN, cnr.upper()):
            return False
            
        return True
    
    @staticmethod
    def parse_cnr(cnr: str) -> Dict[str, str]:
        """Parse CNR into components"""
        if not CNRValidator.validate_cnr(cnr):
            raise ValueError(ERROR_MESSAGES['invalid_cnr'])
        
        cnr_upper = cnr.upper()
        state_code = cnr_upper[:2]
        court_code = cnr_upper[2:4]
        unique_number = cnr_upper[4:]
        
        return {
            'state_code': state_code,
            'court_code': court_code,
            'unique_number': unique_number,
            'full_cnr': cnr_upper
        }
    
    @staticmethod
    def detect_court_type(cnr: str) -> Dict[str, str]:
        """Detect court type and extract court information"""
        parsed = CNRValidator.parse_cnr(cnr)
        state_code = parsed['state_code']
        court_code = parsed['court_code']
        
        if not validate_state_code(state_code):
            raise ValueError(f"Unsupported state code: {state_code}")
        
        state_name = get_state_name(state_code)
        is_high_court = is_high_court_code(state_code, court_code)
        
        return {
            'state_code': state_code,
            'state_name': state_name,
            'court_code': court_code,
            'unique_number': parsed['unique_number'],
            'court_type': 'High Court' if is_high_court else 'District Court',
            'is_high_court': is_high_court
        }


class BrowserManager:
    """Handles browser initialization and configuration"""
    
    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def initialize_browser(self) -> webdriver.Chrome:
        """Initialize Chrome browser with stealth configuration"""
        try:
            options = Options()
            
            # Basic options
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument(f'--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Stealth options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Set user agent
            user_agent = get_random_user_agent()
            options.add_argument(f'--user-agent={user_agent}')
            
            # Additional browser options from config
            for key, value in BROWSER_OPTIONS.items():
                if isinstance(value, bool):
                    if value:
                        options.add_argument(f'--{key}')
                else:
                    options.add_argument(f'--{key}={value}')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute stealth script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set up WebDriverWait
            self.wait = WebDriverWait(self.driver, BROWSER_TIMEOUT)
            
            logging.info("Browser initialized successfully")
            return self.driver
            
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise WebDriverException(f"Browser initialization failed: {str(e)}")
    
    def close_browser(self):
        """Close browser and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.warning(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
                self.wait = None


class CaptchaDetector:
    """Handles CAPTCHA detection on web pages"""
    
    @staticmethod
    def detect_captcha(driver: webdriver.Chrome) -> bool:
        """Detect if CAPTCHA is present on the current page"""
        try:
            page_source = driver.page_source.lower()
            
            # Check for CAPTCHA keywords
            for keyword in CAPTCHA_KEYWORDS:
                if keyword in page_source:
                    return True
            
            # Check for common CAPTCHA elements
            captcha_selectors = [
                "input[name*='captcha']",
                "input[id*='captcha']",
                "img[src*='captcha']",
                ".captcha",
                "#captcha",
                "iframe[src*='captcha']"
            ]
            
            for selector in captcha_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.warning(f"Error detecting CAPTCHA: {str(e)}")
            return False


class DataExtractor:
    """Handles data extraction and parsing from HTML"""
    
    @staticmethod
    def parse_case_details_from_html(soup: BeautifulSoup, cnr: str) -> Dict[str, Any]:
        """Extract structured case data from HTML"""
        case_data = {
            'cnr': cnr,
            'status': 'found',
            'case_number': None,
            'case_type': None,
            'filing_date': None,
            'registration_date': None,
            'petitioners': [],
            'respondents': [],
            'court_name': None,
            'judge_name': None,
            'next_hearing_date': None,
            'case_stage': None,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Extract case number
            case_number_selectors = [
                'td:contains("Case No") + td',
                'td:contains("Case Number") + td',
                '.case-number',
                '#caseNumber'
            ]
            case_data['case_number'] = DataExtractor._extract_text_by_selectors(soup, case_number_selectors)
            
            # Extract case type
            case_type_selectors = [
                'td:contains("Case Type") + td',
                'td:contains("Nature of Case") + td',
                '.case-type',
                '#caseType'
            ]
            case_data['case_type'] = DataExtractor._extract_text_by_selectors(soup, case_type_selectors)
            
            # Extract filing date
            filing_date_selectors = [
                'td:contains("Filing Date") + td',
                'td:contains("Date of Filing") + td',
                '.filing-date',
                '#filingDate'
            ]
            case_data['filing_date'] = DataExtractor._extract_text_by_selectors(soup, filing_date_selectors)
            
            # Extract registration date
            reg_date_selectors = [
                'td:contains("Registration Date") + td',
                'td:contains("Date of Registration") + td',
                '.registration-date',
                '#registrationDate'
            ]
            case_data['registration_date'] = DataExtractor._extract_text_by_selectors(soup, reg_date_selectors)
            
            # Extract petitioners
            petitioner_selectors = [
                'td:contains("Petitioner") + td',
                'td:contains("Plaintiff") + td',
                '.petitioner',
                '#petitioner'
            ]
            petitioners_text = DataExtractor._extract_text_by_selectors(soup, petitioner_selectors)
            if petitioners_text:
                case_data['petitioners'] = [p.strip() for p in petitioners_text.split(',') if p.strip()]
            
            # Extract respondents
            respondent_selectors = [
                'td:contains("Respondent") + td',
                'td:contains("Defendant") + td',
                '.respondent',
                '#respondent'
            ]
            respondents_text = DataExtractor._extract_text_by_selectors(soup, respondent_selectors)
            if respondents_text:
                case_data['respondents'] = [r.strip() for r in respondents_text.split(',') if r.strip()]
            
            # Extract court name
            court_selectors = [
                'td:contains("Court Name") + td',
                'td:contains("Court") + td',
                '.court-name',
                '#courtName'
            ]
            case_data['court_name'] = DataExtractor._extract_text_by_selectors(soup, court_selectors)
            
            # Extract judge name
            judge_selectors = [
                'td:contains("Judge") + td',
                'td:contains("Presiding Officer") + td',
                '.judge-name',
                '#judgeName'
            ]
            case_data['judge_name'] = DataExtractor._extract_text_by_selectors(soup, judge_selectors)
            
            # Extract next hearing date
            hearing_selectors = [
                'td:contains("Next Hearing") + td',
                'td:contains("Hearing Date") + td',
                '.next-hearing',
                '#nextHearing'
            ]
            case_data['next_hearing_date'] = DataExtractor._extract_text_by_selectors(soup, hearing_selectors)
            
            # Extract case stage
            stage_selectors = [
                'td:contains("Case Stage") + td',
                'td:contains("Stage") + td',
                '.case-stage',
                '#caseStage'
            ]
            case_data['case_stage'] = DataExtractor._extract_text_by_selectors(soup, stage_selectors)
            
        except Exception as e:
            logging.error(f"Error parsing case details: {str(e)}")
            case_data['status'] = 'parsing_error'
        
        return case_data
    
    @staticmethod
    def _extract_text_by_selectors(soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle CSS contains selector manually
                    tag_part = selector.split(':contains(')[0]
                    text_part = selector.split(':contains(')[1].rstrip(')').strip('"\'')
                    
                    elements = soup.select(tag_part)
                    for element in elements:
                        if text_part.lower() in element.get_text().lower():
                            next_td = element.find_next_sibling('td')
                            if next_td:
                                return next_td.get_text().strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text().strip()
            except Exception:
                continue
        return None


class AutomatedECourtsScraper:
    """Main scraper class for Indian eCourts case information"""
    
    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self.browser_manager = BrowserManager(headless)
        self.captcha_detector = CaptchaDetector()
        self.data_extractor = DataExtractor()
        self.driver = None
        self.wait = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure results directory exists
        Path(RESULTS_DIR).mkdir(exist_ok=True)
    
    def _initialize_browser(self):
        """Initialize browser if not already done"""
        if not self.driver:
            self.driver = self.browser_manager.initialize_browser()
            self.wait = WebDriverWait(self.driver, BROWSER_TIMEOUT)
    
    def _rate_limit(self):
        """Implement intelligent delays between requests"""
        delay = get_random_delay()
        self.logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
        time.sleep(delay)
    
    def _detect_captcha(self) -> bool:
        """Detect if CAPTCHA is present"""
        return self.captcha_detector.detect_captcha(self.driver)
    
    def _save_case_result(self, case_data: Dict[str, Any]) -> str:
        """Save case result to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{CASE_FILE_PREFIX}{case_data['cnr']}_{timestamp}.json"
            filepath = Path(RESULTS_DIR) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Case result saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving case result: {str(e)}")
            return ""
    
    def validate_cnr(self, cnr: str) -> bool:
        """Validate CNR format"""
        return CNRValidator.validate_cnr(cnr)
    
    def detect_court_type(self, cnr: str) -> Dict[str, str]:
        """Detect court type and extract court information"""
        return CNRValidator.detect_court_type(cnr)
    
    def scrape_case_with_retry(self, cnr: str, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
        """Main scraping method with retry logic"""
        self.logger.info(f"Starting to scrape CNR: {cnr}")
        
        # Validate CNR
        if not self.validate_cnr(cnr):
            error_result = {
                'cnr': cnr,
                'status': 'invalid_cnr',
                'error': ERROR_MESSAGES['invalid_cnr'],
                'scraped_at': datetime.now().isoformat()
            }
            return error_result
        
        # Detect court type
        try:
            court_info = self.detect_court_type(cnr)
            self.logger.info(f"Detected court type: {court_info['court_type']} in {court_info['state_name']}")
        except ValueError as e:
            error_result = {
                'cnr': cnr,
                'status': 'unsupported_state',
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
            return error_result
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries} for CNR: {cnr}")
                
                result = self.scrape_single_case(cnr)
                
                if result['status'] == 'found':
                    self.logger.info(f"Successfully scraped CNR: {cnr}")
                    return result
                elif result['status'] == 'captcha_detected':
                    self.logger.warning(f"CAPTCHA detected for CNR: {cnr}. Skipping.")
                    return result
                else:
                    self.logger.warning(f"Failed attempt {attempt + 1} for CNR: {cnr}. Status: {result['status']}")
                    
            except Exception as e:
                self.logger.error(f"Error in attempt {attempt + 1} for CNR: {cnr}: {str(e)}")
                
            # Wait before retry
            if attempt < max_retries - 1:
                retry_delay = (attempt + 1) * 2
                self.logger.info(f"Waiting {retry_delay} seconds before retry")
                time.sleep(retry_delay)
        
        # All retries failed
        error_result = {
            'cnr': cnr,
            'status': 'max_retries_exceeded',
            'error': f'Failed after {max_retries} attempts',
            'detected_court_info': court_info,
            'scraped_at': datetime.now().isoformat()
        }
        
        self.logger.error(f"All retry attempts failed for CNR: {cnr}")
        return error_result
    
    def scrape_single_case(self, cnr: str) -> Dict[str, Any]:
        """Single case processing with accurate extraction"""
        try:
            # Initialize browser if needed
            self._initialize_browser()
            
            # Detect court type
            court_info = self.detect_court_type(cnr)
            
            # Route to appropriate court service
            if court_info['is_high_court']:
                self.logger.info(f"Scraping High Court case: {cnr}")
                result = self._scrape_high_court_automated(cnr)
            else:
                self.logger.info(f"Scraping District Court case: {cnr}")
                result = self._scrape_district_court_automated(cnr, court_info['state_name'])
            
            if result:
                result['detected_court_info'] = court_info
                result['cnr'] = cnr
                
                # Save result
                self._save_case_result(result)
                
                return result
            else:
                return {
                    'cnr': cnr,
                    'status': 'case_not_found',
                    'error': ERROR_MESSAGES['case_not_found'],
                    'detected_court_info': court_info,
                    'scraped_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error scraping case {cnr}: {str(e)}")
            return {
                'cnr': cnr,
                'status': 'error',
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
    
    def _scrape_high_court_automated(self, cnr: str) -> Optional[Dict[str, Any]]:
        """Handle High Court website navigation and scraping"""
        try:
            self.logger.info(f"Navigating to High Court website: {HIGH_COURT_URL}")
            self.driver.get(HIGH_COURT_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check for CAPTCHA
            if self._detect_captcha():
                self.logger.warning("CAPTCHA detected on High Court website")
                return {
                    'status': 'captcha_detected',
                    'error': ERROR_MESSAGES['captcha_detected']
                }
            
            # Find CNR input field and submit
            cnr_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "cnr"))
            )
            cnr_input.clear()
            cnr_input.send_keys(cnr)
            
            # Find and click search button
            search_button = self.driver.find_element(By.XPATH, "//input[@type='submit' or @value='Search']")
            search_button.click()
            
            # Wait for results
            time.sleep(5)
            
            # Check for CAPTCHA again after search
            if self._detect_captcha():
                self.logger.warning("CAPTCHA detected after search")
                return {
                    'status': 'captcha_detected',
                    'error': ERROR_MESSAGES['captcha_detected']
                }
            
            # Parse the results page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            case_data = self.data_extractor.parse_case_details_from_html(soup, cnr)
            
            return case_data
            
        except TimeoutException:
            self.logger.error("Timeout while scraping High Court")
            return None
        except Exception as e:
            self.logger.error(f"Error scraping High Court: {str(e)}")
            return None
    
    def _scrape_district_court_automated(self, cnr: str, state: str) -> Optional[Dict[str, Any]]:
        """Handle District Court website navigation and scraping"""
        try:
            self.logger.info(f"Navigating to District Court website: {DISTRICT_COURT_URL}")
            self.driver.get(DISTRICT_COURT_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check for CAPTCHA
            if self._detect_captcha():
                self.logger.warning("CAPTCHA detected on District Court website")
                return {
                    'status': 'captcha_detected',
                    'error': ERROR_MESSAGES['captcha_detected']
                }
            
            # Find and fill CNR input
            cnr_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "cnr"))
            )
            cnr_input.clear()
            cnr_input.send_keys(cnr)
            
            # Find and click search button
            search_button = self.driver.find_element(By.XPATH, "//input[@type='submit' or @value='Search']")
            search_button.click()
            
            # Wait for results
            time.sleep(5)
            
            # Check for CAPTCHA again after search
            if self._detect_captcha():
                self.logger.warning("CAPTCHA detected after search")
                return {
                    'status': 'captcha_detected',
                    'error': ERROR_MESSAGES['captcha_detected']
                }
            
            # Parse the results page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            case_data = self.data_extractor.parse_case_details_from_html(soup, cnr)
            
            return case_data
            
        except TimeoutException:
            self.logger.error("Timeout while scraping District Court")
            return None
        except Exception as e:
            self.logger.error(f"Error scraping District Court: {str(e)}")
            return None
    
    def close(self):
        """Close browser and clean up resources"""
        if self.driver:
            self.browser_manager.close_browser()
            self.driver = None
            self.wait = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
