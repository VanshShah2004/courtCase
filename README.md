# 🏛️ Indian eCourts Automated Case Scraper

A comprehensive Python scraper for extracting case information from Indian eCourts websites using Selenium with visible browser operation.

## Features

- ✅ **Interactive Browser Operation** - Visible browser window for user observation
- ✅ **Real-time Data Scraping** - Extract case details from eCourts websites
- ✅ **Multi-Court Support** - Both High Court and District Court cases
- ✅ **Intelligent CNR Validation** - Automatic court type detection
- ✅ **CAPTCHA Detection** - Detect (but not solve) CAPTCHAs
- ✅ **Retry Logic** - Automatic retry with intelligent delays
- ✅ **Batch Processing** - Process multiple CNR numbers
- ✅ **Modular Architecture** - Clean, maintainable code structure

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Interactive Mode (Single Case)

```bash
cd courtCase
python run_interactive.py
```

### 3. Batch Processing

```bash
cd courtCase
python run_batch.py cnr_list.txt
```

## CNR Format

```
SSCCNNNNNNNNNNNN
SS = State Code (2 chars)
CC = Court Code (2 chars)  
NN = Unique Number (12 digits)
```

### Example CNR Numbers:
- `GJAH010053852024` - Gujarat High Court
- `DL01HC001234567` - Delhi High Court
- `MH01DC005678901` - Maharashtra District Court

## Supported States

The scraper supports all major Indian states including Gujarat, Delhi, Maharashtra, Karnataka, Tamil Nadu, Uttar Pradesh, Rajasthan, West Bengal, Madhya Pradesh, Andhra Pradesh, Bihar, Odisha, Kerala, Assam, Jharkhand, Chhattisgarh, Uttarakhand, Himachal Pradesh, Punjab, Haryana, and more.

## Usage Examples

### Single Case Processing

```python
from automated_scraper import AutomatedECourtsScraper

scraper = AutomatedECourtsScraper(headless=False)
result = scraper.scrape_case_with_retry("GJAH010053852024")
print(f"Status: {result['status']}")
scraper.close()
```

### Context Manager Usage

```python
with AutomatedECourtsScraper(headless=False) as scraper:
    result = scraper.scrape_case_with_retry("GJAH010053852024")
    print(f"Case found: {result['status'] == 'found'}")
```

### Batch Processing

```python
from run_batch import BatchProcessor

processor = BatchProcessor(headless=False)
cnr_list = ["GJAH010053852024", "DL01HC001234567"]
results = processor.process_batch(cnr_list)
```

## Output Format

Each scraped case returns structured data:

```json
{
    "cnr": "GJAH010053852024",
    "status": "found",
    "case_number": "12345/2024",
    "case_type": "Civil Appeal",
    "filing_date": "2024-01-15",
    "registration_date": "2024-01-16",
    "petitioners": ["John Doe"],
    "respondents": ["Jane Smith"],
    "court_name": "Gujarat High Court",
    "judge_name": "Justice ABC",
    "next_hearing_date": "2024-12-01",
    "case_stage": "Arguments",
    "detected_court_info": {
        "state_code": "GJ",
        "state": "Gujarat",
        "court_code": "AH",
        "court_type": "High Court"
    },
    "scraped_at": "2024-10-17T11:36:31.393672"
}
```

## File Structure

```
courtCase/
├── automated_scraper.py      # Main scraper class
├── run_interactive.py        # Interactive runner
├── run_batch.py             # Batch processor
├── config.py                # Configuration settings
├── example_usage.py         # Usage examples
├── cnr_list.txt            # Sample CNR numbers
└── results/                # Output directory
```

## Configuration

Key settings in `config.py`:

- `HEADLESS`: Browser visibility (False for visible)
- `MAX_RETRIES`: Number of retry attempts
- `MIN_DELAY_BETWEEN_REQUESTS`: Rate limiting delays
- `BROWSER_TIMEOUT`: Page load timeout

## Error Handling

The scraper handles various scenarios:

- ❌ **Invalid CNR Format** - Validates 16-character format
- 🤖 **CAPTCHA Detection** - Skips cases with CAPTCHAs
- 🔍 **Case Not Found** - Handles missing cases gracefully
- ⚠️ **Network Errors** - Retry logic with exponential backoff
- 🕐 **Timeouts** - Configurable timeout handling

## Legal Compliance

- ✅ Respectful scraping with rate limiting
- ✅ No CAPTCHA solving (detection only)
- ✅ Visible browser operation for transparency
- ✅ Appropriate delays between requests
- ✅ Error handling for server protection

## Requirements

- Python 3.7+
- Chrome browser
- Internet connection
- Required Python packages (see requirements.txt)

## Running Examples

```bash
cd courtCase
python example_usage.py
```

## Support

For issues or questions:
1. Check the example usage files
2. Review the configuration settings
3. Ensure all dependencies are installed
4. Verify CNR format is correct

## License

This project is for educational and research purposes. Please ensure compliance with website terms of service and applicable laws.
