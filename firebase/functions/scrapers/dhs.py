"""
DHS.gov scraper for immigration-related press releases and announcements.

Targets:
- DHS Press Releases: https://www.dhs.gov/news-releases/press-releases
"""

import logging
import time
from typing import List, Dict
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Respectful scraping: 2-second delay between requests
SCRAPE_DELAY_SECONDS = 2

# Request headers
HEADERS = {
    'User-Agent': 'Migravio Immigration Assistant (migravio.ai) - Policy Monitoring',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Immigration-related keywords for filtering
IMMIGRATION_KEYWORDS = [
    'immigration', 'immigrant', 'visa', 'uscis', 'cbp', 'ice',
    'asylum', 'refugee', 'border', 'deportation', 'removal',
    'green card', 'naturalization', 'citizenship', 'h-1b', 'opt',
    'daca', 'tps', 'parole', 'inadmissible', 'admissible',
]


def scrape_dhs_news() -> List[Dict[str, str]]:
    """
    Scrape DHS press releases, filtering for immigration-related content.

    Returns:
        List of news items with structure:
        {
            'title': str,
            'date': str (ISO format),
            'summary': str,
            'url': str,
            'source': 'dhs_news'
        }
    """
    url = 'https://www.dhs.gov/news-releases/press-releases'
    logger.info(f"Scraping DHS news from {url}")

    try:
        with httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        news_items = []

        # DHS news items are typically in article elements or list items
        articles = soup.select('article.node, .view-content article, .views-row')

        if not articles:
            # Fallback: find all articles on page
            articles = soup.find_all('article', limit=30)

        logger.info(f"Found {len(articles)} potential DHS news items")

        for article in articles[:30]:  # Check up to 30 most recent
            try:
                # Extract title
                title_elem = article.find(['h2', 'h3', 'h4'])
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Filter for immigration relevance
                if not is_immigration_related(title):
                    # Check summary/teaser for immigration keywords
                    teaser_elem = article.find(class_=lambda x: x and any(t in x.lower() for t in ['teaser', 'summary', 'description']))
                    if teaser_elem:
                        teaser_text = teaser_elem.get_text(strip=True)
                        if not is_immigration_related(teaser_text):
                            continue  # Skip non-immigration content
                    else:
                        continue

                # Extract link
                link_elem = title_elem.find('a') or article.find('a')
                if link_elem and link_elem.get('href'):
                    article_url = link_elem['href']
                    if not article_url.startswith('http'):
                        article_url = f"https://www.dhs.gov{article_url}"
                else:
                    article_url = url

                # Extract date
                date_elem = article.find(class_=lambda x: x and 'date' in x.lower())
                if not date_elem:
                    date_elem = article.find('time')

                article_date = None
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    try:
                        article_date = parse_dhs_date(date_text)
                    except Exception as e:
                        logger.warning(f"Could not parse date '{date_text}': {e}")
                        article_date = datetime.now().isoformat()
                else:
                    article_date = datetime.now().isoformat()

                # Extract summary
                summary_elem = article.find(class_=lambda x: x and any(term in x.lower() for term in ['summary', 'teaser', 'description']))
                if not summary_elem:
                    summary_elem = article.find('p')

                summary = summary_elem.get_text(strip=True) if summary_elem else title

                news_items.append({
                    'title': title,
                    'date': article_date,
                    'summary': summary[:500],  # Limit summary length
                    'url': article_url,
                    'source': 'dhs_news',
                })

            except Exception as e:
                logger.warning(f"Error parsing DHS news item: {e}")
                continue

        logger.info(f"Successfully scraped {len(news_items)} immigration-related DHS news items")
        time.sleep(SCRAPE_DELAY_SECONDS)
        return news_items

    except httpx.HTTPError as e:
        logger.error(f"HTTP error scraping DHS news: {e}")
        raise
    except Exception as e:
        logger.error(f"Error scraping DHS news: {e}")
        raise


def is_immigration_related(text: str) -> bool:
    """
    Check if text contains immigration-related keywords.

    Args:
        text: Text to check

    Returns:
        True if text contains immigration keywords, False otherwise
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in IMMIGRATION_KEYWORDS)


def parse_dhs_date(date_str: str) -> str:
    """
    Parse various DHS date formats into ISO format.

    DHS uses formats like:
    - "March 13, 2026"
    - "03/13/2026"
    - "2026-03-13T00:00:00"

    Returns:
        ISO format date string
    """
    from datetime import datetime

    # Clean up the string
    date_str = date_str.strip()

    # Remove common prefixes
    for prefix in ['Released:', 'Posted:', 'Date:', 'Published:']:
        if date_str.startswith(prefix):
            date_str = date_str[len(prefix):].strip()

    # Try different date formats
    formats = [
        '%B %d, %Y',           # March 13, 2026
        '%b %d, %Y',           # Mar 13, 2026
        '%m/%d/%Y',            # 03/13/2026
        '%Y-%m-%d',            # 2026-03-13
        '%Y-%m-%dT%H:%M:%S',   # 2026-03-13T00:00:00
        '%d %B %Y',            # 13 March 2026
        '%d %b %Y',            # 13 Mar 2026
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
