#!/usr/bin/env python3
"""
Scraper for https://replit.com/gallery
Handles anti-bot measures and dynamic loading
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

class ReplitGalleryScraper:
    def __init__(self):
        self.base_url = "https://replit.com/gallery"
        self.projects_data = []
        
    async def scrape_all_projects(self):
        """Main scraping function that handles Replit Gallery structure"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                print(f"Navigating to {self.base_url}")
                
                # Set extra headers to appear more like a real browser
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                })
                
                # Try to navigate to the page
                response = await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                
                if response.status != 200:
                    print(f"Failed to load page. Status: {response.status}")
                    return
                
                print("Page loaded successfully, waiting for content...")
                await page.wait_for_timeout(5000)
                
                # Handle potential dynamic loading
                await self.handle_dynamic_loading(page)
                
                # Extract projects from the page
                await self.extract_projects_from_page(page)
                
                print(f"\nScraping completed! Total projects found: {len(self.projects_data)}")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Try to save partial data if any was collected
                if self.projects_data:
                    print(f"Saving partial data ({len(self.projects_data)} projects)...")
                    self.save_to_json('replit_projects_partial.json')
                
            finally:
                await browser.close()
    
    async def handle_dynamic_loading(self, page):
        """Handle dynamic content loading (infinite scroll, load more buttons, etc.)"""
        try:
            print("Checking for dynamic loading mechanisms...")
            
            # Look for load more buttons
            load_more_selectors = [
                'button:has-text("Load more")',
                'button:has-text("Show more")',
                '[data-testid*="load-more"]',
                '.load-more',
                'button[class*="load"]'
            ]
            
            loaded_more = True
            attempts = 0
            max_attempts = 5
            
            while loaded_more and attempts < max_attempts:
                loaded_more = False
                attempts += 1
                
                # Try clicking load more buttons
                for selector in load_more_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button:
                            is_visible = await button.is_visible()
                            if is_visible:
                                print(f"Found load more button, clicking... (attempt {attempts})")
                                await button.click()
                                await page.wait_for_timeout(3000)
                                loaded_more = True
                                break
                    except Exception as e:
                        continue
                
                # Try infinite scroll if no buttons found
                if not loaded_more:
                    print(f"Trying infinite scroll... (attempt {attempts})")
                    prev_height = await page.evaluate('document.body.scrollHeight')
                    
                    # Scroll to bottom
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(3000)
                    
                    # Check if more content loaded
                    new_height = await page.evaluate('document.body.scrollHeight')
                    if new_height > prev_height:
                        loaded_more = True
                        print(f"New content loaded via scroll (height: {prev_height} -> {new_height})")
                
                if loaded_more:
                    await page.wait_for_timeout(2000)
            
            print(f"Dynamic loading completed after {attempts} attempts")
            
        except Exception as e:
            print(f"Error in dynamic loading: {e}")
    
    async def extract_projects_from_page(self, page):
        """Extract project data from the current page state"""
        print("Extracting projects from page...")
        
        content = await page.content()
        
        # Save debug HTML
        with open('replit_debug.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        soup = BeautifulSoup(content, 'html.parser')
        
        projects = []
        
        # Try multiple selector strategies for Replit Gallery
        project_selectors = [
            # Common Replit selectors
            '[data-testid*="project"]',
            '[data-testid*="repl"]',
            '.repl-card',
            '.project-card',
            # Generic card patterns
            '.card',
            '[class*="card"]',
            # Grid/list patterns
            '.grid > div',
            '.gallery > div',
            '[class*="gallery"] > div',
            '[class*="grid"] > div',
            # Link-based project cards
            'a[href*="/repl/"]',
            'a[href*="/@"]'
        ]
        
        project_elements = []
        for selector in project_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # Filter for elements that look like project cards
                    filtered_elements = []
                    for el in elements:
                        if self.looks_like_project_card(el):
                            filtered_elements.append(el)
                    
                    if len(filtered_elements) > 5:  # Should find multiple projects
                        project_elements = filtered_elements
                        print(f"Using selector '{selector}' found {len(filtered_elements)} project elements")
                        break
            except Exception as e:
                continue
        
        # Fallback: look for any links that might be projects
        if not project_elements:
            print("Trying fallback approach...")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if ('/@' in href and '/repl/' in href) or '/repl/' in href:
                    if self.looks_like_project_card(link):
                        project_elements.append(link)
        
        print(f"Processing {len(project_elements)} potential project elements")
        
        for element in project_elements:
            project_data = self.extract_project_details(element)
            if project_data and project_data.get('title'):
                # Avoid duplicates
                if not any(existing.get('title') == project_data['title'] and 
                          existing.get('app_url') == project_data['app_url'] for existing in projects):
                    projects.append(project_data)
        
        self.projects_data = projects
        print(f"Successfully extracted {len(projects)} unique projects")
    
    def looks_like_project_card(self, element) -> bool:
        """Check if element looks like a project card"""
        try:
            text = element.get_text(strip=True)
            
            # Should have reasonable text length
            if len(text) < 10 or len(text) > 1000:
                return False
            
            # Should have images or links
            has_img = bool(element.find('img'))
            has_link = bool(element.find('a')) or element.name == 'a'
            
            if not (has_img or has_link):
                return False
            
            # Should not be navigation elements
            nav_indicators = ['nav', 'menu', 'header', 'footer', 'sidebar']
            classes = ' '.join(element.get('class', []))
            if any(indicator in classes.lower() for indicator in nav_indicators):
                return False
            
            return True
            
        except Exception:
            return False
    
    def extract_project_details(self, element) -> Dict[str, Any]:
        """Extract project details from a single element"""
        project_data = {
            'title': None,
            'description': None,
            'creator_name': None,
            'app_url': None,
            'screenshot_url': None,
            'tags': [],
            'language': None,
            'stars': None,
            'forks': None,
            'created_date': None,
            'submitted_by': 'system'
        }
        
        # Extract title
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '[data-testid*="title"]',
            '.title', '.name', '.project-name',
            '[class*="title"]', '[class*="name"]'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if len(title_text) > 2 and len(title_text) < 100:
                    project_data['title'] = title_text
                    break
        
        # Extract description
        desc_selectors = [
            'p', '.description', '.summary',
            '[data-testid*="description"]',
            '[class*="description"]', '[class*="summary"]'
        ]
        
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 10 and len(desc_text) < 500:
                    project_data['description'] = desc_text
                    break
        
        # Extract author
        author_selectors = [
            '[data-testid*="author"]',
            '.author', '.creator', '.username',
            '[class*="author"]', '[class*="creator"]'
        ]
        
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                if len(author_text) > 1 and len(author_text) < 50:
                    project_data['creator_name'] = author_text
                    break
        
        # Extract URL
        link_elem = element if element.name == 'a' else element.find('a')
        if link_elem:
            href = link_elem.get('href')
            if href:
                project_data['app_url'] = self.normalize_url(href)
        
        # Extract image
        img_elem = element.find('img')
        if img_elem:
            img_src = img_elem.get('src') or img_elem.get('data-src')
            if img_src:
                project_data['screenshot_url'] = self.normalize_url(img_src)
        
        # Extract tags/languages
        tag_selectors = [
            '.tag', '.badge', '.label', '.language',
            '[class*="tag"]', '[class*="badge"]', '[class*="language"]'
        ]
        
        for selector in tag_selectors:
            tag_elements = element.select(selector)
            if tag_elements:
                tags = []
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    if tag_text and len(tag_text) < 30:
                        tags.append(tag_text)
                if tags:
                    project_data['tags'] = tags[:5]  # Limit to 5 tags
                    break
        
        # Try to extract language from text content
        if not project_data['language']:
            text_content = element.get_text()
            languages = ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin']
            for lang in languages:
                if lang in text_content:
                    project_data['language'] = lang
                    break
        
        # Extract metrics (stars, forks, etc.)
        metrics_text = element.get_text()
        
        # Look for star patterns
        star_match = re.search(r'(\d+)\s*(?:star|★)', metrics_text, re.IGNORECASE)
        if star_match:
            project_data['stars'] = int(star_match.group(1))
        
        # Look for fork patterns
        fork_match = re.search(r'(\d+)\s*(?:fork|🍴)', metrics_text, re.IGNORECASE)
        if fork_match:
            project_data['forks'] = int(fork_match.group(1))
        
        # Convert tags to single category and add required fields
        if project_data['tags']:
            project_data['category'] = project_data['tags'][0]
        else:
            # Use language as category if available, otherwise default
            project_data['category'] = project_data.get('language') or 'general'
        
        project_data['submission_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Remove tags array since we now have single category
        del project_data['tags']
        
        return project_data if project_data.get('title') else None
    
    def normalize_url(self, url):
        """Normalize URLs to be absolute"""
        if not url:
            return None
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"https://replit.com{url}"
        else:
            return f"https://replit.com/{url}"
    
    def save_to_json(self, filename: str = 'replit_projects.json'):
        """Save scraped data to JSON file"""
        # Create summary statistics
        total_projects = len(self.projects_data)
        
        # Count languages and tags
        all_languages = [p.get('language') for p in self.projects_data if p.get('language')]
        all_tags = []
        for project in self.projects_data:
            all_tags.extend(project.get('tags', []))
        
        language_counts = {}
        for lang in all_languages:
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        data = {
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_website': 'https://replit.com/gallery',
            'total_projects_found': total_projects,
            'description': 'Projects from Replit Gallery',
            'language_summary': dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'tag_summary': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'projects': self.projects_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
        print(f"Total projects scraped: {total_projects}")
        if language_counts:
            print(f"Top languages: {list(language_counts.keys())[:5]}")
        if tag_counts:
            print(f"Top tags: {list(tag_counts.keys())[:5]}")

async def main():
    scraper = ReplitGalleryScraper()
    await scraper.scrape_all_projects()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())