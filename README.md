# Frontenac Firewatch

Automated monitoring of municipal burn ban status across the Frontenac County townships.

## How It Works
1. **Data Collection**: A Python script fetches municipal web pages and extracts current fire ban status.
2. **Normalization**: Status text and images are parsed into a unified schema (`ON`, `OFF`, or `UNKNOWN`).
3. **Automation**: GitHub Actions runs the script every 6 hours, commits changes only when status values shift.
4. **Visualization**: A lightweight MapLibre frontend reads the generated `fire_status.json` and renders color-coded township boundaries.

## Architecture
```
Municipal Websites --> Python Scraper --> fire_status.json --> MapLibre Frontend
        ^                      ^                    ^                ^
   HTML/Image parsing    BeautifulSoup + requests   JSON data       WebGL rendering
```

## Local Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the scraper to generate initial data:
   ```bash
   python fire_status.py
   ```
4. Serve the frontend:
   ```bash
   python -m http.server 8000
   ```
5. Open `http://localhost:8000` in your browser.

## Automated Pipeline
- The workflow triggers every 6 hours UTC.

## Data Sources
- **North Frontenac**: Image-based status indicators parsed from page containers.
- **Central Frontenac**: Text-based heading extraction from dynamic content blocks.
- **South Frontenac**: Text-based heading extraction from emergency services page.
- **Frontenac Islands**: Manual toggle. //Semi Automatic
- **Township Boundaries**: ArcGIS FeatureServer (`Township_Boundaries`).
- **Fire Danger Rating (Planned)**: LIO Open Data WMS layer.

## File Structure
- `fire_status.py` : Core scraper and status normalization logic.
- `fire_status.json` : Auto-generated output used by the frontend.
- `index.html` : Standalone MapLibre visualization.
- `.github/workflows/` : Scheduled automation configuration.

## Notes
- Frontenac Islands status is updated manually.
- Municipal websites update at irregular intervals. The 6-hour polling schedule captures changes without excessive server requests.
- If a page structure changes, the extractor functions in `fire_status.py` require selector updates.
- The frontend uses raw `fire_status.json` from the repository. For public deployment, GitHub Pages or a static host will serve the files automatically.
- This is a concept in the end, I will take lessions from this and make this into an experience builder or dashboard app so that it can be controlled internally, reducing friction.
