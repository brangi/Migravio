"""
AI-powered summarization of policy changes using OpenRouter.

Generates concise summaries and extracts affected visa types from
scraped government content.
"""

import logging
import os
from typing import List, Dict, Optional
from openai import AsyncOpenAI
import asyncio

logger = logging.getLogger(__name__)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

# Model selection: use Haiku for cost efficiency
MODEL_NAME = 'anthropic/claude-haiku-4-5'

# Visa types we track
VISA_TYPES = [
    'H-1B', 'H-4', 'H-2A', 'H-2B',
    'L-1', 'L-2',
    'F-1', 'F-2', 'OPT', 'CPT', 'STEM OPT',
    'J-1', 'J-2',
    'O-1', 'O-2',
    'E-1', 'E-2', 'E-3',
    'TN',
    'Green Card', 'EB-1', 'EB-2', 'EB-3', 'EB-4', 'EB-5',
    'Family-Based', 'IR-1', 'IR-2', 'IR-5', 'F-1', 'F-2', 'F-3', 'F-4',
    'Asylum', 'Refugee',
    'TPS', 'DACA',
    'U Visa', 'T Visa',
    'K-1', 'K-3',
    'Citizenship', 'Naturalization',
]


async def summarize_changes(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Generate AI summaries for changed/new policy items.

    Args:
        items: List of scraped items (new or changed)

    Returns:
        List of items with added AI summaries and extracted visa types
    """
    if not items:
        return []

    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set, skipping AI summarization")
        # Return items with basic processing
        return [
            {
                **item,
                'aiSummary': item.get('summary', '')[:500],
                'affectsVisaTypes': extract_visa_types_basic(item),
            }
            for item in items
        ]

    logger.info(f"Generating AI summaries for {len(items)} items")

    # Process items concurrently (but limit concurrency to avoid rate limits)
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests

    async def process_item(item: Dict[str, str]) -> Dict[str, str]:
        async with semaphore:
            return await summarize_single_item(item)

    results = await asyncio.gather(
        *[process_item(item) for item in items],
        return_exceptions=True
    )

    # Filter out exceptions and return successful results
    summarized = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error summarizing item {i}: {result}")
            # Fallback to basic processing
            summarized.append({
                **items[i],
                'aiSummary': items[i].get('summary', '')[:500],
                'affectsVisaTypes': extract_visa_types_basic(items[i]),
            })
        else:
            summarized.append(result)

    logger.info(f"Completed AI summarization for {len(summarized)} items")
    return summarized


async def summarize_single_item(item: Dict[str, str]) -> Dict[str, str]:
    """
    Generate AI summary for a single item.

    Args:
        item: Scraped item dict

    Returns:
        Item with 'aiSummary' and 'affectsVisaTypes' added
    """
    client = AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    title = item.get('title', '')
    content = item.get('summary', '')
    source = item.get('source', '')

    # Construct prompt for summarization
    prompt = f"""You are analyzing a U.S. immigration policy update from {source}.

Title: {title}

Content: {content}

Please provide:
1. A clear, concise 2-3 sentence summary for immigrants explaining what changed and why it matters
2. List which visa types are affected (choose from: {', '.join(VISA_TYPES[:20])}, or "All" if broadly applicable)

Format your response as:
SUMMARY: [your summary here]
VISA_TYPES: [comma-separated list]

Be accurate and specific. If unclear, say "May affect: [types]" rather than guessing."""

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
            max_tokens=300,
            temperature=0.3,  # Lower temperature for more consistent output
        )

        ai_response = response.choices[0].message.content.strip()

        # Parse the response
        summary, visa_types = parse_ai_response(ai_response)

        logger.info(f"Generated summary for: {title[:50]}...")

        return {
            **item,
            'aiSummary': summary,
            'affectsVisaTypes': visa_types,
        }

    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        # Fallback to basic extraction
        return {
            **item,
            'aiSummary': content[:500],
            'affectsVisaTypes': extract_visa_types_basic(item),
        }


def parse_ai_response(response: str) -> tuple[str, List[str]]:
    """
    Parse AI response to extract summary and visa types.

    Args:
        response: Raw AI response text

    Returns:
        Tuple of (summary, visa_types_list)
    """
    lines = response.strip().split('\n')

    summary = ''
    visa_types = []

    for line in lines:
        line = line.strip()

        if line.startswith('SUMMARY:'):
            summary = line[8:].strip()
        elif line.startswith('VISA_TYPES:'):
            types_str = line[11:].strip()
            # Split by comma and clean up
            visa_types = [t.strip() for t in types_str.split(',') if t.strip()]

    # Fallback if parsing failed
    if not summary:
        summary = response[:500]

    if not visa_types:
        # Try to extract from full response
        visa_types = extract_visa_types_basic({'summary': response})

    return summary, visa_types


def extract_visa_types_basic(item: Dict[str, str]) -> List[str]:
    """
    Basic keyword-based extraction of visa types from text.

    Fallback when AI is not available or fails.

    Args:
        item: Item dict with 'title' and 'summary'

    Returns:
        List of visa types found in the text
    """
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()

    found_types = []

    for visa_type in VISA_TYPES:
        # Check for exact match or common variations
        check_patterns = [
            visa_type.lower(),
            visa_type.lower().replace('-', ' '),
            visa_type.lower().replace('-', ''),
        ]

        if any(pattern in text for pattern in check_patterns):
            found_types.append(visa_type)

    # Special cases
    if 'employment-based' in text or 'employment based' in text:
        if 'EB-1' not in found_types:
            found_types.extend(['EB-1', 'EB-2', 'EB-3'])

    if 'family-based' in text or 'family based' in text:
        if 'Family-Based' not in found_types:
            found_types.append('Family-Based')

    if 'all visa' in text or 'all applicants' in text:
        found_types = ['All']

    # Remove duplicates while preserving order
    seen = set()
    unique_types = []
    for t in found_types:
        if t not in seen:
            seen.add(t)
            unique_types.append(t)

    return unique_types if unique_types else ['General']


# Synchronous wrapper for use in Cloud Functions
def summarize_changes_sync(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Synchronous wrapper for summarize_changes.

    Args:
        items: List of items to summarize

    Returns:
        List of summarized items
    """
    return asyncio.run(summarize_changes(items))
