"""
Scrape all aggregator project pages to extract structural elements.
Uses Selenium for JavaScript rendering.
"""

import csv
import json
import time
import re
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

OUTPUT_DIR = Path(__file__).parent / "scraped_pages"
OUTPUT_DIR.mkdir(exist_ok=True)

# URLs from CSV
PAGES = [
    ("difc-residences.ae", "https://difc-residences.ae/projects/jumeirah-residences-emirates-towers"),
    ("sobha-central.ae", "https://sobha-central.ae/projects/the-tranquil-sobha-central-szr-dubai"),
    ("dubaimaritime-city.ae", "https://dubaimaritime-city.ae/projects/anwa-aria"),
    ("rashid-yachts-marina.ae", "https://rashid-yachts-marina.ae/project/sera-rym-city-walk"),
    ("city-walk-property.ae", "https://www.city-walk-property.ae/project/city-walk-crestlane"),
    ("dubaislands.ae", "https://dubaislands.ae/projects/agua-residences"),
    ("dubai-creek-living.ae", "https://www.dubai-creek-living.ae/project/albero"),
    ("dubaihills-property.ae", "https://www.dubaihills-property.ae/project/hillsedge"),
    ("urbanvillas-dubaisouth.ae", "https://www.urbanvillas-dubaisouth.ae/project/hayat-townhomes-dubai-south-properties"),
    ("saudi-estates.com", "https://www.saudi-estates.com/project/neptune"),
    ("ras-al-khaimah-properties.ae", "https://www.ras-al-khaimah-properties.ae/project/mirasol-2-north-harbour-ras-al-khaimah"),
    ("urban-luxury.penthouse.ae", "https://urban-luxury.penthouse.ae/project/eden-house-dubai-hills"),
    ("tilalalghaf-maf.ae", "https://www.tilalalghaf-maf.ae/project/elan"),
    ("luxury-villas-dubai.ae-ru", "https://www.luxury-villas-dubai.ae/ru/project/morocco"),
    ("sobha-hartland-2.ae", "https://sobha-hartland-2.ae/project/skyvue-stellar"),
    ("dubai-harbour-property.ae", "https://www.dubai-harbour-property.ae/project/south-beach"),
    ("the-valley-villas.ae", "https://www.the-valley-villas.ae/project/elva"),
    ("luxury-collection.ae", "https://www.luxury-collection.ae/project/sky-edition"),
    ("sharjah-residences.ae", "https://sharjah-residences.ae/project/gem-residences"),
    ("bloom-living.ae", "https://bloom-living.ae/project/bloom-living-granada"),
    ("luxury-villas-dubai.ae", "https://www.luxury-villas-dubai.ae/project/grand-polo-club-and-resort"),
    ("capital.luxury", "https://capital.luxury/projects/jacob-co-beachfront-living-by-ohana"),
]

def setup_driver():
    """Setup headless Chrome driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def extract_text_content(element):
    """Extract visible text from element."""
    try:
        text = element.text.strip()
        return text if text else None
    except:
        return None

def extract_page_structure(driver, url, site_name):
    """Extract structural elements from a project page."""
    result = {
        "site": site_name,
        "url": url,
        "status": "success",
        "sections": [],
        "headings": [],
        "meta": {},
        "content_lengths": {},
        "errors": []
    }

    try:
        print(f"  Loading page...")
        driver.get(url)
        time.sleep(3)  # Wait for JS rendering

        # Extract meta tags
        try:
            title = driver.title
            result["meta"]["title"] = title
            result["meta"]["title_length"] = len(title) if title else 0
        except:
            pass

        try:
            meta_desc = driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
            desc = meta_desc.get_attribute("content")
            result["meta"]["description"] = desc
            result["meta"]["description_length"] = len(desc) if desc else 0
        except:
            pass

        # Extract all headings
        for tag in ["h1", "h2", "h3", "h4"]:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for el in elements:
                text = extract_text_content(el)
                if text:
                    result["headings"].append({
                        "tag": tag,
                        "text": text[:200],  # Truncate
                        "length": len(text)
                    })

        # Try to identify sections by common patterns
        section_selectors = [
            ("section", "section"),
            ("div[class*='section']", "div.section"),
            ("div[class*='block']", "div.block"),
            ("div[class*='container']", "div.container"),
            ("div[class*='wrapper']", "div.wrapper"),
        ]

        for selector, name in section_selectors:
            try:
                sections = driver.find_elements(By.CSS_SELECTOR, selector)
                for i, sec in enumerate(sections[:20]):  # Limit to 20
                    sec_data = {
                        "type": name,
                        "index": i,
                        "classes": sec.get_attribute("class") or "",
                        "id": sec.get_attribute("id") or "",
                    }

                    # Get section text length
                    text = extract_text_content(sec)
                    if text:
                        sec_data["text_length"] = len(text)
                        sec_data["text_preview"] = text[:100]

                    # Get headings within section
                    sec_headings = []
                    for tag in ["h1", "h2", "h3"]:
                        hs = sec.find_elements(By.TAG_NAME, tag)
                        for h in hs:
                            ht = extract_text_content(h)
                            if ht:
                                sec_headings.append({"tag": tag, "text": ht[:100]})
                    sec_data["headings"] = sec_headings

                    if sec_data.get("text_length", 0) > 50:  # Only meaningful sections
                        result["sections"].append(sec_data)
            except Exception as e:
                result["errors"].append(f"Section extraction ({name}): {str(e)[:100]}")

        # Look for specific content patterns
        patterns = {
            "hero": ["hero", "banner", "header", "intro"],
            "about": ["about", "overview", "description"],
            "amenities": ["amenities", "features", "facilities"],
            "payment": ["payment", "plan", "price", "pricing"],
            "location": ["location", "map", "area", "neighborhood"],
            "developer": ["developer", "builder", "company"],
            "faq": ["faq", "question", "accordion"],
            "gallery": ["gallery", "images", "photos", "slider"],
            "floor_plans": ["floor", "plan", "layout", "unit"],
            "contact": ["contact", "form", "inquiry", "register"],
        }

        detected_sections = {}
        page_source = driver.page_source.lower()

        for section_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in page_source:
                    detected_sections[section_type] = True
                    break

        result["detected_patterns"] = list(detected_sections.keys())

        # Take screenshot
        screenshot_path = OUTPUT_DIR / f"{site_name}.png"
        driver.save_screenshot(str(screenshot_path))
        result["screenshot"] = str(screenshot_path)

        # Get page height for full-page context
        result["page_height"] = driver.execute_script("return document.body.scrollHeight")

    except TimeoutException:
        result["status"] = "timeout"
        result["errors"].append("Page load timeout (30s)")
    except WebDriverException as e:
        result["status"] = "error"
        result["errors"].append(f"WebDriver error: {str(e)[:200]}")
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Unknown error: {str(e)[:200]}")

    return result

def main():
    print("=" * 70)
    print("PROJECT PAGE SCRAPER")
    print("=" * 70)

    driver = setup_driver()
    all_results = {}

    try:
        for i, (site_name, url) in enumerate(PAGES, 1):
            print(f"\n[{i}/{len(PAGES)}] Scraping: {site_name}")
            print(f"  URL: {url}")

            result = extract_page_structure(driver, url, site_name)
            all_results[site_name] = result

            if result["status"] == "success":
                print(f"  Status: OK")
                print(f"  Headings found: {len(result['headings'])}")
                print(f"  Sections found: {len(result['sections'])}")
                print(f"  Patterns detected: {result['detected_patterns']}")
            else:
                print(f"  Status: {result['status']}")
                print(f"  Errors: {result['errors']}")

            # Small delay between requests
            time.sleep(2)

    finally:
        driver.quit()

    # Save results
    output_path = OUTPUT_DIR / "page_structures.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'=' * 70}")
    print(f"Results saved to: {output_path}")
    print(f"Screenshots saved to: {OUTPUT_DIR}")

    # Summary
    success = sum(1 for r in all_results.values() if r["status"] == "success")
    print(f"\nSuccess: {success}/{len(PAGES)}")

if __name__ == "__main__":
    main()
