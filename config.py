"""
Configuration settings for Indian eCourts Automated Case Scraper
"""

import random
from typing import Dict, List

# Browser settings
HEADLESS = False
BROWSER_TIMEOUT = 20
MAX_RETRIES = 3
WINDOW_SIZE = (1920, 1080)

# Rate limiting settings
MIN_DELAY_BETWEEN_REQUESTS = 2
MAX_DELAY_BETWEEN_REQUESTS = 5
DELAY_BETWEEN_CASES = 5
REQUEST_TIMEOUT = 30

# URLs
HIGH_COURT_URL = "https://hcservices.ecourts.gov.in/hcservices/"
DISTRICT_COURT_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

# User agents for rotation (realistic browser user agents)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# State code mapping for CNR parsing
STATE_CODES = {
    'GJ': 'Gujarat',
    'DL': 'Delhi', 
    'MH': 'Maharashtra',
    'KA': 'Karnataka',
    'TN': 'Tamil Nadu',
    'UP': 'Uttar Pradesh',
    'RJ': 'Rajasthan',
    'WB': 'West Bengal',
    'MP': 'Madhya Pradesh',
    'AP': 'Andhra Pradesh',
    'BR': 'Bihar',
    'OR': 'Odisha',
    'KL': 'Kerala',
    'AS': 'Assam',
    'JH': 'Jharkhand',
    'CT': 'Chhattisgarh',
    'UT': 'Uttarakhand',
    'HP': 'Himachal Pradesh',
    'PB': 'Punjab',
    'HR': 'Haryana',
    'JK': 'Jammu and Kashmir',
    'LD': 'Lakshadweep',
    'MN': 'Manipur',
    'ML': 'Meghalaya',
    'MZ': 'Mizoram',
    'NL': 'Nagaland',
    'PY': 'Puducherry',
    'SK': 'Sikkim',
    'TR': 'Tripura',
    'AR': 'Arunachal Pradesh',
    'GA': 'Goa',
    'CH': 'Chandigarh',
    'DN': 'Dadra and Nagar Haveli',
    'DD': 'Daman and Diu'
}

# Court code patterns for High Courts (commonly used codes)
HIGH_COURT_CODES = {
    'GJ': ['AH'],  # Ahmedabad
    'DL': ['01'],  # Delhi
    'MH': ['01', '02', '03'],  # Mumbai, Nagpur, Aurangabad
    'KA': ['01'],  # Bengaluru
    'TN': ['01'],  # Chennai
    'UP': ['01', '02'],  # Allahabad, Lucknow
    'RJ': ['01'],  # Jodhpur
    'WB': ['01'],  # Kolkata
    'MP': ['01'],  # Jabalpur
    'AP': ['01'],  # Hyderabad
    'BR': ['01'],  # Patna
    'OR': ['01'],  # Cuttack
    'KL': ['01'],  # Kochi
    'AS': ['01'],  # Guwahati
    'JH': ['01'],  # Ranchi
    'CT': ['01'],  # Bilaspur
    'UT': ['01'],  # Nainital
    'HP': ['01'],  # Shimla
    'PB': ['01'],  # Chandigarh
    'HR': ['01'],  # Chandigarh
}

# Output settings
RESULTS_DIR = "results"
CASE_FILE_PREFIX = "case_"
BATCH_FILE_PREFIX = "batch_summary_"
LOG_LEVEL = "INFO"

# CAPTCHA detection settings
CAPTCHA_KEYWORDS = [
    "captcha", "verification", "robot", "security check",
    "please verify", "enter the code", "human verification"
]

# Browser configuration options
BROWSER_OPTIONS = {
    'disable-blink-features': 'AutomationControlled',
    'disable-dev-shm-usage': True,
    'no-sandbox': True,
    'disable-gpu': False,
    'disable-extensions': False,
    'disable-plugins': False,
    'disable-images': False,
    'disable-javascript': False,
    'disable-web-security': False,
    'allow-running-insecure-content': True,
    'disable-features': 'VizDisplayCompositor'
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': 'scraper.log',
            'mode': 'a',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

def get_random_user_agent() -> str:
    """Get a random user agent from the list"""
    return random.choice(USER_AGENTS)

def get_random_delay() -> float:
    """Get a random delay between min and max delay values"""
    return random.uniform(MIN_DELAY_BETWEEN_REQUESTS, MAX_DELAY_BETWEEN_REQUESTS)

def validate_state_code(state_code: str) -> bool:
    """Validate if state code exists in mapping"""
    return state_code.upper() in STATE_CODES

def get_state_name(state_code: str) -> str:
    """Get state name from state code"""
    return STATE_CODES.get(state_code.upper(), "Unknown")

def is_high_court_code(state_code: str, court_code: str) -> bool:
    """Check if the combination indicates a High Court"""
    return court_code in HIGH_COURT_CODES.get(state_code.upper(), [])

# CNR validation patterns
CNR_PATTERN = r'^[A-Z]{2}[A-Z0-9]{2}[0-9]{12}$'
CNR_LENGTH = 16

# Error messages
ERROR_MESSAGES = {
    'invalid_cnr': 'Invalid CNR format. Must be 16 characters: SSCCNNNNNNNNNNNN',
    'unsupported_state': 'Unsupported state code in CNR',
    'captcha_detected': 'CAPTCHA detected on page. Manual intervention required.',
    'network_error': 'Network error occurred during scraping',
    'timeout_error': 'Request timed out. Server may be slow or unresponsive.',
    'parsing_error': 'Error parsing case data from webpage',
    'browser_error': 'Browser initialization or navigation error',
    'case_not_found': 'Case not found in court database'
}

# Success messages
SUCCESS_MESSAGES = {
    'case_found': 'Case found and data extracted successfully',
    'processing_complete': 'Case processing completed',
    'batch_complete': 'Batch processing completed successfully'
}
