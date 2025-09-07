#!/usr/bin/env python3
"""
Enhanced scraper for https://launched.lovable.dev/ 
Extracts both current week's apps and historical weekly winners
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

class LovableScraperEnhanced:
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
                await self.extract_current_week_apps(soup)
                
                # Extract historical weekly winners  
                await self.extract_historical_apps(soup)
                
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
    
    async def extract_current_week_apps(self, soup):
        """Extract current week's ranked apps"""
        print("Extracting current week's top apps...")
        
        # Find the current week's app list
        current_week_section = soup.find('h3', string='Top Products launched this week')
        if not current_week_section:
            print("Current week section not found")
            return
        
        # Find the parent container with app listings
        apps_container = current_week_section.find_parent().find_parent()
        if not apps_container:
            print("Apps container not found")
            return
        
        # Find all app entries in the current week
        app_entries = apps_container.find_all('div', class_='flex w-full items-stretch gap-4')
        
        for entry in app_entries:
            app_data = self.extract_ranked_app_details(entry)
            if app_data:
                app_data['type'] = 'current_week'
                self.current_week_apps.append(app_data)
        
        print(f"Found {len(self.current_week_apps)} current week apps")
    
    async def extract_historical_apps(self, soup):
        """Extract historical weekly winners"""
        print("Extracting historical weekly winners...")
        
        # Find all historical week sections by looking for "Week of" pattern
        week_pattern = re.compile(r'Week of|Last Week')
        
        # Find elements that contain week information
        week_elements = soup.find_all(text=week_pattern)
        
        processed_weeks = set()
        
        for week_text_node in week_elements:
            # Get the parent element containing the week info
            week_element = week_text_node.parent
            if not week_element:
                continue
                
            week_name = week_text_node.strip()
            
            # Avoid processing the same week multiple times
            if week_name in processed_weeks:
                continue
            processed_weeks.add(week_name)
            
            # Find the associated link and image
            link_element = None
            img_element = None
            
            # Try to find the link and image in the same container
            container = week_element
            for _ in range(5):  # Search up to 5 parent levels
                if container is None:
                    break
                    
                link_element = container.find('a', href=True)
                img_element = container.find('img')
                
                if link_element and img_element:
                    break
                    
                container = container.parent
            
            if link_element and img_element:
                app_data = {
                    'title': week_name,
                    'description': None,
                    'image_url': self.normalize_url(img_element.get('src')),
                    'app_url': self.normalize_url(link_element.get('href')),
                    'tags': [],
                    'author': None,
                    'launch_date': week_name,
                    'rank': None,
                    'votes': None,
                    'type': 'historical_winner'
                }
                
                # Try to extract app name from image alt or nearby text
                alt_text = img_element.get('alt', '')
                if alt_text and not week_pattern.search(alt_text):
                    app_data['actual_app_name'] = alt_text
                
                self.historical_apps.append(app_data)
        
        print(f"Found {len(self.historical_apps)} historical apps")
    
    def extract_ranked_app_details(self, entry) -> Dict[str, Any]:
        """Extract details from a ranked app entry"""
        try:
            app_data = {
                'title': None,
                'description': None,
                'image_url': None,
                'app_url': None,
                'tags': [],
                'author': None,
                'launch_date': None,
                'rank': None,
                'votes': None,
                'type': 'current_week'
            }
            
            # Extract rank
            rank_elem = entry.find('div', string=re.compile(r'^\d+\.$'))
            if rank_elem:
                rank_text = rank_elem.get_text(strip=True)
                app_data['rank'] = int(rank_text.replace('.', ''))
            
            # Extract app name
            name_elem = entry.find('div', class_='text-neutral-50 font-semibold')
            if name_elem:
                app_data['title'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = entry.find('div', class_='text-zinc-300 font-normal')
            if desc_elem:
                app_data['description'] = desc_elem.get_text(strip=True)
            
            # Extract image
            img_elem = entry.find('img')
            if img_elem:
                app_data['image_url'] = self.normalize_url(img_elem.get('src'))
                if img_elem.get('alt'):
                    app_data['alt_text'] = img_elem.get('alt')
            
            # Extract app URL
            link_elem = entry.find('a', href=True)
            if link_elem:
                href = link_elem.get('href')
                if href and not href.startswith('#'):
                    app_data['app_url'] = self.normalize_url(href)
            
            # Extract vote count
            vote_elem = entry.find('span', class_='text-neutral-50 font-medium text-lg')
            if not vote_elem:
                vote_elem = entry.find('span', class_='text-neutral-50 font-medium text-[15px]')
            
            if vote_elem:
                vote_text = vote_elem.get_text(strip=True)
                if vote_text.isdigit():
                    app_data['votes'] = int(vote_text)
            
            return app_data if app_data.get('title') else None
            
        except Exception as e:
            print(f"Error extracting app details: {str(e)}")
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
    
    def save_to_json(self, filename: str = 'lovable_apps_enhanced.json'):
        """Save scraped data to JSON file"""
        data = {
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_apps': len(self.all_apps),
            'current_week_count': len(self.current_week_apps),
            'historical_count': len(self.historical_apps),
            'current_week_apps': self.current_week_apps,
            'historical_apps': self.historical_apps,
            'all_apps': self.all_apps
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
        print(f"Total apps scraped: {len(self.all_apps)}")
        print(f"- Current week apps: {len(self.current_week_apps)}")
        print(f"- Historical weekly winners: {len(self.historical_apps)}")

async def main():
    scraper = LovableScraperEnhanced()
    await scraper.scrape_all_apps()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())