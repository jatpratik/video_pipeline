"""
Asset Retriever (Phase 2.5)
==============================
Searches the web for relevant images/diagrams for visual segments,
takes screenshots using Playwright, and stores them locally.

Supports: DuckDuckGo (default, free), SerpAPI, Google Custom Search.
Segments that don't need images (e.g. kinetic_text) are skipped.
Fallback: CSS/SVG generation if no image is found.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from urllib.parse import quote_plus

logger = logging.getLogger("video_pipeline.agents.asset_retriever")

# Strategies that benefit from real-world images
SEARCHABLE_STRATEGIES = {
    "diagram_flow",
    "metaphor_animation",
    "ui_mockup",
    "image_montage",
    "data_visualization",
}


# ======================================================================
# Public API
# ======================================================================

def retrieve_assets(
    visual_map: list[dict],
    assets_dir: Path,
    search_provider: str = "duckduckgo",
    search_api_key: str = "",
    google_cse_id: str = "",
    max_results: int = 3,
    screenshot_width: int = 1280,
    screenshot_height: int = 800,
) -> list[dict]:
    """
    Enrich visual_map segments with retrieved image assets.

    For each segment whose visual_strategy is in SEARCHABLE_STRATEGIES,
    search the web for relevant images, screenshot them, and store locally.

    Args:
        visual_map:        List of visual segment dicts from Phase 2.
        assets_dir:        Directory to store downloaded/screenshotted images.
        search_provider:   "duckduckgo" | "serpapi" | "google_cse"
        search_api_key:    API key for serpapi or google_cse.
        google_cse_id:     Google Custom Search Engine ID.
        max_results:       Max images to retrieve per segment.
        screenshot_width:  Viewport width for screenshots.
        screenshot_height: Viewport height for screenshots.

    Returns:
        Updated visual_map with 'assets' and 'asset_fallback' fields.
    """
    assets_dir.mkdir(parents=True, exist_ok=True)

    searchable = [
        seg for seg in visual_map
        if seg.get("visual_strategy") in SEARCHABLE_STRATEGIES
    ]

    logger.info(
        f"Phase 2.5: Asset Retrieval — "
        f"{len(searchable)}/{len(visual_map)} segments need images"
    )

    if not searchable:
        # Mark all segments as CSS/SVG fallback
        for seg in visual_map:
            seg.setdefault("assets", [])
            seg.setdefault("asset_fallback", "css_svg")
        return visual_map

    # Run async retrieval
    asyncio.run(
        _retrieve_all_async(
            searchable, assets_dir,
            search_provider, search_api_key, google_cse_id,
            max_results, screenshot_width, screenshot_height,
        )
    )

    # Mark non-searchable segments
    for seg in visual_map:
        if seg.get("visual_strategy") not in SEARCHABLE_STRATEGIES:
            seg.setdefault("assets", [])
            seg.setdefault("asset_fallback", "css_svg")

    return visual_map


# ======================================================================
# Async retrieval engine
# ======================================================================

async def _retrieve_all_async(
    segments: list[dict],
    assets_dir: Path,
    search_provider: str,
    search_api_key: str,
    google_cse_id: str,
    max_results: int,
    screenshot_width: int,
    screenshot_height: int,
) -> None:
    """Retrieve assets for all searchable segments."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for seg in segments:
            segment_id = seg.get("segment_id", "unknown")
            query = _build_search_query(seg)

            logger.info(f"  Searching for {segment_id}: \"{query}\"")

            try:
                image_urls = search_images(
                    query=query,
                    provider=search_provider,
                    api_key=search_api_key,
                    cse_id=google_cse_id,
                    max_results=max_results,
                )
            except Exception as e:
                logger.warning(f"  Search failed for {segment_id}: {e}")
                image_urls = []

            assets = []
            for idx, img_info in enumerate(image_urls[:max_results]):
                url = img_info.get("url", "")
                if not url:
                    continue

                output_path = assets_dir / f"{segment_id}_{idx}.png"
                try:
                    success = await _screenshot_url(
                        browser, url, output_path,
                        screenshot_width, screenshot_height,
                    )
                    if success:
                        assets.append({
                            "asset_id": f"{segment_id}_{idx}",
                            "source_url": url,
                            "local_path": str(output_path.relative_to(assets_dir.parent)),
                            "search_query": query,
                            "title": img_info.get("title", ""),
                            "type": "screenshot",
                        })
                        logger.info(f"    ✓ Saved {output_path.name}")
                except Exception as e:
                    logger.warning(f"    ✗ Screenshot failed for {url}: {e}")

            seg["assets"] = assets
            seg["asset_fallback"] = "css_svg" if not assets else "none"

            if not assets:
                logger.info(f"    No assets found — will use CSS/SVG fallback")

        await browser.close()


# ======================================================================
# Search API abstraction
# ======================================================================

def search_images(
    query: str,
    provider: str = "duckduckgo",
    api_key: str = "",
    cse_id: str = "",
    max_results: int = 3,
) -> list[dict]:
    """
    Search for images using the configured provider.

    Returns:
        List of dicts with keys: url, title, thumbnail_url
    """
    if provider == "serpapi":
        return _search_serpapi(query, api_key, max_results)
    elif provider == "google_cse":
        return _search_google_cse(query, api_key, cse_id, max_results)
    else:  # duckduckgo (default)
        return _search_duckduckgo(query, max_results)


def _search_duckduckgo(query: str, max_results: int = 3) -> list[dict]:
    """
    Search DuckDuckGo for images using their instant answer API.
    Free, no API key required.
    """
    import requests

    # DuckDuckGo image search via their API
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"DuckDuckGo API error: {e}")
        # Fallback: try DuckDuckGo image search scraping
        return _search_duckduckgo_images(query, max_results)

    results = []

    # Check for direct image result
    if data.get("Image"):
        results.append({
            "url": data["Image"],
            "title": data.get("Heading", query),
            "thumbnail_url": data.get("Image", ""),
        })

    # Check related topics for images
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Icon", {}).get("URL"):
            results.append({
                "url": topic["Icon"]["URL"],
                "title": topic.get("Text", "")[:100],
                "thumbnail_url": topic["Icon"]["URL"],
            })

    if not results:
        return _search_duckduckgo_images(query, max_results)

    return results[:max_results]


def _search_duckduckgo_images(query: str, max_results: int = 3) -> list[dict]:
    """
    Fallback: search DuckDuckGo images via their image search endpoint.
    """
    import requests

    url = "https://duckduckgo.com/"
    params = {"q": query, "iax": "images", "ia": "images"}

    try:
        session = requests.Session()
        # First get the token
        resp = session.get(url, params={"q": query}, timeout=10)
        # Extract vqd token
        vqd_match = re.search(r'vqd=["\']([^"\']+)', resp.text)
        if not vqd_match:
            logger.warning("Could not extract DuckDuckGo search token")
            return []

        vqd = vqd_match.group(1)

        # Now search images
        img_url = "https://duckduckgo.com/i.js"
        img_params = {
            "l": "us-en",
            "o": "json",
            "q": query,
            "vqd": vqd,
            "f": ",,,,,",
            "p": "1",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://duckduckgo.com/",
        }

        resp = session.get(img_url, params=img_params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", [])[:max_results]:
            results.append({
                "url": item.get("image", ""),
                "title": item.get("title", ""),
                "thumbnail_url": item.get("thumbnail", ""),
            })

        return results

    except Exception as e:
        logger.warning(f"DuckDuckGo image search error: {e}")
        return []


def _search_serpapi(query: str, api_key: str, max_results: int = 3) -> list[dict]:
    """Search using SerpAPI (requires API key)."""
    import requests

    if not api_key:
        logger.warning("SerpAPI key not configured, skipping search")
        return []

    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "tbm": "isch",
        "api_key": api_key,
        "num": max_results,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("images_results", [])[:max_results]:
            results.append({
                "url": item.get("original", ""),
                "title": item.get("title", ""),
                "thumbnail_url": item.get("thumbnail", ""),
            })
        return results
    except Exception as e:
        logger.warning(f"SerpAPI error: {e}")
        return []


def _search_google_cse(
    query: str, api_key: str, cse_id: str, max_results: int = 3
) -> list[dict]:
    """Search using Google Custom Search Engine (requires API key + CSE ID)."""
    import requests

    if not api_key or not cse_id:
        logger.warning("Google CSE credentials not configured, skipping search")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": min(max_results, 10),
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("items", [])[:max_results]:
            results.append({
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "thumbnail_url": item.get("image", {}).get("thumbnailLink", ""),
            })
        return results
    except Exception as e:
        logger.warning(f"Google CSE error: {e}")
        return []


# ======================================================================
# Playwright screenshot
# ======================================================================

async def _screenshot_url(
    browser,
    url: str,
    output_path: Path,
    width: int = 1280,
    height: int = 800,
) -> bool:
    """Open URL in headless Chromium, take screenshot, return success."""
    context = await browser.new_context(
        viewport={"width": width, "height": height},
    )
    page = await context.new_page()

    try:
        await page.goto(url, wait_until="networkidle", timeout=15000)
        await page.screenshot(path=str(output_path), full_page=False)
        return True
    except Exception as e:
        logger.debug(f"Screenshot error for {url}: {e}")
        return False
    finally:
        await page.close()
        await context.close()


# ======================================================================
# Helpers
# ======================================================================

def _build_search_query(segment: dict) -> str:
    """Build a concise search query from a visual segment."""
    parts = []

    # Use key_elements first
    elements = segment.get("key_elements", [])
    if elements:
        parts.extend(elements[:3])

    # Add strategy-specific terms
    strategy = segment.get("visual_strategy", "")
    if strategy == "diagram_flow":
        parts.append("diagram")
    elif strategy == "ui_mockup":
        parts.append("UI screenshot")
    elif strategy == "data_visualization":
        parts.append("chart infographic")

    # Fallback to visual_description keywords
    if not parts:
        desc = segment.get("visual_description", "")
        # Extract key nouns from description
        words = desc.split()[:6]
        parts.extend(words)

    query = " ".join(parts[:5])  # Cap at 5 terms
    return query if query.strip() else segment.get("teaching_goal", "educational diagram")
