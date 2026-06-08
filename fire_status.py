#!/usr/bin/env python3
"""
Frontenac Fire Status Poller - WordPress Migration Update
Run: python fire_status.py
"""

import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# --- MANUAL OVERRIDE SETTINGS ---
# Toggle the ban status for Frontenac Islands here (since no automated source yet)
FRONTENAC_ISLANDS_STATUS = "OFF"  # Change to "ON" or "OFF" as needed
FRONTENAC_ISLANDS_URL = "https://www.frontenacislands.ca/living-here/fire-and-emergency-services/"

MUNICIPALITIES = {
    "north_frontenac": {
        "url": "https://www.northfrontenac.com/our-community/burn-ban-status-and-fire-danger/",
        "type": "image",
        "image_pattern_on": "Fire-Ban-ON",  # Look for this in img src/alt
        "page_check_keywords": ["burn ban", "fire danger", "north frontenac"]
    },
    "central_frontenac": {
        "url": "https://www.centralfrontenac.com/living-here/burn-permits-and-status/",
        "type": "image",
        "image_pattern_on": "burn-ban-on-icon",
        "page_check_keywords": ["burn permit", "fire status", "central frontenac"]
    },
    "south_frontenac": {
        "url": "https://www.southfrontenac.net/living-in-south-frontenac/fire-and-emergency-services/open-air-fire-rules-fire-ban-status/",
        "type": "text"
    },
    "frontenac_islands": {
        "url": FRONTENAC_ISLANDS_URL,
        "type": "manual"  # Special type for manual override
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FireStatusMonitor/0.8"
}

def fetch_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None

def extract_image_status(html, pattern_on, page_check_keywords=None):
    """
    Simple, robust extractor: look for the ON pattern.
    If found → ON. If not found + page looks valid → OFF.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Look for the ON pattern in any image src or alt attribute
    for img in soup.find_all('img'):
        src = img.get('src', '').lower()
        alt = img.get('alt', '').lower()
        combined = src + ' ' + alt
        
        if pattern_on.lower() in combined:
            return {"ban": "ON"}
    
    # 2. ON pattern not found - verify page is valid before assuming OFF
    if page_check_keywords:
        page_text = soup.get_text(separator=' ', strip=True).lower()
        if not any(kw.lower() in page_text for kw in page_check_keywords):
            # Page looks broken or significantly changed
            return {"ban": "UNKNOWN:PAGE_CONTENT_UNEXPECTED"}
    
    # 3. Page looks valid, ON image not present → assume OFF
    return {"ban": "OFF"}

def extract_south_frontenac(html):
    """Text-based extractor for South Frontenac (still working)"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Target the specific paragraph used on South Frontenac's site
    status_p = soup.find('p', class_='intro')
    if status_p:
        text = status_p.get_text(strip=True).lower()
        if 'not a fire ban' in text or 'no ban' in text or 'lifted' in text:
            return {"ban": "OFF"}
        elif 'fire ban in place' in text or 'ban active' in text:
            return {"ban": "ON"}
            
    # Fallback: Search entire page text
    page_text = soup.get_text(separator=' ', strip=True).lower()
    if any(kw in page_text for kw in ['there is not a fire ban', 'no ban', 'ban was lifted', 'ban is off']):
        return {"ban": "OFF"}
    elif any(kw in page_text for kw in ['fire ban in place', 'ban is active', 'ban is on']):
        return {"ban": "ON"}
        
    return {"ban": "UNKNOWN:STATUS_NOT_FOUND"}

def poll_municipality(key, config):
    print(f"\n[{key}] Fetching {config['url']}...")
    
    # Handle manual override municipalities
    if config.get("type") == "manual":
        print(f"  → Using manual override: ban={FRONTENAC_ISLANDS_STATUS}")
        return {"ban": FRONTENAC_ISLANDS_STATUS}
    
    html = fetch_html(config['url'])
    if not html:
        return {"error": "fetch_failed"}
    
    if config['type'] == 'image':
        return extract_image_status(
            html,
            pattern_on=config.get('image_pattern_on', ''),
            page_check_keywords=config.get('page_check_keywords', [])
        )
    elif key == 'south_frontenac':
        return extract_south_frontenac(html)
    
    return {"error": "unknown_extractor"}

def main():
    print("🔥 Frontenac Fire Status Poller")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "municipalities": {}
    }
    
    for key, config in MUNICIPALITIES.items():
        status = poll_municipality(key, config)
        output["municipalities"][key] = {
            **status,
            "source_url": config["url"]
        }
        print(f"  → Result: {status}")
    
    with open("fire_status.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Output saved to fire_status.json")
    print("\n--- Summary ---")
    for muni, data in output["municipalities"].items():
        print(f"{muni:20} ban: {data.get('ban', 'N/A')}")

if __name__ == "__main__":
    main()
