"""
State Department scraper for visa bulletins and travel advisories.

Targets:
- Visa Bulletin: https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html
- Travel Advisories: https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html/
"""

import logging
import time
from typing import List, Dict
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

# Respectful scraping: 2-second delay between requests
SCRAPE_DELAY_SECONDS = 2

# Request headers
HEADERS = {
    'User-Agent': 'Migravio Immigration Assistant (migravio.com) - Policy Monitoring',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_state_dept_visa_bulletin() -> List[Dict[str, str]]:
    """
    Scrape State Department Visa Bulletin page.

    The Visa Bulletin is published monthly and contains priority date information
    for employment-based and family-based immigration.

    Returns:
        List of visa bulletin items (typically just the current month's bulletin).
    """
    url = 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html'
    logger.info(f"Scraping State Dept Visa Bulletin from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        bulletins = []

        # Look for the current bulletin link/heading
        # The page typically has a prominent link to the current month's bulletin
        current_bulletin = soup.find('a', text=re.compile(r'visa bulletin', re.I))

        if not current_bulletin:
            # Try finding by heading
            current_bulletin = soup.find(['h1', 'h2', 'h3'], text=re.compile(r'visa bulletin', re.I))

        if current_bulletin:
            # Extract month/year from bulletin title
            title = current_bulletin.get_text(strip=True)

            # Extract link if available
            bulletin_url = url
            if current_bulletin.name == 'a' and current_bulletin.get('href'):
                bulletin_url = current_bulletin['href']
                if not bulletin_url.startswith('http'):
                    bulletin_url = f"https://travel.state.gov{bulletin_url}"

            # Try to extract date from title (e.g., "Visa Bulletin for March 2026")
            bulletin_date = extract_bulletin_date(title)

            # Get summary from nearby content
            summary = title
            parent = current_bulletin.find_parent(['div', 'article', 'section'])
            if parent:
                summary_elem = parent.find('p')
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)[:500]

            bulletins.append({
                'title': title,
                'date': bulletin_date,
                'summary': summary,
                'url': bulletin_url,
                'source': 'state_dept_visa_bulletin',
            })

        # Also look for archived bulletins or recent updates
        archive_links = soup.find_all('a', text=re.compile(r'(20\d{2}|bulletin)', re.I), limit=5)

        for link in archive_links:
            try:
                link_text = link.get_text(strip=True)

                # Skip if it's the same as current bulletin
                if bulletins and link_text == bulletins[0]['title']:
                    continue

                link_url = link.get('href', '')
                if link_url and not link_url.startswith('http'):
                    link_url = f"https://travel.state.gov{link_url}"

                bulletin_date = extract_bulletin_date(link_text)

                bulletins.append({
                    'title': link_text,
                    'date': bulletin_date,
                    'summary': link_text,
                    'url': link_url or url,
                    'source': 'state_dept_visa_bulletin',
                })

            except Exception as e:
                logger.warning(f"Error parsing bulletin archive link: {e}")
                continue

        # If no bulletins found, create a placeholder entry
        if not bulletins:
            bulletins.append({
                'title': 'State Department Visa Bulletin',
                'date': datetime.now().isoformat(),
                'summary': 'Monthly visa bulletin with priority dates for employment-based and family-based immigration',
                'url': url,
                'source': 'state_dept_visa_bulletin',
            })

        logger.info(f"Successfully scraped {len(bulletins)} visa bulletin items")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return bulletins[:3]  # Return at most 3 most recent

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping State Dept visa bulletin: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping State Dept visa bulletin: {e}")
        raise


def scrape_state_dept_advisories() -> List[Dict[str, str]]:
    """
    Scrape State Department travel advisories for immigration-relevant updates.

    This focuses on advisories that might affect visa processing or travel
    for immigrants (e.g., embassy closures, processing delays).

    Returns:
        List of relevant advisory items.
    """
    url = 'https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html/'
    logger.info(f"Scraping State Dept travel advisories from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        advisories = []

        # Look for general advisories or updates about visa processing
        # This page structure varies, so we'll look for common patterns
        advisory_items = soup.select('.tsg-rwd-emergency-item, .advisory-item, article')

        if not advisory_items:
            advisory_items = soup.find_all(['article', 'div'], class_=re.compile(r'(advisory|alert|notice)', re.I), limit=10)

        for item in advisory_items[:10]:
            try:
                # Extract title
                title_elem = item.find(['h2', 'h3', 'h4', 'strong'])
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Filter for immigration/visa relevance
                if not is_visa_related(title):
                    summary_elem = item.find('p')
                    if summary_elem:
                        summary_text = summary_elem.get_text(strip=True)
                        if not is_visa_related(summary_text):
                            continue
                    else:
                        continue

                # Extract link
                link_elem = item.find('a')
                advisory_url = url
                if link_elem and link_elem.get('href'):
                    advisory_url = link_elem['href']
                    if not advisory_url.startswith('http'):
                        advisory_url = f"https://travel.state.gov{advisory_url}"

                # Extract date (if available)
                date_elem = item.find(class_=lambda x: x and 'date' in x.lower())
                if not date_elem:
                    date_elem = item.find('time')

                advisory_date = datetime.now().isoformat()
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        advisory_date = parse_state_dept_date(date_text)
                    except Exception as e:
                        logger.warning(f"Could not parse date '{date_text}': {e}")

                # Extract summary
                summary_elem = item.find('p')
                summary = summary_elem.get_text(strip=True)[:500] if summary_elem else title

                advisories.append({
                    'title': title,
                    'date': advisory_date,
                    'summary': summary,
                    'url': advisory_url,
                    'source': 'state_dept_advisories',
                })

            except Exception as e:
                logger.warning(f"Error parsing advisory item: {e}")
                continue

        logger.info(f"Successfully scraped {len(advisories)} relevant State Dept advisories")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return advisories

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping State Dept advisories: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping State Dept advisories: {e}")
        raise


def extract_bulletin_date(text: str) -> str:
    """
    Extract date from visa bulletin title.

    Examples:
    - "Visa Bulletin for March 2026" -> 2026-03-01
    - "March 2026 Visa Bulletin" -> 2026-03-01

    Returns:
        ISO format date string
    """
    from datetime import datetime

    # Look for month and year pattern
    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})'
    match = re.search(month_pattern, text, re.I)

    if match:
        month_str = match.group(1)
        year_str = match.group(2)
        try:
            dt = datetime.strptime(f"{month_str} {year_str}", "%B %Y")
            return dt.isoformat()
        except ValueError:
            pass

    # Fallback to current date
    return datetime.now().isoformat()


def is_visa_related(text: str) -> bool:
    """
    Check if text is related to visa processing or immigration services.

    Args:
        text: Text to check

    Returns:
        True if visa-related, False otherwise
    """
    keywords = [
        'visa', 'immigration', 'embassy', 'consulate', 'passport',
        'processing', 'application', 'interview', 'appointment',
        'immigrant', 'nonimmigrant', 'waiver', 'petition',
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


def parse_state_dept_date(date_str: str) -> str:
    """
    Parse various State Dept date formats into ISO format.

    Returns:
        ISO format date string
    """
    from datetime import datetime

    # Clean up the string
    date_str = date_str.strip()

    # Try different date formats
    formats = [
        '%B %d, %Y',           # March 13, 2026
        '%b %d, %Y',           # Mar 13, 2026
        '%m/%d/%Y',            # 03/13/2026
        '%Y-%m-%d',            # 2026-03-13
        '%Y-%m-%dT%H:%M:%S',   # 2026-03-13T00:00:00
        '%d %B %Y',            # 13 March 2026
        '%B %Y',               # March 2026
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue

    # If all parsing fails, return current date
    logger.warning(f"Could not parse date '{date_str}', using current date")
    return datetime.now().isoformat()
