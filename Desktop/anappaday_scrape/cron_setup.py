#!/usr/bin/env python3
"""
Cron job setup utility for Mac and Linux
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

class CronManager:
    def __init__(self):
        self.current_dir = Path.cwd().absolute()
        self.python_path = sys.executable
        self.script_path = self.current_dir / "manage_scraping.py"
        
    def generate_cron_entry(self, minute: int = 0, hour: int = 9, day_of_week: int = 1):
        """
        Generate cron entry for scraping
        day_of_week: 0=Sunday, 1=Monday, 2=Tuesday, etc.
        """
        log_file = self.current_dir / "logs" / "cron.log"
        
        # Ensure logs directory exists
        log_file.parent.mkdir(exist_ok=True)
        
        # Create cron entry
        cron_line = (
            f"{minute} {hour} * * {day_of_week} "
            f"cd {self.current_dir} && "
            f"{self.python_path} {self.script_path} run-once "
            f">> {log_file} 2>&1"
        )
        
        return cron_line
    
    def get_current_crontab(self):
        """Get current user's crontab"""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            # No crontab exists yet
            return []
    
    def install_cron_job(self, minute: int = 0, hour: int = 9, day_of_week: int = 1, 
                        overwrite: bool = False):
        """Install the cron job"""
        cron_entry = self.generate_cron_entry(minute, hour, day_of_week)
        
        # Check if our job already exists
        current_crontab = self.get_current_crontab()
        scraper_lines = [line for line in current_crontab if "manage_scraping.py" in line]
        
        if scraper_lines and not overwrite:
            print("❗ Scraping cron job already exists:")
            for line in scraper_lines:
                print(f"   {line}")
            
            response = input("Overwrite existing job? (y/n) [n]: ").strip().lower()
            if response != 'y':
                print("❌ Cancelled")
                return False
            
            # Remove existing scraper lines
            current_crontab = [line for line in current_crontab if "manage_scraping.py" not in line]
        
        # Add our new job
        new_crontab = current_crontab + [cron_entry]
        
        # Write new crontab
        try:
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate('\n'.join(new_crontab) + '\n')
            
            if process.returncode == 0:
                print("✅ Cron job installed successfully!")
                print(f"📅 Will run: {self._format_schedule(minute, hour, day_of_week)}")
                print(f"📂 Logs: {self.current_dir}/logs/cron.log")
                return True
            else:
                print("❌ Failed to install cron job")
                return False
                
        except Exception as e:
            print(f"❌ Error installing cron job: {e}")
            return False
    
    def uninstall_cron_job(self):
        """Remove scraping cron jobs"""
        current_crontab = self.get_current_crontab()
        scraper_lines = [line for line in current_crontab if "manage_scraping.py" in line]
        
        if not scraper_lines:
            print("ℹ️ No scraping cron jobs found")
            return True
        
        print("Found scraping cron jobs:")
        for line in scraper_lines:
            print(f"   {line}")
        
        response = input("Remove all scraping jobs? (y/n) [n]: ").strip().lower()
        if response != 'y':
            print("❌ Cancelled")
            return False
        
        # Remove scraper lines
        new_crontab = [line for line in current_crontab if "manage_scraping.py" not in line]
        
        try:
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate('\n'.join(new_crontab) + '\n')
            
            if process.returncode == 0:
                print("✅ Cron jobs removed successfully!")
                return True
            else:
                print("❌ Failed to remove cron jobs")
                return False
                
        except Exception as e:
            print(f"❌ Error removing cron jobs: {e}")
            return False
    
    def list_cron_jobs(self):
        """List all current cron jobs"""
        current_crontab = self.get_current_crontab()
        
        if not current_crontab:
            print("ℹ️ No cron jobs found")
            return
        
        print("📋 Current cron jobs:")
        for i, line in enumerate(current_crontab, 1):
            if line.strip() and not line.startswith('#'):
                is_scraper = "manage_scraping.py" in line
                prefix = "🔍" if is_scraper else "  "
                print(f"{prefix} {i}. {line}")
    
    def _format_schedule(self, minute: int, hour: int, day_of_week: int) -> str:
        """Format schedule for human reading"""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_name = days[day_of_week]
        time_str = f"{hour:02d}:{minute:02d}"
        
        return f"Every {day_name} at {time_str}"
    
    def create_launchd_plist(self, minute: int = 0, hour: int = 9, day_of_week: int = 1):
        """Create macOS LaunchAgent plist file (alternative to cron)"""
        if sys.platform != "darwin":
            print("❌ LaunchAgent only available on macOS")
            return False
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.weekly-scraper</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_path}</string>
        <string>{self.script_path}</string>
        <string>run-once</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{self.current_dir}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>{minute}</integer>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Weekday</key>
        <integer>{day_of_week}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{self.current_dir}/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.current_dir}/logs/launchd.log</string>
</dict>
</plist>'''
        
        # Save plist file
        home_dir = Path.home()
        launch_agents_dir = home_dir / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        
        plist_file = launch_agents_dir / "com.user.weekly-scraper.plist"
        
        with open(plist_file, 'w') as f:
            f.write(plist_content)
        
        print(f"✅ LaunchAgent plist created: {plist_file}")
        print("To load the agent:")
        print(f"  launchctl load {plist_file}")
        print("To unload:")
        print(f"  launchctl unload {plist_file}")
        print("To start immediately:")
        print("  launchctl start com.user.weekly-scraper")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cron Job Setup for Weekly Scraping")
    
    subparsers = parser.add_subparsers(dest='action', help='Available actions')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install cron job')
    install_parser.add_argument('--minute', type=int, default=0, help='Minute (0-59)')
    install_parser.add_argument('--hour', type=int, default=9, help='Hour (0-23)')
    install_parser.add_argument('--day', type=int, default=1, 
                               help='Day of week (0=Sunday, 1=Monday, etc.)')
    install_parser.add_argument('--overwrite', action='store_true', 
                               help='Overwrite existing cron job')
    
    # Other commands
    subparsers.add_parser('uninstall', help='Remove cron job')
    subparsers.add_parser('list', help='List current cron jobs')
    subparsers.add_parser('generate', help='Generate cron entry without installing')
    
    # LaunchAgent for Mac
    launchd_parser = subparsers.add_parser('launchd', help='Create macOS LaunchAgent (alternative to cron)')
    launchd_parser.add_argument('--minute', type=int, default=0, help='Minute (0-59)')
    launchd_parser.add_argument('--hour', type=int, default=9, help='Hour (0-23)')
    launchd_parser.add_argument('--day', type=int, default=1, 
                               help='Day of week (0=Sunday, 1=Monday, etc.)')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return
    
    cron_manager = CronManager()
    
    if args.action == 'install':
        cron_manager.install_cron_job(
            args.minute, args.hour, args.day, args.overwrite
        )
    elif args.action == 'uninstall':
        cron_manager.uninstall_cron_job()
    elif args.action == 'list':
        cron_manager.list_cron_jobs()
    elif args.action == 'generate':
        minute = int(input("Minute (0-59) [0]: ") or 0)
        hour = int(input("Hour (0-23) [9]: ") or 9)
        day = int(input("Day of week (0=Sunday, 1=Monday, etc.) [1]: ") or 1)
        
        cron_entry = cron_manager.generate_cron_entry(minute, hour, day)
        print("\nGenerated cron entry:")
        print(cron_entry)
        print("\nTo install manually:")
        print("1. Run: crontab -e")
        print("2. Add the line above")
        print("3. Save and exit")
    elif args.action == 'launchd':
        cron_manager.create_launchd_plist(args.minute, args.hour, args.day)

if __name__ == "__main__":
    main()