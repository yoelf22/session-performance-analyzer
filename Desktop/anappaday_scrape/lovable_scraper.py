#!/usr/bin/env python3
"""
Scraper for https://launched.lovable.dev/ 
Extracts all apps through pagination with dynamic content handling
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class LovableScraper:
    def __init__(self):
        self.base_url = "https://launched.lovable.dev/"
        self.apps_data = []
        
    async def scrape_apps(self):
        """Main scraping function that handles pagination and dynamic loading"""
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"Navigating to {self.base_url}")
                await page.goto(self.base_url, wait_until="networkidle")
                
                # Wait for initial content to load
                await page.wait_for_timeout(5000)
                
                # Scroll down to load any lazy-loaded content
                await self.scroll_to_load_content(page)
                
                page_num = 1
                has_more_pages = True
                scroll_attempts = 0
                max_scroll_attempts = 10
                
                while has_more_pages and scroll_attempts < max_scroll_attempts:
                    print(f"Processing page/scroll {page_num}...")
                    
                    # Wait for app cards to load
                    await self.wait_for_apps_to_load(page)
                    
                    # Extract apps from current page
                    current_count = len(self.apps_data)
                    apps_on_page = await self.extract_apps_from_page(page)
                    
                    # Filter out duplicates based on title and URL
                    new_apps = []
                    existing_titles = {app.get('title') for app in self.apps_data}
                    existing_urls = {app.get('app_url') for app in self.apps_data}
                    
                    for app in apps_on_page:
                        if (app.get('title') not in existing_titles and 
                            app.get('app_url') not in existing_urls):
                            new_apps.append(app)
                    
                    if new_apps:
                        self.apps_data.extend(new_apps)
                        print(f"Found {len(new_apps)} new apps (total: {len(self.apps_data)})")
                    else:
                        print(f"No new apps found on page {page_num}")
                    
                    # Try to navigate to next page or scroll for more content
                    previous_count = len(self.apps_data)
                    has_more_pages = await self.go_to_next_page(page)
                    
                    if has_more_pages:
                        page_num += 1
                        scroll_attempts += 1
                        await page.wait_for_timeout(3000)
                        
                        # If no new content after scrolling, stop
                        if len(self.apps_data) == previous_count:
                            scroll_attempts += 1
                            if scroll_attempts >= 3:  # No new content for 3 attempts
                                print("No new content loaded, stopping...")
                                break
                    else:
                        break
                    
                print(f"\nScraping completed! Total apps found: {len(self.apps_data)}")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                
            finally:
                await browser.close()
    
    async def scroll_to_load_content(self, page):
        """Scroll down to trigger lazy loading of content"""
        try:
            # Get initial height
            last_height = await page.evaluate('document.body.scrollHeight')
            
            # Scroll down in increments
            for i in range(5):  # Try up to 5 scrolls
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                
                # Check if new content loaded
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break  # No more content to load
                last_height = new_height
                print(f"Scrolled to load more content (height: {new_height})")
                
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
    
    async def wait_for_apps_to_load(self, page):
        """Wait for app cards to load on the page"""
        selectors_to_try = [
            '[data-testid*="app"]',
            '.app-card',
            '.project-card', 
            '[class*="card"]',
            '[class*="app"]',
            '[class*="project"]'
        ]
        
        for selector in selectors_to_try:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                print(f"Found apps using selector: {selector}")
                return
            except:
                continue
        
        # If no specific selectors work, wait a bit for dynamic content
        await page.wait_for_timeout(3000)
    
    async def extract_apps_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract app data from the current page"""
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        apps = []
        
        # Debug: Save the HTML to see the structure
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # More specific selectors for app cards on Lovable
        app_selectors = [
            # Likely selectors for app/project cards
            '.grid-item',
            '.project-item',
            '.app-item',
            '[data-app-id]',
            '[data-project-id]', 
            'a[href*="/app/"]',
            'a[href*="/project/"]',
            # Grid layouts
            '.grid > a',
            '.grid > div > a',
            '.grid-container > div',
            # Cards with images and links
            'div:has(img):has(a)',
            'article:has(img)',
            # React component patterns
            '[class*="Card"]',
            '[class*="Item"]',
            '[data-testid*="card"]',
            '[data-testid*="item"]'
        ]
        
        app_elements = []
        for selector in app_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # Filter out elements that are too small or don't contain meaningful content
                    filtered_elements = []
                    for el in elements:
                        text_content = el.get_text(strip=True)
                        has_image = bool(el.select('img'))
                        has_link = bool(el.select('a')) or el.name == 'a'
                        
                        if (len(text_content) > 10 and 
                            (has_image or has_link) and
                            'Top Products launched this week' not in text_content):
                            filtered_elements.append(el)
                    
                    if filtered_elements:
                        app_elements = filtered_elements
                        print(f"Using selector '{selector}' found {len(filtered_elements)} app elements")
                        break
            except Exception as e:
                continue
        
        # If still no elements found, try a different approach
        if not app_elements:
            # Look for any clickable elements with images that might be apps
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                # Skip navigation links
                if any(skip in href for skip in ['#', 'javascript:', 'mailto:', 'tel:']):
                    continue
                
                # Look for links that might be apps
                text = link.get_text(strip=True)
                has_img = bool(link.find('img'))
                
                if (len(text) > 5 and len(text) < 200 and 
                    (has_img or 'app' in href.lower() or 'project' in href.lower()) and
                    'Top Products launched this week' not in text):
                    app_elements.append(link)
        
        print(f"Final app elements count: {len(app_elements)}")
        
        for element in app_elements:
            app_data = self.extract_app_details(element)
            if (app_data and app_data.get('title') and 
                app_data['title'] != 'Top Products launched this week' and
                len(app_data['title']) > 3):
                apps.append(app_data)
        
        return apps
    
    def extract_app_details(self, element) -> Dict[str, Any]:
        """Extract details from a single app element"""
        app_data = {
            'title': None,
            'description': None,
            'image_url': None,
            'app_url': None,
            'tags': [],
            'author': None,
            'launch_date': None
        }
        
        # Extract title
        title_selectors = ['h1', 'h2', 'h3', 'h4', '[class*="title"]', '[class*="name"]', 'strong']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                app_data['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract description
        desc_selectors = ['p', '[class*="description"]', '[class*="summary"]', '.text']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem and desc_elem.get_text(strip=True):
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 10:  # Avoid very short text that's probably not description
                    app_data['description'] = desc_text
                    break
        
        # Extract image URL
        img_elem = element.select_one('img')
        if img_elem:
            img_src = img_elem.get('src') or img_elem.get('data-src')
            if img_src:
                if img_src.startswith('http'):
                    app_data['image_url'] = img_src
                elif img_src.startswith('/'):
                    app_data['image_url'] = f"https://launched.lovable.dev{img_src}"
        
        # Extract app URL
        link_elem = element.select_one('a')
        if link_elem:
            href = link_elem.get('href')
            if href:
                if href.startswith('http'):
                    app_data['app_url'] = href
                elif href.startswith('/'):
                    app_data['app_url'] = f"https://launched.lovable.dev{href}"
        
        # Extract tags
        tag_selectors = ['.tag', '.badge', '[class*="tag"]', '[class*="category"]']
        for selector in tag_selectors:
            tag_elements = element.select(selector)
            if tag_elements:
                app_data['tags'] = [tag.get_text(strip=True) for tag in tag_elements]
                break
        
        # Extract author
        author_selectors = ['.author', '[class*="author"]', '[class*="creator"]', 'small']
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem and author_elem.get_text(strip=True):
                app_data['author'] = author_elem.get_text(strip=True)
                break
        
        # Extract date
        date_selectors = ['time', '.date', '[class*="date"]', '[datetime]']
        for selector in date_selectors:
            date_elem = element.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                if date_text:
                    app_data['launch_date'] = date_text
                    break
        
        return app_data
    
    async def go_to_next_page(self, page) -> bool:
        """Try to navigate to the next page, return True if successful"""
        # Try different pagination selectors
        next_selectors = [
            'button:has-text("Next")',
            'a:has-text("Next")',
            '[aria-label*="next" i]',
            '.pagination .next',
            'button[class*="next"]',
            'a[class*="next"]',
            '.pagination li:last-child a',
            'button:has-text(">")',
            'a:has-text(">")'
        ]
        
        for selector in next_selectors:
            try:
                next_button = await page.query_selector(selector)
                if next_button:
                    # Check if button is disabled
                    is_disabled = await next_button.get_attribute('disabled')
                    has_disabled_class = await next_button.evaluate('el => el.classList.contains("disabled")')
                    
                    if not is_disabled and not has_disabled_class:
                        await next_button.click()
                        await page.wait_for_timeout(2000)  # Wait for navigation
                        print(f"Successfully clicked next page using selector: {selector}")
                        return True
            except Exception as e:
                continue
        
        # Try infinite scroll
        try:
            current_height = await page.evaluate('document.body.scrollHeight')
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(3000)
            new_height = await page.evaluate('document.body.scrollHeight')
            
            if new_height > current_height:
                print("Successfully loaded more content via infinite scroll")
                return True
        except:
            pass
        
        # Try URL-based pagination
        try:
            current_url = page.url
            # Look for page parameter in URL and increment it
            if 'page=' in current_url:
                import re
                match = re.search(r'page=(\d+)', current_url)
                if match:
                    current_page = int(match.group(1))
                    next_page_url = current_url.replace(f'page={current_page}', f'page={current_page + 1}')
                    await page.goto(next_page_url, wait_until="networkidle")
                    return True
        except:
            pass
        
        return False
    
    def save_to_json(self, filename: str = 'lovable_apps.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_apps': len(self.apps_data),
                'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'apps': self.apps_data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
        print(f"Total apps scraped: {len(self.apps_data)}")

async def main():
    scraper = LovableScraper()
    await scraper.scrape_apps()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())