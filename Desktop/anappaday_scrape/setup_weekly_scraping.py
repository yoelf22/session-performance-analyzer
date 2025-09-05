#!/usr/bin/env python3
"""
Setup script for weekly scraping system
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🌐 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        print("✅ Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    dirs = [
        "weekly_scraping_data",
        "logs"
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"  ✅ Created: {dir_name}")

def test_scrapers():
    """Test that scrapers can import correctly"""
    print("🧪 Testing scraper imports...")
    
    try:
        from database import ScrapingDatabase
        from weekly_scraper import WeeklyScraper
        from scheduler import ScrapingScheduler
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def create_systemd_service():
    """Create a systemd service file for Linux"""
    if sys.platform != "linux":
        return
    
    current_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Weekly App Scraper
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={current_dir}
ExecStart={python_path} scheduler.py --mode schedule --day monday --time 09:00
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("/tmp/weekly-scraper.service")
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"📋 Systemd service file created at: {service_file}")
    print("To install the service:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl enable weekly-scraper")
    print("  sudo systemctl start weekly-scraper")

def create_cron_job():
    """Create a cron job entry"""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    cron_line = f"0 9 * * 1 cd {current_dir} && {python_path} scheduler.py --mode run-once >> logs/cron.log 2>&1"
    
    print("📅 Cron job entry (runs every Monday at 9:00 AM):")
    print(f"  {cron_line}")
    print()
    print("To add to crontab:")
    print("  crontab -e")
    print("  Add the line above")

def main():
    print("🚀 Weekly Scraping System Setup")
    print("=" * 40)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Install Playwright browsers
    if not install_playwright_browsers():
        print("❌ Setup failed at Playwright browser installation")
        return False
    
    # Test imports
    if not test_scrapers():
        print("❌ Setup failed at module testing")
        return False
    
    print()
    print("✅ Setup completed successfully!")
    print()
    print("📋 Usage Options:")
    print("1. Run once immediately:")
    print("   python scheduler.py --mode run-once")
    print()
    print("2. Start scheduler daemon:")
    print("   python scheduler.py --mode schedule --day monday --time 09:00")
    print()
    print("3. Run weekly scraper directly:")
    print("   python weekly_scraper.py")
    print()
    
    # Platform-specific scheduling options
    if sys.platform == "linux":
        create_systemd_service()
        print()
    
    create_cron_job()
    
    print()
    print("📊 Data will be saved to:")
    print("  - Database: weekly_scraping_data/scraping_history.db")
    print("  - JSON files: weekly_scraping_data/")
    print("  - Reports: weekly_scraping_data/")
    print("  - Logs: scraping.log")

if __name__ == "__main__":
    main()