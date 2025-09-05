#!/usr/bin/env python3
"""
Scraper for https://catalog.base44.com/apps
Handles numbered pagination and card-based app layout
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

class Base44Scraper:
    def __init__(self):
        self.base_url = "https://catalog.base44.com/apps"
        self.apps_data = []
        
    async def scrape_all_apps(self):
        """Main scraping function that handles numbered pagination"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"Starting to scrape {self.base_url}")
                
                # Start with page 1
                current_page = 1
                has_more_pages = True
                
                while has_more_pages:
                    page_url = f"{self.base_url}?page={current_page}" if current_page > 1 else self.base_url
                    print(f"Scraping page {current_page}: {page_url}")
                    
                    await page.goto(page_url, wait_until="networkidle")
                    await page.wait_for_timeout(3000)
                    
                    # Extract apps from current page
                    apps_on_page = await self.extract_apps_from_page(page)
                    
                    if apps_on_page:
                        # Add page number to each app
                        for app in apps_on_page:
                            app['page_number'] = current_page
                        
                        self.apps_data.extend(apps_on_page)
                        print(f"Found {len(apps_on_page)} apps on page {current_page}")
                    else:
                        print(f"No apps found on page {current_page}")
                        has_more_pages = False
                        break
                    
                    # Check if there's a next page
                    has_more_pages = await self.has_next_page(page, current_page)
                    
                    if has_more_pages:
                        current_page += 1
                        await page.wait_for_timeout(2000)  # Be respectful
                    else:
                        print("No more pages to scrape")
                        break
                
                print(f"\nScraping completed! Total apps found: {len(self.apps_data)}")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
    
    async def extract_apps_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract app data from current page"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        apps = []
        
        # Look for app cards - try different selector strategies
        app_selectors = [
            # Common card/grid patterns
            '.card',
            '.app-card',
            '[class*="card"]',
            '.grid-item',
            '.app-item',
            # Generic container patterns
            '.grid > div',
            '.container > div',
            '[class*="grid"] > div',
            # Link-based cards
            'a[href*="/app"]',
            'a[href*="/apps"]',
            # Flex/grid layouts
            '[class*="flex"] [class*="card"]',
            '[class*="grid"] [class*="item"]'
        ]
        
        app_elements = []
        for selector in app_selectors:
            try:
                elements = soup.select(selector)
                if elements and len(elements) > 2:  # Should have multiple apps
                    # Filter for elements that look like app cards
                    filtered_elements = []
                    for el in elements:
                        # Check if element contains app-like content
                        text = el.get_text(strip=True)
                        has_links = bool(el.find('a'))
                        has_images = bool(el.find('img'))
                        
                        # App cards should have reasonable text length and some interactive elements
                        if (len(text) > 20 and len(text) < 500 and 
                            (has_links or has_images) and
                            not self.is_navigation_element(el)):
                            filtered_elements.append(el)
                    
                    if len(filtered_elements) >= 3:  # Should find multiple apps
                        app_elements = filtered_elements
                        print(f"Using selector '{selector}' found {len(filtered_elements)} app elements")
                        break
                        
            except Exception as e:
                continue
        
        # If no specific selectors work, try to find elements with app-like patterns
        if not app_elements:
            # Look for any elements that might contain app information
            all_elements = soup.find_all(['div', 'article', 'section'], class_=True)
            
            for el in all_elements:
                text = el.get_text(strip=True)
                
                # Look for elements with app-like text patterns
                if (len(text) > 30 and len(text) < 300 and
                    ('Created by' in text or 'months ago' in text or 
                     'ago' in text or 'app' in text.lower()) and
                    not self.is_navigation_element(el)):
                    app_elements.append(el)
        
        print(f"Processing {len(app_elements)} potential app elements")
        
        for element in app_elements:
            app_data = self.extract_app_details(element)
            if app_data and app_data.get('title'):
                # Avoid duplicates
                if not any(existing['title'] == app_data['title'] for existing in apps):
                    apps.append(app_data)
        
        return apps
    
    def is_navigation_element(self, element) -> bool:
        """Check if element is likely navigation rather than an app"""
        text = element.get_text(strip=True).lower()
        nav_indicators = ['next', 'previous', 'page', 'navigation', 'menu', 'header', 'footer']
        return any(indicator in text for indicator in nav_indicators) and len(text) < 50
    
    def extract_app_details(self, element) -> Dict[str, Any]:
        """Extract app details from a single element"""
        app_data = {
            'title': None,
            'description': None,
            'categories': [],  # Will be converted to single category later
            'screenshot_url': None,
            'app_url': None,
            'creator_name': None,
            'created_date': None,
            'submitted_by': 'system',
            'tech_stack': 'Base44',
            'page_number': None
        }
        
        # Debug: print element content for first few apps
        debug_text = element.get_text(strip=True)[:100]
        if len(debug_text) > 20:  # Only debug actual app content
            pass  # Remove print to reduce noise
        
        # Extract app title - try different patterns
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.title', '.name', '.app-name',
            '[class*="title"]', '[class*="name"]',
            'strong', 'b'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Skip very short or long titles, and common non-app text
                if (len(title_text) > 2 and len(title_text) < 100 and
                    title_text not in ['Next', 'Previous', 'Page', 'Apps'] and
                    not title_text.isdigit()):
                    app_data['title'] = title_text
                    break
        
        # Extract description
        desc_selectors = [
            'p', '.description', '.summary', 
            '[class*="description"]', '[class*="summary"]',
            '.text', '[class*="text"]'
        ]
        
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                # Look for description-like text
                if (len(desc_text) > 20 and len(desc_text) < 300 and
                    'Created by' not in desc_text and
                    not desc_text.isdigit()):
                    app_data['description'] = desc_text
                    break
        
        # Extract screenshot/logo image
        img_elem = element.select_one('img')
        if img_elem:
            img_src = img_elem.get('src') or img_elem.get('data-src')
            if img_src:
                app_data['screenshot_url'] = self.normalize_url(img_src)
            else:
                # Use Base44 logo as fallback when no app logo found
                app_data['screenshot_url'] = 'https://catalog.base44.com/logo_v3.png'
        else:
            # Use Base44 logo as fallback when no img element found
            app_data['screenshot_url'] = 'https://catalog.base44.com/logo_v3.png'
        
        # Extract app URL - try multiple strategies
        app_url = None
        
        # Strategy 1: Look for links within the element that contain '/apps/'
        app_links = element.select('a[href*="/apps/"]')
        if app_links:
            # Take the first link that contains '/apps/' in the href
            for link in app_links:
                href = link.get('href')
                if href and '/apps/' in href and not href.endswith('/apps'):  # Not just the base URL
                    app_url = self.normalize_url(href)
                    break
        
        # Strategy 2: Look for any direct links within the element
        if not app_url:
            link_elem = element.select_one('a[href]')
            if link_elem:
                href = link_elem.get('href')
                if href and not href.startswith('#') and ('app' in href or len(href) > 5):
                    app_url = self.normalize_url(href)
        
        # Strategy 3: Check if the element itself is a link
        if not app_url and element.name == 'a':
            href = element.get('href')
            if href and not href.startswith('#'):
                app_url = self.normalize_url(href)
        
        # Strategy 4: Look for parent or sibling links that might contain the app URL
        if not app_url:
            # Check parent elements for links
            parent = element.parent
            while parent and not app_url:
                if parent.name == 'a' and parent.get('href'):
                    href = parent.get('href')
                    if href and not href.startswith('#') and ('/apps/' in href or len(href) > 10):
                        app_url = self.normalize_url(href)
                        break
                # Look for app-specific links in parent
                parent_app_links = parent.select('a[href*="/apps/"]')
                if parent_app_links:
                    href = parent_app_links[0].get('href')
                    if href and '/apps/' in href and not href.endswith('/apps'):
                        app_url = self.normalize_url(href)
                        break
                parent = parent.parent
        
        app_data['app_url'] = app_url
        
        # Extract categories/badges
        badge_selectors = [
            '.badge', '.tag', '.category', '.label',
            '[class*="badge"]', '[class*="tag"]', '[class*="category"]'
        ]
        
        for selector in badge_selectors:
            badge_elements = element.select(selector)
            if badge_elements:
                categories = []
                for badge in badge_elements:
                    badge_text = badge.get_text(strip=True)
                    if badge_text and len(badge_text) < 50:
                        categories.append(badge_text)
                if categories:
                    app_data['categories'] = categories[:5]  # Limit to 5 categories
                    break
        
        # Extract creator and creation info
        text_content = element.get_text()
        
        # Look for "Created by" pattern
        created_by_match = re.search(r'Created by[:\s]+([^,\n]+)', text_content, re.IGNORECASE)
        if created_by_match:
            app_data['creator_name'] = created_by_match.group(1).strip()
        
        # Look for time patterns (X months ago, etc.)
        time_pattern = re.search(r'(\d+)\s+(months?|weeks?|days?|years?)\s+ago', text_content, re.IGNORECASE)
        if time_pattern:
            app_data['created_date'] = time_pattern.group(0)
        
        # Convert categories array to single category
        if app_data['categories']:
            # Choose the first/primary category
            app_data['category'] = app_data['categories'][0]
        else:
            app_data['category'] = 'general'  # Default category
        
        # Add submission date (current timestamp)
        app_data['submission_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Remove the categories array since we now have single category
        del app_data['categories']
        
        return app_data if app_data.get('title') else None
    
    async def has_next_page(self, page, current_page) -> bool:
        """Check if there's a next page available"""
        try:
            # Look for next button or higher page numbers
            next_selectors = [
                'a:has-text("Next")',
                'button:has-text("Next")',
                '[aria-label*="next" i]',
                '.next',
                f'a:has-text("{current_page + 1}")'  # Look for next page number
            ]
            
            for selector in next_selectors:
                next_element = await page.query_selector(selector)
                if next_element:
                    # Check if element is not disabled
                    is_disabled = await next_element.get_attribute('disabled')
                    has_disabled_class = await next_element.evaluate('el => el.classList.contains("disabled")')
                    
                    if not is_disabled and not has_disabled_class:
                        return True
            
            # Check if current page + 1 exists as a link
            try:
                next_page_selector = f'a[href*="page={current_page + 1}"]'
                next_page_link = await page.query_selector(next_page_selector)
                if next_page_link:
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Error checking for next page: {e}")
            return False
    
    def normalize_url(self, url):
        """Normalize URLs to be absolute"""
        if not url:
            return None
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"https://catalog.base44.com{url}"
        else:
            return f"https://catalog.base44.com/{url}"
    
    def save_to_json(self, filename: str = 'base44_apps.json'):
        """Save scraped data to JSON file"""
        # Create summary statistics
        total_apps = len(self.apps_data)
        pages_scraped = len(set(app.get('page_number', 0) for app in self.apps_data))
        
        # Count categories
        all_categories = []
        for app in self.apps_data:
            all_categories.extend(app.get('categories', []))
        
        category_counts = {}
        for cat in all_categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        data = {
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_website': 'https://catalog.base44.com/apps',
            'total_apps_found': total_apps,
            'pages_scraped': pages_scraped,
            'description': 'Apps from Base44 catalog with numbered pagination',
            'category_summary': dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'apps': self.apps_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
        print(f"Total apps scraped: {total_apps}")
        print(f"Pages processed: {pages_scraped}")
        if category_counts:
            print(f"Top categories: {list(category_counts.keys())[:5]}")

async def main():
    scraper = Base44Scraper()
    await scraper.scrape_all_apps()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())