#!/usr/bin/env python3
"""
Weekly scraper orchestrator - runs all scrapers and generates new items reports
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import traceback

# Import our scrapers
from lovable_scraper_final import LovableScraperFinal
from base44_scraper import Base44Scraper
from replit_scraper import ReplitGalleryScraper
from bolt_scraper import BoltGalleryScraper
from database import ScrapingDatabase
from notifications import NotificationManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeeklyScraper:
    def __init__(self, data_dir: str = "weekly_scraping_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.db = ScrapingDatabase(str(self.data_dir / "scraping_history.db"))
        self.notification_manager = NotificationManager()
        
        # Configure scrapers
        self.scrapers = {
            "lovable": {
                "class": LovableScraperFinal,
                "name": "Lovable Launched",
                "url": "https://launched.lovable.dev/"
            },
            "base44": {
                "class": Base44Scraper,
                "name": "Base44 Catalog",
                "url": "https://catalog.base44.com/apps"
            },
            "replit": {
                "class": ReplitGalleryScraper,
                "name": "Replit Gallery",
                "url": "https://replit.com/gallery"
            },
            "bolt": {
                "class": BoltGalleryScraper,
                "name": "Bolt.new Gallery",
                "url": "https://bolt.new/gallery/all"
            }
        }
    
    async def run_single_scraper(self, scraper_key: str) -> Dict[str, Any]:
        """Run a single scraper and return results"""
        scraper_config = self.scrapers[scraper_key]
        scraper_class = scraper_config["class"]
        site_name = scraper_config["name"]
        
        logger.info(f"Starting {site_name} scraper...")
        
        try:
            # Initialize and run scraper
            scraper = scraper_class()
            
            if hasattr(scraper, 'scrape_all_apps'):
                await scraper.scrape_all_apps()
                items = scraper.apps_data if hasattr(scraper, 'apps_data') else scraper.all_apps
            elif hasattr(scraper, 'scrape_all_projects'):
                await scraper.scrape_all_projects()
                items = scraper.projects_data
            else:
                logger.error(f"Unknown scraper interface for {site_name}")
                return {"success": False, "error": "Unknown scraper interface"}
            
            logger.info(f"{site_name}: Found {len(items)} total items")
            
            # Find new items
            new_items = self.db.find_new_items(site_name, items)
            logger.info(f"{site_name}: {len(new_items)} new items since last run")
            
            # Save all results to database
            stats = self.db.save_scraping_results(site_name, items)
            
            # Save weekly results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save all items
            all_items_file = self.data_dir / f"{scraper_key}_all_{timestamp}.json"
            with open(all_items_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'site': site_name,
                    'url': scraper_config["url"],
                    'total_items': len(items),
                    'items': items
                }, f, indent=2, ensure_ascii=False)
            
            # Save new items
            new_items_file = self.data_dir / f"{scraper_key}_new_{timestamp}.json"
            with open(new_items_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'site': site_name,
                    'url': scraper_config["url"],
                    'new_items_count': len(new_items),
                    'new_items': new_items
                }, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "site": site_name,
                "total_items": len(items),
                "new_items": len(new_items),
                "stats": stats,
                "files": {
                    "all_items": str(all_items_file),
                    "new_items": str(new_items_file)
                }
            }
            
        except Exception as e:
            error_msg = f"Error scraping {site_name}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Send error notification
            self.notification_manager.notify_error(str(e), f"{site_name} scraper")
            
            return {
                "success": False,
                "site": site_name,
                "error": str(e)
            }
    
    async def run_all_scrapers(self) -> Dict[str, Any]:
        """Run all scrapers and generate reports"""
        logger.info("Starting weekly scraping run...")
        start_time = time.time()
        
        results = {}
        total_new_items = 0
        
        # Run each scraper
        for scraper_key in self.scrapers.keys():
            result = await self.run_single_scraper(scraper_key)
            results[scraper_key] = result
            
            if result["success"]:
                total_new_items += result["new_items"]
        
        # Generate summary report
        end_time = time.time()
        duration = end_time - start_time
        
        summary = {
            "run_timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_new_items": total_new_items,
            "scrapers": results
        }
        
        # Save summary
        summary_file = self.data_dir / f"weekly_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Weekly scraping completed in {duration:.1f}s. Total new items: {total_new_items}")
        
        # Send notifications
        self.notification_manager.notify_scraping_results(summary)
        
        return summary
    
    def generate_weekly_report(self, days: int = 7) -> str:
        """Generate a human-readable weekly report"""
        report_lines = []
        report_lines.append("📊 WEEKLY SCRAPING REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Covering last {days} days")
        report_lines.append("")
        
        # Get stats from database
        stats = self.db.get_stats()
        
        report_lines.append("🌐 SITES SUMMARY:")
        total_new = 0
        for site in stats["sites"]:
            report_lines.append(f"  • {site['name']}")
            report_lines.append(f"    - Total items tracked: {site['tracked_items']}")
            report_lines.append(f"    - New this week: {site['new_this_week']}")
            report_lines.append(f"    - Last scraped: {site['last_scraped'] or 'Never'}")
            report_lines.append("")
            total_new += site['new_this_week']
        
        report_lines.append(f"🎯 TOTAL NEW ITEMS THIS WEEK: {total_new}")
        report_lines.append("")
        
        report_lines.append("📈 RECENT SCRAPING RUNS:")
        for run in stats["recent_runs"][:5]:
            report_lines.append(f"  • {run['site']} - {run['timestamp']}")
            report_lines.append(f"    Found: {run['items_found']}, New: {run['new_items']}")
        
        report_lines.append("")
        report_lines.append("📁 Data files are saved in: " + str(self.data_dir))
        
        return "\n".join(report_lines)
    
    def get_new_items_by_site(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get new items organized by site"""
        new_items_by_site = {}
        
        for scraper_key, config in self.scrapers.items():
            site_name = config["name"]
            new_items = self.db.get_new_items_since(site_name, days)
            if new_items:
                new_items_by_site[site_name] = new_items
        
        return new_items_by_site

async def main():
    """Main function for running weekly scraper"""
    scraper = WeeklyScraper()
    
    # Run all scrapers
    results = await scraper.run_all_scrapers()
    
    # Generate and save report
    report = scraper.generate_weekly_report()
    
    # Save report to file
    report_file = scraper.data_dir / f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Print report
    print(report)
    print(f"\nReport saved to: {report_file}")
    
    # Print new items summary
    new_items = scraper.get_new_items_by_site()
    if new_items:
        print("\n🆕 NEW ITEMS DETAILS:")
        for site, items in new_items.items():
            print(f"\n{site} ({len(items)} new items):")
            for item in items[:5]:  # Show first 5
                title = item.get('title', 'No title')
                url = item.get('url', 'No URL')
                print(f"  • {title}")
                print(f"    {url}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")

if __name__ == "__main__":
    asyncio.run(main())