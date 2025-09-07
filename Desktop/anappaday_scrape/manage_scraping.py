#!/usr/bin/env python3
"""
Management script for weekly scraping system
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

def setup_system():
    """Run the setup process"""
    print("🚀 Setting up weekly scraping system...")
    from setup_weekly_scraping import main
    main()

def run_once():
    """Run scraping once immediately"""
    print("🔄 Running all scrapers once...")
    from scheduler import run_once_now
    results = run_once_now()
    print("✅ Scraping completed!")
    return results

def start_scheduler(day="monday", time="09:00"):
    """Start the weekly scheduler"""
    print(f"📅 Starting weekly scheduler ({day.title()} at {time})...")
    from scheduler import run_scheduler_daemon
    run_scheduler_daemon(day, time)

def show_stats():
    """Show current statistics"""
    try:
        from database import ScrapingDatabase
        
        db = ScrapingDatabase()
        stats = db.get_stats()
        
        print("📊 SCRAPING STATISTICS")
        print("=" * 40)
        
        if not stats["sites"]:
            print("No data found. Run scraping at least once to see statistics.")
            return
        
        total_items = sum(site["tracked_items"] for site in stats["sites"])
        total_new_week = sum(site["new_this_week"] for site in stats["sites"])
        
        print(f"Total tracked items: {total_items}")
        print(f"New items this week: {total_new_week}")
        print()
        
        print("Sites:")
        for site in stats["sites"]:
            print(f"  • {site['name']}")
            print(f"    - Tracked items: {site['tracked_items']}")
            print(f"    - New this week: {site['new_this_week']}")
            print(f"    - Last scraped: {site['last_scraped'] or 'Never'}")
            print()
        
        if stats["recent_runs"]:
            print("Recent runs:")
            for run in stats["recent_runs"][:5]:
                print(f"  • {run['site']} - {run['timestamp']}")
                print(f"    Found: {run['items_found']}, New: {run['new_items']}")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        print("Make sure you've run scraping at least once.")

def show_new_items(days=7):
    """Show new items from recent days"""
    try:
        from weekly_scraper import WeeklyScraper
        
        scraper = WeeklyScraper()
        new_items = scraper.get_new_items_by_site(days)
        
        print(f"🆕 NEW ITEMS (Last {days} days)")
        print("=" * 40)
        
        if not new_items:
            print("No new items found.")
            return
        
        total = sum(len(items) for items in new_items.values())
        print(f"Total new items: {total}")
        print()
        
        for site_name, items in new_items.items():
            print(f"{site_name} ({len(items)} items):")
            for item in items:
                title = item.get('title', 'No title')[:50]
                url = item.get('url', 'No URL')
                first_seen = item.get('first_seen', '')
                print(f"  • {title}")
                if url != 'No URL':
                    print(f"    {url}")
                print(f"    First seen: {first_seen}")
                print()
    
    except Exception as e:
        print(f"❌ Error getting new items: {e}")

def setup_notifications():
    """Setup notifications"""
    print("🔔 Setting up notifications...")
    from notifications import setup_notifications
    setup_notifications()

def setup_cron():
    """Setup cron job"""
    print("⏰ Setting up cron job...")
    from cron_setup import CronManager
    
    manager = CronManager()
    
    print("Current schedule options:")
    print("1. Monday 9:00 AM (default)")
    print("2. Custom schedule")
    
    choice = input("Choose option (1-2) [1]: ").strip() or "1"
    
    if choice == "1":
        minute, hour, day = 0, 9, 1
    else:
        minute = int(input("Minute (0-59) [0]: ") or 0)
        hour = int(input("Hour (0-23) [9]: ") or 9)
        day = int(input("Day of week (0=Sunday, 1=Monday, etc.) [1]: ") or 1)
    
    success = manager.install_cron_job(minute, hour, day)
    if success:
        print("✅ Cron job installed!")
        print("💡 Tip: Set up notifications to get notified when new items are found")

def backup_data():
    """Create a backup of the database and recent files"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backup_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        data_dir = Path("weekly_scraping_data")
        if data_dir.exists():
            shutil.copytree(data_dir, backup_dir / "weekly_scraping_data")
            print(f"✅ Data backed up to: {backup_dir}")
        else:
            print("❌ No data directory found to backup")
    
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Weekly Scraping System Manager")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Set up the scraping system')
    
    # Run once command
    subparsers.add_parser('run-once', help='Run all scrapers once immediately')
    
    # Start scheduler command  
    scheduler_parser = subparsers.add_parser('start-scheduler', help='Start weekly scheduler daemon')
    scheduler_parser.add_argument('--day', default='monday', help='Day of week (default: monday)')
    scheduler_parser.add_argument('--time', default='09:00', help='Time in HH:MM format (default: 09:00)')
    
    # Stats command
    subparsers.add_parser('stats', help='Show current statistics')
    
    # New items command
    new_items_parser = subparsers.add_parser('new-items', help='Show new items from recent days')
    new_items_parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    
    # Backup command
    subparsers.add_parser('backup', help='Create a backup of all data')
    
    # Setup commands
    subparsers.add_parser('setup-notifications', help='Setup notification preferences')
    subparsers.add_parser('setup-cron', help='Setup cron job for weekly scheduling')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'setup':
            setup_system()
        elif args.command == 'run-once':
            run_once()
        elif args.command == 'start-scheduler':
            start_scheduler(args.day, args.time)
        elif args.command == 'stats':
            show_stats()
        elif args.command == 'new-items':
            show_new_items(args.days)
        elif args.command == 'backup':
            backup_data()
        elif args.command == 'setup-notifications':
            setup_notifications()
        elif args.command == 'setup-cron':
            setup_cron()
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()