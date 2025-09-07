#!/usr/bin/env python3
"""
Scheduler system for running scrapers weekly
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
import signal
import sys
from pathlib import Path

from weekly_scraper import WeeklyScraper

logger = logging.getLogger(__name__)

class ScrapingScheduler:
    def __init__(self):
        self.weekly_scraper = WeeklyScraper()
        self.is_running = True
        self.current_task = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.is_running = False
        if self.current_task:
            self.current_task.cancel()
        sys.exit(0)
    
    async def run_scheduled_scraping(self):
        """Run the weekly scraping job"""
        try:
            logger.info("🚀 Starting scheduled weekly scraping...")
            self.current_task = asyncio.create_task(self.weekly_scraper.run_all_scrapers())
            results = await self.current_task
            
            # Generate reports
            report = self.weekly_scraper.generate_weekly_report()
            
            # Save report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = Path(f"scheduled_report_{timestamp}.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"✅ Weekly scraping completed successfully!")
            logger.info(f"📄 Report saved to: {report_file}")
            
            # Log summary
            total_new = sum(r.get('new_items', 0) for r in results['scrapers'].values() if r.get('success', False))
            logger.info(f"📊 Summary: {total_new} total new items found")
            
            return results
            
        except asyncio.CancelledError:
            logger.info("Scraping task was cancelled")
            raise
        except Exception as e:
            logger.error(f"❌ Error during scheduled scraping: {str(e)}")
            raise
        finally:
            self.current_task = None
    
    def schedule_weekly_job(self, day: str = "monday", time_str: str = "09:00"):
        """Schedule the weekly job"""
        logger.info(f"📅 Scheduling weekly scraping for every {day.title()} at {time_str}")
        
        # Schedule the job
        getattr(schedule.every(), day.lower()).at(time_str).do(
            lambda: asyncio.run(self.run_scheduled_scraping())
        )
    
    def run_scheduler(self, check_interval: int = 60):
        """Run the scheduler loop"""
        logger.info(f"🔄 Scheduler started, checking every {check_interval} seconds")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(check_interval)
        
        logger.info("Scheduler stopped")

def run_scheduler_daemon(day: str = "monday", time_str: str = "09:00"):
    """Run scheduler as a daemon"""
    scheduler = ScrapingScheduler()
    scheduler.schedule_weekly_job(day, time_str)
    scheduler.run_scheduler()

def run_once_now():
    """Run scraping once immediately (for testing)"""
    async def _run():
        scraper = WeeklyScraper()
        results = await scraper.run_all_scrapers()
        
        # Generate and print report
        report = scraper.generate_weekly_report()
        print(report)
        
        return results
    
    return asyncio.run(_run())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scraping Scheduler")
    parser.add_argument("--mode", choices=["schedule", "run-once"], default="schedule",
                       help="Mode: schedule for daemon, run-once for immediate execution")
    parser.add_argument("--day", default="monday", 
                       help="Day of week for scheduled runs (default: monday)")
    parser.add_argument("--time", default="09:00",
                       help="Time for scheduled runs in HH:MM format (default: 09:00)")
    
    args = parser.parse_args()
    
    if args.mode == "run-once":
        print("Running scraping job once...")
        results = run_once_now()
        print("✅ Scraping completed!")
    else:
        print(f"Starting scheduler daemon - will run every {args.day.title()} at {args.time}")
        run_scheduler_daemon(args.day, args.time)