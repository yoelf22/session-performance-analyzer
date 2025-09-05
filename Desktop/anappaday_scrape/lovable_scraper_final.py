#!/usr/bin/env python3
"""
Final comprehensive scraper for https://launched.lovable.dev/ 
Extracts both current week's ranked apps and all historical weekly winners
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

class LovableScraperFinal:
    def __init__(self):
        self.base_url = "https://launched.lovable.dev/"
        self.current_week_apps = []
        self.historical_apps = []
        self.all_apps = []
        
    async def scrape_all_apps(self):
        """Main scraping function that extracts current and historical apps"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"Navigating to {self.base_url}")
                await page.goto(self.base_url, wait_until="networkidle")
                
                # Wait for content to load
                await page.wait_for_timeout(5000)
                
                # Scroll to load all content
                await self.scroll_to_load_content(page)
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract current week's top apps
                self.extract_current_week_apps(soup)
                
                # Extract historical weekly winners  
                self.extract_historical_apps(soup)
                
                # Combine all apps
                self.all_apps = self.current_week_apps + self.historical_apps
                
                print(f"\nScraping completed!")
                print(f"Current week apps: {len(self.current_week_apps)}")
                print(f"Historical apps: {len(self.historical_apps)}")
                print(f"Total apps: {len(self.all_apps)}")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
    
    async def scroll_to_load_content(self, page):
        """Scroll down to trigger lazy loading of content"""
        try:
            last_height = await page.evaluate('document.body.scrollHeight')
            
            for i in range(5):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break
                last_height = new_height
                print(f"Scrolled to load more content (height: {new_height})")
                
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
    
    def extract_current_week_apps(self, soup):
        """Extract current week's ranked apps"""
        print("Extracting current week's top apps...")
        
        # Find all ranking divs that contain numbered rankings
        ranking_divs = soup.find_all('div', string=re.compile(r'^\d+\.$'))
        
        for rank_div in ranking_divs:
            try:
                # Get the rank number
                rank_text = rank_div.get_text(strip=True)
                rank = int(rank_text.replace('.', ''))
                
                # Find the parent container that has all the app info
                app_container = rank_div.find_parent('div', class_='flex w-full items-stretch gap-4')
                if not app_container:
                    continue
                
                app_data = self.extract_ranked_app_details(app_container, rank)
                if app_data:
                    self.current_week_apps.append(app_data)
                    
            except Exception as e:
                print(f"Error processing rank div: {e}")
                continue
        
        # Sort by rank
        self.current_week_apps.sort(key=lambda x: x.get('rank', 999))
        print(f"Found {len(self.current_week_apps)} current week apps")
    
    def extract_historical_apps(self, soup):
        """Extract historical weekly winners"""
        print("Extracting historical weekly winners...")
        
        # Look for sections that appear to be weekly winners
        # These typically have "Week of" text patterns
        potential_winners = []
        
        # Find all links that might be to apps
        all_links = soup.find_all('a', href=True)
        
        processed_urls = set()
        
        for link in all_links:
            href = link.get('href', '')
            
            # Skip if we've already processed this URL
            if href in processed_urls:
                continue
                
            # Skip navigation and internal links
            if any(skip in href for skip in ['#', 'javascript:', 'mailto:', 'tel:', '/sso/', 'lovable.dev']):
                continue
            
            # Skip empty or very short hrefs
            if not href or len(href) < 5:
                continue
                
            # Look for external app links (likely actual apps)
            if ('http' in href and 
                'launched.lovable.dev' not in href and 
                ('lovable.app' in href or 'vercel.app' in href or 'netlify.app' in href or 
                 '.com' in href or '.org' in href or '.io' in href)):
                
                processed_urls.add(href)
                
                # Try to extract associated information
                app_data = self.extract_historical_app_details(link)
                if app_data:
                    self.historical_apps.append(app_data)
        
        # Remove duplicates based on URL
        unique_historical = []
        seen_urls = set()
        for app in self.historical_apps:
            url = app.get('app_url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_historical.append(app)
        
        self.historical_apps = unique_historical
        print(f"Found {len(self.historical_apps)} historical apps")
    
    def extract_ranked_app_details(self, app_container, rank) -> Dict[str, Any]:
        """Extract details from a ranked app entry"""
        try:
            app_data = {
                'title': None,
                'description': None,
                'screenshot_url': None,
                'app_url': None,
                'tags': [],
                'creator_name': None,
                'launch_date': None,
                'rank': rank,
                'votes': None,
                'type': 'current_week',
                'submitted_by': 'system'
            }
            
            # Extract app name
            name_elem = app_container.find('div', class_='text-neutral-50 font-semibold')
            if name_elem:
                app_data['title'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = app_container.find('div', class_='text-zinc-300 font-normal')
            if desc_elem:
                app_data['description'] = desc_elem.get_text(strip=True)
            
            # Extract image
            img_elem = app_container.find('img')
            if img_elem:
                app_data['screenshot_url'] = self.normalize_url(img_elem.get('src'))
                if img_elem.get('alt'):
                    app_data['alt_text'] = img_elem.get('alt')
            
            # Extract app URL
            link_elem = app_container.find('a', href=True)
            if link_elem:
                href = link_elem.get('href')
                if href and not href.startswith('#'):
                    app_data['app_url'] = self.normalize_url(href)
            
            # Extract vote count - try multiple possible selectors
            vote_selectors = [
                'span.text-neutral-50.font-medium.text-lg',
                'span.text-neutral-50.font-medium.text-[15px]',
                'span[class*="text-neutral-50"][class*="font-medium"]'
            ]
            
            for selector in vote_selectors:
                vote_elems = app_container.select(selector)
                for vote_elem in vote_elems:
                    vote_text = vote_elem.get_text(strip=True)
                    if vote_text.isdigit():
                        app_data['votes'] = int(vote_text)
                        break
                if app_data['votes']:
                    break
            
            # Add required schema fields
            if app_data['tags']:
                app_data['category'] = app_data['tags'][0]
            else:
                app_data['category'] = 'general'
            
            app_data['submission_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Remove tags array since we now have single category
            del app_data['tags']
            
            return app_data if app_data.get('title') else None
            
        except Exception as e:
            print(f"Error extracting ranked app details: {str(e)}")
            return None
    
    def extract_historical_app_details(self, link_element) -> Dict[str, Any]:
        """Extract details from a historical app link"""
        try:
            # Get the container around this link
            container = link_element
            for _ in range(5):  # Look up to 5 parent levels
                container = container.parent if container.parent else container
                
                # Look for week information in the container or nearby
                week_text = None
                for text_node in container.find_all(string=True):
                    text = text_node.strip()
                    if re.search(r'Week of|Last Week', text):
                        week_text = text
                        break
                
                if week_text:
                    break
            
            # If no week text found, try to get context from nearby elements
            if not week_text:
                # Look for any text that might indicate this is a historical entry
                prev_siblings = []
                current = link_element
                for _ in range(10):  # Check previous elements
                    if current.previous_sibling:
                        current = current.previous_sibling
                        if hasattr(current, 'get_text'):
                            text = current.get_text(strip=True)
                            if text and len(text) < 50:
                                prev_siblings.append(text)
                                if re.search(r'Week of|Last Week', text):
                                    week_text = text
                                    break
            
            app_data = {
                'title': week_text or 'Historical App',
                'description': None,
                'screenshot_url': None,
                'app_url': self.normalize_url(link_element.get('href')),
                'tags': [],
                'creator_name': None,
                'launch_date': week_text,
                'rank': None,
                'votes': None,
                'type': 'historical_winner',
                'submitted_by': 'system'
            }
            
            # Try to find associated image
            img_elem = container.find('img') if container else None
            if img_elem:
                app_data['screenshot_url'] = self.normalize_url(img_elem.get('src'))
                # If image has good alt text, use it as the actual app name
                alt_text = img_elem.get('alt', '').strip()
                if alt_text and len(alt_text) < 100 and not re.search(r'Week of|Last Week', alt_text):
                    app_data['actual_app_name'] = alt_text
            
            # Add required schema fields
            if app_data['tags']:
                app_data['category'] = app_data['tags'][0]
            else:
                app_data['category'] = 'general'
            
            app_data['submission_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Remove tags array since we now have single category
            del app_data['tags']
            
            return app_data
            
        except Exception as e:
            print(f"Error extracting historical app details: {str(e)}")
            return None
    
    def normalize_url(self, url):
        """Normalize URLs to be absolute"""
        if not url:
            return None
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"https://launched.lovable.dev{url}"
        else:
            return url
    
    def save_to_json(self, filename: str = 'lovable_apps_comprehensive.json'):
        """Save scraped data to JSON file"""
        # Create a summary of current week apps
        current_week_summary = []
        for app in self.current_week_apps:
            summary = {
                'rank': app.get('rank'),
                'name': app.get('title'),
                'description': app.get('description'),
                'votes': app.get('votes'),
                'url': app.get('app_url')
            }
            current_week_summary.append(summary)
        
        data = {
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_apps': len(self.all_apps),
            'current_week_count': len(self.current_week_apps),
            'historical_count': len(self.historical_apps),
            'current_week_summary': current_week_summary,
            'detailed_data': {
                'current_week_apps': self.current_week_apps,
                'historical_apps': self.historical_apps
            },
            'all_apps': self.all_apps
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
        print(f"Total apps scraped: {len(self.all_apps)}")
        print(f"- Current week apps: {len(self.current_week_apps)}")
        print(f"- Historical weekly winners: {len(self.historical_apps)}")
        
        # Print current week summary
        if self.current_week_apps:
            print(f"\nCurrent Week's Top Apps:")
            for app in self.current_week_apps[:5]:
                print(f"  {app.get('rank', '?')}. {app.get('title', 'Unknown')} - {app.get('votes', '?')} votes")

async def main():
    scraper = LovableScraperFinal()
    await scraper.scrape_all_apps()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())