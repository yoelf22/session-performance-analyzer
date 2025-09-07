#!/usr/bin/env python3
"""
Scraper for https://bolt.new/gallery/all
Handles load more pagination and project cards
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re

class BoltGalleryScraper:
    def __init__(self):
        self.base_url = "https://bolt.new/gallery/all"
        self.projects_data = []
        
    async def scrape_all_projects(self):
        """Main scraping function for Bolt.new Gallery"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                print(f"Navigating to {self.base_url}")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                print("Page loaded successfully, waiting for content...")
                
                await page.wait_for_timeout(5000)
                
                # Handle load more pagination
                await self.handle_load_more_pagination(page)
                
                # Extract projects from the page
                await self.extract_projects_from_page(page)
                
                print(f"\nScraping completed! Total projects found: {len(self.projects_data)}")
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Save partial data if any was collected
                if self.projects_data:
                    print(f"Saving partial data ({len(self.projects_data)} projects)...")
                    self.save_to_json('bolt_projects_partial.json')
                
            finally:
                await browser.close()
    
    async def handle_load_more_pagination(self, page):
        """Handle load more button clicking"""
        try:
            print("Looking for load more functionality...")
            
            load_more_attempts = 0
            max_attempts = 20  # Bolt.new might have many pages
            
            while load_more_attempts < max_attempts:
                load_more_attempts += 1
                
                # Look for load more button
                load_more_selectors = [
                    'button:has-text("Load More")',
                    'button:has-text("Load more")',
                    'button:has-text("Show More")',
                    '[data-testid*="load-more"]',
                    '.load-more',
                    'button[class*="load"]'
                ]
                
                button_clicked = False
                for selector in load_more_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button:
                            is_visible = await button.is_visible()
                            is_disabled = await button.get_attribute('disabled')
                            
                            if is_visible and not is_disabled:
                                print(f"Clicking load more button (attempt {load_more_attempts})...")
                                
                                # Get current project count
                                current_content = await page.content()
                                current_soup = BeautifulSoup(current_content, 'html.parser')
                                current_project_count = len(self.find_project_elements(current_soup))
                                
                                await button.click()
                                await page.wait_for_timeout(3000)  # Wait for new content
                                
                                # Check if new content loaded
                                new_content = await page.content()
                                new_soup = BeautifulSoup(new_content, 'html.parser')
                                new_project_count = len(self.find_project_elements(new_soup))
                                
                                if new_project_count > current_project_count:
                                    print(f"Loaded more projects: {current_project_count} -> {new_project_count}")
                                    button_clicked = True
                                    break
                                else:
                                    print("No new projects loaded, stopping...")
                                    return
                    except Exception as e:
                        continue
                
                if not button_clicked:
                    print("No more load buttons found")
                    break
                    
                await page.wait_for_timeout(2000)  # Be respectful with requests
            
            print(f"Load more pagination completed after {load_more_attempts} attempts")
            
        except Exception as e:
            print(f"Error in load more pagination: {e}")
    
    def find_project_elements(self, soup):
        """Find project elements in soup (helper for pagination)"""
        project_selectors = [
            '[data-testid*="project"]',
            '.project-card',
            '.gallery-item',
            '[class*="project"]',
            '[class*="gallery"]',
            '.card'
        ]
        
        for selector in project_selectors:
            elements = soup.select(selector)
            if len(elements) > 5:  # Should have multiple projects
                return elements
        
        # Fallback: look for any structured elements that might be projects
        return soup.find_all('div', class_=True)
    
    async def extract_projects_from_page(self, page):
        """Extract all projects from the current page state"""
        print("Extracting projects from page...")
        
        content = await page.content()
        
        # Save debug HTML
        with open('bolt_debug.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        soup = BeautifulSoup(content, 'html.parser')
        
        projects = []
        
        # Try multiple selector strategies for Bolt.new
        project_selectors = [
            # Bolt.new specific selectors
            '[data-testid*="project"]',
            '[data-testid*="gallery"]',
            '.project-card',
            '.gallery-item',
            '.gallery-card',
            # Generic selectors
            '[class*="project"]',
            '[class*="gallery"]',
            '.card',
            # Grid patterns
            '.grid > div',
            '[class*="grid"] > div',
            # Link patterns
            'a[href*="/project/"]',
            'a[href*="/gallery/"]'
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
                    
                    if len(filtered_elements) >= 5:  # Should find multiple projects
                        project_elements = filtered_elements
                        print(f"Using selector '{selector}' found {len(filtered_elements)} project elements")
                        break
            except Exception as e:
                continue
        
        # Fallback approach: look for any elements with project-like content
        if not project_elements:
            print("Trying fallback approach...")
            all_divs = soup.find_all('div', class_=True)
            
            for div in all_divs:
                if self.looks_like_project_card(div):
                    project_elements.append(div)
        
        print(f"Processing {len(project_elements)} potential project elements")
        
        for element in project_elements:
            project_data = self.extract_project_details(element)
            if project_data and project_data.get('title'):
                # Avoid duplicates
                if not any(existing.get('title') == project_data['title'] and 
                          existing.get('app_url') == project_data.get('app_url') for existing in projects):
                    projects.append(project_data)
        
        self.projects_data = projects
        print(f"Successfully extracted {len(projects)} unique projects")
    
    def looks_like_project_card(self, element) -> bool:
        """Check if element looks like a project card"""
        try:
            text = element.get_text(strip=True)
            
            # Should have reasonable text length
            if len(text) < 15 or len(text) > 1000:
                return False
            
            # Should have images or links or both
            has_img = bool(element.find('img'))
            has_link = bool(element.find('a')) or element.name == 'a'
            has_button = bool(element.find('button'))
            
            if not (has_img or has_link or has_button):
                return False
            
            # Should not be navigation/header/footer
            classes = ' '.join(element.get('class', []))
            nav_indicators = ['nav', 'menu', 'header', 'footer', 'sidebar', 'toolbar']
            if any(indicator in classes.lower() for indicator in nav_indicators):
                return False
            
            # Look for project-like text patterns
            project_indicators = ['project', 'app', 'demo', 'build', 'create', 'made with']
            if any(indicator in text.lower() for indicator in project_indicators):
                return True
            
            # If it has an image and reasonable text, it's likely a project card
            if has_img and len(text) > 20 and len(text) < 200:
                return True
                
            return False
            
        except Exception:
            return False
    
    def extract_project_details(self, element) -> Dict[str, Any]:
        """Extract project details from an element"""
        project_data = {
            'title': None,
            'description': None,
            'creator_name': None,
            'app_url': None,
            'screenshot_url': None,
            'tags': [],
            'likes': None,
            'created_date': None,
            'category': None,
            'submitted_by': 'system'
        }
        
        # Extract title
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            '[data-testid*="title"]',
            '.title', '.name', '.project-title',
            '[class*="title"]', '[class*="name"]'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if len(title_text) > 2 and len(title_text) < 150:
                    project_data['title'] = title_text
                    break
        
        # Extract description
        desc_selectors = [
            'p', '.description', '.summary',
            '[data-testid*="description"]',
            '[class*="description"]', '[class*="summary"]',
            '.excerpt', '[class*="excerpt"]'
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
            '.author', '.creator', '.username', '.by',
            '[class*="author"]', '[class*="creator"]',
            '[class*="username"]'
        ]
        
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # Clean up author text
                author_text = re.sub(r'^(by|created by|author:)\s*', '', author_text, flags=re.IGNORECASE)
                if len(author_text) > 1 and len(author_text) < 50:
                    project_data['creator_name'] = author_text
                    break
        
        # Extract URL
        link_elem = element if element.name == 'a' else element.find('a')
        if link_elem:
            href = link_elem.get('href')
            if href and not href.startswith('#'):
                project_data['app_url'] = self.normalize_url(href)
        
        # Extract image
        img_elem = element.find('img')
        if img_elem:
            img_src = img_elem.get('src') or img_elem.get('data-src')
            if img_src:
                project_data['screenshot_url'] = self.normalize_url(img_src)
        
        # Extract tags
        tag_selectors = [
            '.tag', '.badge', '.label', '.category',
            '[class*="tag"]', '[class*="badge"]', '[class*="label"]'
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
                    project_data['tags'] = tags[:5]
                    break
        
        # Extract likes/hearts
        text_content = element.get_text()
        like_patterns = [
            r'(\d+)\s*(?:like|heart|♥|❤)',
            r'(\d+)\s*👍',
            r'(\d+)\s*⭐'
        ]
        
        for pattern in like_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                project_data['likes'] = int(match.group(1))
                break
        
        # Convert tags to single category and add required fields
        if project_data['tags']:
            project_data['category'] = project_data['tags'][0] 
        elif not project_data['category']:
            project_data['category'] = 'general'
        
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
            return f"https://bolt.new{url}"
        else:
            return f"https://bolt.new/{url}"
    
    def save_to_json(self, filename: str = 'bolt_projects.json'):
        """Save scraped data to JSON file"""
        total_projects = len(self.projects_data)
        
        # Analyze tags and categories
        all_tags = []
        authors = []
        
        for project in self.projects_data:
            all_tags.extend(project.get('tags', []))
            if project.get('author'):
                authors.append(project.get('author'))
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        author_counts = {}
        for author in authors:
            author_counts[author] = author_counts.get(author, 0) + 1
        
        data = {
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_website': 'https://bolt.new/gallery/all',
            'total_projects_found': total_projects,
            'description': 'Projects from Bolt.new Gallery with load more pagination',
            'tag_summary': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'top_authors': dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'projects': self.projects_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
        print(f"Total projects scraped: {total_projects}")
        if tag_counts:
            print(f"Top tags: {list(tag_counts.keys())[:5]}")
        if author_counts:
            print(f"Top authors: {list(author_counts.keys())[:5]}")

async def main():
    scraper = BoltGalleryScraper()
    await scraper.scrape_all_projects()
    scraper.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())