"""
USCIS.gov scraper for policy updates, news alerts, and processing times.

Targets:
- News/Alerts: https://www.uscis.gov/news/alerts
- Policy Manual: https://www.uscis.gov/policy-manual/updates
- Processing Times: https://egov.uscis.gov/processing-times/
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Respectful scraping: 2-second delay between requests
SCRAPE_DELAY_SECONDS = 2

# Request headers to identify ourselves
HEADERS = {
    'User-Agent': 'Migravio Immigration Assistant (migravio.com) - Policy Monitoring',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_uscis_alerts() -> List[Dict[str, str]]:
    """
    Scrape USCIS news alerts page.

    Returns:
        List of alert items with structure:
        {
            'title': str,
            'date': str (ISO format),
            'summary': str,
            'url': str,
            'source': 'uscis_alerts'
        }
    """
    url = 'https://www.uscis.gov/news/alerts'
    logger.info(f"Scraping USCIS alerts from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        alerts = []

        # USCIS alerts are typically in article elements or specific divs
        # This selector may need adjustment based on actual page structure
        alert_items = soup.select('article.views-row, .view-content article, .views-field')

        if not alert_items:
            # Fallback: try finding articles with news content
            alert_items = soup.find_all('article', limit=20)

        logger.info(f"Found {len(alert_items)} potential alert items")

        for item in alert_items[:20]:  # Limit to 20 most recent
            try:
                # Extract title
                title_elem = item.find(['h2', 'h3', 'h4'], class_=lambda x: x and ('title' in x.lower() or 'headline' in x.lower()))
                if not title_elem:
                    title_elem = item.find(['h2', 'h3', 'h4'])

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Extract link
                link_elem = title_elem.find('a') or item.find('a')
                if link_elem and link_elem.get('href'):
                    article_url = link_elem['href']
                    if not article_url.startswith('http'):
                        article_url = f"https://www.uscis.gov{article_url}"
                else:
                    article_url = url

                # Extract date
                date_elem = item.find(class_=lambda x: x and 'date' in x.lower())
                if not date_elem:
                    date_elem = item.find('time')

                article_date = None
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        # Try to parse date (USCIS uses various formats)
                        article_date = parse_uscis_date(date_text)
                    except Exception as e:
                        logger.warning(f"Could not parse date '{date_text}': {e}")
                        article_date = datetime.now().isoformat()
                else:
                    article_date = datetime.now().isoformat()

                # Extract summary
                summary_elem = item.find(class_=lambda x: x and any(term in x.lower() for term in ['summary', 'teaser', 'description']))
                if not summary_elem:
                    # Fallback: get first paragraph
                    summary_elem = item.find('p')

                summary = summary_elem.get_text(strip=True) if summary_elem else title

                alerts.append({
                    'title': title,
                    'date': article_date,
                    'summary': summary[:500],  # Limit summary length
                    'url': article_url,
                    'source': 'uscis_alerts',
                })

            except Exception as e:
                logger.warning(f"Error parsing alert item: {e}")
                continue

        logger.info(f"Successfully scraped {len(alerts)} USCIS alerts")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return alerts

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping USCIS alerts: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping USCIS alerts: {e}")
        raise


def scrape_uscis_policy_manual() -> List[Dict[str, str]]:
    """
    Scrape USCIS Policy Manual updates page.

    Returns:
        List of policy update items with same structure as alerts.
    """
    url = 'https://www.uscis.gov/policy-manual/updates'
    logger.info(f"Scraping USCIS policy manual updates from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        updates = []

        # Policy updates are typically in a table or list format
        update_items = soup.select('table.views-table tbody tr, .view-content .views-row')

        if not update_items:
            # Fallback: look for any structured list
            update_items = soup.find_all('tr', limit=20)

        logger.info(f"Found {len(update_items)} potential policy update items")

        for item in update_items[:20]:
            try:
                # Extract title/description
                title_elem = item.find('td', class_=lambda x: x and 'title' in x.lower()) or item.find('a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Extract link
                link_elem = item.find('a')
                if link_elem and link_elem.get('href'):
                    update_url = link_elem['href']
                    if not update_url.startswith('http'):
                        update_url = f"https://www.uscis.gov{update_url}"
                else:
                    update_url = url

                # Extract date
                date_elem = item.find('td', class_=lambda x: x and 'date' in x.lower())
                if not date_elem:
                    date_elem = item.find('time')

                update_date = None
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        update_date = parse_uscis_date(date_text)
                    except Exception as e:
                        logger.warning(f"Could not parse date '{date_text}': {e}")
                        update_date = datetime.now().isoformat()
                else:
                    update_date = datetime.now().isoformat()

                # Extract volume/part info if available
                volume_elem = item.find('td', class_=lambda x: x and 'volume' in x.lower())
                volume_info = volume_elem.get_text(strip=True) if volume_elem else ''

                summary = f"{volume_info} - {title}" if volume_info else title

                updates.append({
                    'title': title,
                    'date': update_date,
                    'summary': summary[:500],
                    'url': update_url,
                    'source': 'uscis_policy_manual',
                })

            except Exception as e:
                logger.warning(f"Error parsing policy update item: {e}")
                continue

        logger.info(f"Successfully scraped {len(updates)} policy manual updates")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return updates

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping USCIS policy manual: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping USCIS policy manual: {e}")
        raise


def scrape_uscis_processing_times() -> List[Dict[str, str]]:
    """
    Scrape USCIS processing times page for significant updates.

    This is primarily for detecting when processing time data changes,
    not for parsing all individual case types.

    Returns:
        List with a single item representing the processing times page state.
    """
    url = 'https://egov.uscis.gov/processing-times/'
    logger.info(f"Scraping USCIS processing times from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract last updated date if available
        updated_elem = soup.find(text=lambda t: t and 'last updated' in t.lower())
        update_date = datetime.now().isoformat()

        if updated_elem:
            try:
                date_text = updated_elem.strip()
                update_date = parse_uscis_date(date_text)
            except Exception as e:
                logger.warning(f"Could not parse processing times date: {e}")

        # Get a summary of available form types
        form_options = soup.select('select[name="form"] option')
        available_forms = [opt.get_text(strip=True) for opt in form_options if opt.get('value')]

        summary = f"Processing times data available for {len(available_forms)} form types"
        if available_forms:
            summary += f": {', '.join(available_forms[:5])}"
            if len(available_forms) > 5:
                summary += f" and {len(available_forms) - 5} more"

        result = [{
            'title': 'USCIS Processing Times Data',
            'date': update_date,
            'summary': summary,
            'url': url,
            'source': 'uscis_processing_times',
        }]

        logger.info("Successfully scraped USCIS processing times page")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping USCIS processing times: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping USCIS processing times: {e}")
        raise


def parse_uscis_date(date_str: str) -> str:
    """
    Parse various USCIS date formats into ISO format.

    USCIS uses formats like:
    - "March 13, 2026"
    - "03/13/2026"
    - "2026-03-13"
    - "Last Updated: March 13, 2026"

    Returns:
        ISO format date string (YYYY-MM-DD)
    """
    from datetime import datetime

    # Clean up the string
    date_str = date_str.strip()

    # Remove common prefixes
    for prefix in ['Last Updated:', 'Updated:', 'Posted:', 'Date:']:
        if date_str.startswith(prefix):
            date_str = date_str[len(prefix):].strip()

    # Try different date formats
    formats = [
        '%B %d, %Y',      # March 13, 2026
        '%b %d, %Y',      # Mar 13, 2026
        '%m/%d/%Y',       # 03/13/2026
        '%Y-%m-%d',       # 2026-03-13
        '%d %B %Y',       # 13 March 2026
        '%d %b %Y',       # 13 Mar 2026
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
