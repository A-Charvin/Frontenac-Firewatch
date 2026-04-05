#!/usr/bin/env python3
"""
Frontenac Fire Status Poller - With Manual Override for Frontenac Islands
Run: python fire_status.py
"""

import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# --- MANUAL OVERRIDE SETTINGS ---
# Toggle the ban status for Frontenac Islands here (since no automated source yet)
FRONTENAC_ISLANDS_STATUS = "OFF"  # Change to "ON" or "OFF" as needed
FRONTENAC_ISLANDS_URL = "https://www.frontenacislands.ca/en/living-here/fire-and-emergency-services.aspx"

MUNICIPALITIES = {
    "north_frontenac": {
        "url": "https://www.northfrontenac.com/en/our-community/burn-ban-status-and-fire-danger.aspx",
        "type": "image"
    },
    "central_frontenac": {
        "url": "https://www.centralfrontenac.com/en/living-here/burn-permits.aspx",
        "type": "text"
    },
    "south_frontenac": {
        "url": "https://www.southfrontenac.net/living-in-south-frontenac/fire-and-emergency-services/fire-ban-status/",
        "type": "text"
    },
    "frontenac_islands": {
        "url": FRONTENAC_ISLANDS_URL,
        "type": "manual"  # Special type for manual override
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FireStatusMonitor/0.6"
}

def fetch_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None

def extract_north_frontenac(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = {"ban": None}
    
    for container in soup.find_all('div', class_='lb-imageBox'):
        img = container.find('img')
        if not img:
            continue
        src = img.get('src', '').lower()
        
        if 'fire-ban-on.jpg' in src:
            result["ban"] = "ON"
        elif 'fire-ban-off.jpg' in src:
            result["ban"] = "OFF"
        if result["ban"]:
            break
    return result

def extract_central_frontenac(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    for h2 in soup.find_all('h2'):
        text = h2.get_text().strip().lower()
        
        if text in ['current burn ban status', 'burn ban status', 'status']:
            continue
            
        if any(kw in text for kw in ['lifted', '/off', ' no ban', 'not a ban', 'legal to burn']):
            return {"ban": "OFF"}
        elif any(kw in text for kw in ['active', ' on', 'in effect', 'prohibited', 'ban in place', 'ban is active']):
            return {"ban": "ON"}
            
    return {"ban": "UNKNOWN:NO_STATUS_HEADING_FOUND"}

def extract_south_frontenac(html):
    soup = BeautifulSoup(html, 'html.parser')
    heading = soup.find('h3')
    
    if not heading:
        return {"ban": "SELECTOR_NOT_FOUND"}
    
    text = heading.get_text().strip().lower()
    
    if 'not a fire ban' in text or 'ban was lifted' in text or 'no ban' in text:
        return {"ban": "OFF"}
    elif 'fire ban in place' in text or ('level' in text and 'ban' in text and 'lifted' not in text):
        return {"ban": "ON"}
        
    return {"ban": f"UNKNOWN:{text[:80]}"}

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
        return extract_north_frontenac(html)
    elif key == 'central_frontenac':
        return extract_central_frontenac(html)
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
