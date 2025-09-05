#!/usr/bin/env python3
"""
Notification system for scraping results
Supports Mac system notifications, email, and console output
"""

import json
import logging
import smtplib
from datetime import datetime
from email import mime
from email.mime import text as mime_text
from email.mime import multipart as mime_multipart
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import sys
import os

logger = logging.getLogger(__name__)

class NotificationConfig:
    def __init__(self, config_file: str = "notification_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "notifications": {
                "system": {
                    "enabled": True,
                    "platform": "auto"  # auto, mac, linux, windows
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": []
                },
                "console": {
                    "enabled": True,
                    "verbose": True
                }
            },
            "thresholds": {
                "min_new_items_to_notify": 1,
                "notify_on_errors": True,
                "notify_on_zero_results": False
            }
        }
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def setup_email(self, smtp_server: str, smtp_port: int, username: str, 
                   password: str, from_email: str, to_emails: List[str]):
        """Configure email notifications"""
        self.config["notifications"]["email"] = {
            "enabled": True,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_email": from_email,
            "to_emails": to_emails
        }
        self.save_config()

class NotificationManager:
    def __init__(self, config_file: str = "notification_config.json"):
        self.config = NotificationConfig(config_file)
        self.platform = self._detect_platform()
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        platform_config = self.config.config["notifications"]["system"]["platform"]
        
        if platform_config != "auto":
            return platform_config
        
        if sys.platform == "darwin":
            return "mac"
        elif sys.platform.startswith("linux"):
            return "linux"
        elif sys.platform.startswith("win"):
            return "windows"
        else:
            return "unknown"
    
    def send_system_notification(self, title: str, message: str, urgency: str = "normal"):
        """Send system notification based on platform"""
        if not self.config.config["notifications"]["system"]["enabled"]:
            return
        
        try:
            if self.platform == "mac":
                self._send_mac_notification(title, message)
            elif self.platform == "linux":
                self._send_linux_notification(title, message, urgency)
            elif self.platform == "windows":
                self._send_windows_notification(title, message)
            else:
                logger.warning(f"System notifications not supported on platform: {self.platform}")
        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
    
    def _send_mac_notification(self, title: str, message: str):
        """Send notification on macOS using osascript"""
        script = f'''
        display notification "{message}" with title "{title}"
        '''
        subprocess.run(["osascript", "-e", script], check=True)
    
    def _send_linux_notification(self, title: str, message: str, urgency: str = "normal"):
        """Send notification on Linux using notify-send"""
        subprocess.run([
            "notify-send", 
            f"--urgency={urgency}",
            title, 
            message
        ], check=True)
    
    def _send_windows_notification(self, title: str, message: str):
        """Send notification on Windows using plyer"""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=10
            )
        except ImportError:
            logger.error("plyer not installed, cannot send Windows notification")
    
    def send_email(self, subject: str, body: str, is_html: bool = False):
        """Send email notification"""
        email_config = self.config.config["notifications"]["email"]
        
        if not email_config["enabled"]:
            return
        
        if not email_config["to_emails"]:
            logger.warning("No email recipients configured")
            return
        
        try:
            msg = mime_multipart.MIMEMultipart('alternative')
            msg['From'] = email_config["from_email"]
            msg['To'] = ', '.join(email_config["to_emails"])
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(mime_text.MIMEText(body, 'html'))
            else:
                msg.attach(mime_text.MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                
                for recipient in email_config["to_emails"]:
                    server.send_message(msg, to_addrs=[recipient])
            
            logger.info(f"Email sent to {len(email_config['to_emails'])} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def notify_scraping_results(self, results: Dict[str, Any]):
        """Send notifications based on scraping results"""
        total_new_items = results.get("total_new_items", 0)
        duration = results.get("duration_seconds", 0)
        timestamp = results.get("run_timestamp", "")
        
        # Check if we should notify
        min_items = self.config.config["thresholds"]["min_new_items_to_notify"]
        if total_new_items < min_items and total_new_items > 0:
            return
        
        # Generate notification content
        if total_new_items == 0:
            if not self.config.config["thresholds"]["notify_on_zero_results"]:
                return
            title = "📊 Weekly Scraping Complete"
            message = f"No new items found. Scraping completed in {duration:.1f}s"
            urgency = "low"
        else:
            title = f"🆕 {total_new_items} New Apps Found!"
            message = f"Weekly scraping found {total_new_items} new items in {duration:.1f}s"
            urgency = "normal" if total_new_items < 10 else "high"
        
        # Console notification
        if self.config.config["notifications"]["console"]["enabled"]:
            print(f"\n{title}")
            print(f"{message}")
            
            if self.config.config["notifications"]["console"]["verbose"] and total_new_items > 0:
                self._print_detailed_results(results)
        
        # System notification
        self.send_system_notification(title, message, urgency)
        
        # Email notification
        if total_new_items > 0 or self.config.config["thresholds"]["notify_on_zero_results"]:
            email_body = self._generate_email_body(results)
            self.send_email(title, email_body, is_html=True)
    
    def _print_detailed_results(self, results: Dict[str, Any]):
        """Print detailed results to console"""
        print("\n📋 DETAILED RESULTS:")
        
        scrapers = results.get("scrapers", {})
        for scraper_name, scraper_result in scrapers.items():
            if not scraper_result.get("success", False):
                continue
            
            site_name = scraper_result.get("site", scraper_name)
            new_items = scraper_result.get("new_items", 0)
            total_items = scraper_result.get("total_items", 0)
            
            print(f"  • {site_name}: {new_items} new (of {total_items} total)")
    
    def _generate_email_body(self, results: Dict[str, Any]) -> str:
        """Generate HTML email body"""
        total_new = results.get("total_new_items", 0)
        duration = results.get("duration_seconds", 0)
        timestamp = results.get("run_timestamp", "")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2>📊 Weekly App Scraping Report</h2>
            <p><strong>Run Time:</strong> {timestamp}</p>
            <p><strong>Duration:</strong> {duration:.1f} seconds</p>
            <p><strong>Total New Items:</strong> {total_new}</p>
            
            <h3>🌐 Site Results:</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Site</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">New Items</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Total Items</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th>
                </tr>
        """
        
        scrapers = results.get("scrapers", {})
        for scraper_name, scraper_result in scrapers.items():
            site_name = scraper_result.get("site", scraper_name)
            new_items = scraper_result.get("new_items", 0)
            total_items = scraper_result.get("total_items", 0)
            success = scraper_result.get("success", False)
            
            status = "✅ Success" if success else "❌ Failed"
            row_color = "#fff" if success else "#ffe6e6"
            
            html += f"""
                <tr style="background-color: {row_color};">
                    <td style="border: 1px solid #ddd; padding: 8px;">{site_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{new_items}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{total_items}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{status}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                This is an automated report from your weekly app scraping system.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def notify_error(self, error_message: str, context: str = ""):
        """Send error notification"""
        if not self.config.config["thresholds"]["notify_on_errors"]:
            return
        
        title = "❌ Scraping Error"
        message = f"Error in {context}: {error_message}"
        
        # Console
        if self.config.config["notifications"]["console"]["enabled"]:
            print(f"\n{title}")
            print(f"{message}")
        
        # System notification
        self.send_system_notification(title, message, "critical")
        
        # Email
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2>❌ Scraping System Error</h2>
            <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
            <p><strong>Context:</strong> {context}</p>
            <p><strong>Error:</strong> {error_message}</p>
            
            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                Please check the scraping system and logs for more details.
            </p>
        </body>
        </html>
        """
        
        self.send_email(title, email_body, is_html=True)

def setup_notifications():
    """Interactive setup for notifications"""
    config = NotificationConfig()
    
    print("🔔 Notification Setup")
    print("=" * 30)
    
    # System notifications
    system_enabled = input("Enable system notifications? (y/n) [y]: ").strip().lower()
    system_enabled = system_enabled != 'n'
    config.config["notifications"]["system"]["enabled"] = system_enabled
    
    # Email setup
    email_enabled = input("Enable email notifications? (y/n) [n]: ").strip().lower()
    if email_enabled == 'y':
        print("\n📧 Email Configuration:")
        smtp_server = input("SMTP server [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
        smtp_port = int(input("SMTP port [587]: ").strip() or "587")
        username = input("Email username: ").strip()
        password = input("Email password (use app password for Gmail): ").strip()
        from_email = input("From email: ").strip() or username
        
        to_emails = []
        print("Enter recipient emails (one per line, empty line to finish):")
        while True:
            email = input("  Email: ").strip()
            if not email:
                break
            to_emails.append(email)
        
        config.setup_email(smtp_server, smtp_port, username, password, from_email, to_emails)
    
    # Thresholds
    min_items = input("Minimum new items to trigger notification [1]: ").strip()
    try:
        min_items = int(min_items) if min_items else 1
    except ValueError:
        min_items = 1
    
    config.config["thresholds"]["min_new_items_to_notify"] = min_items
    
    notify_errors = input("Notify on errors? (y/n) [y]: ").strip().lower()
    config.config["thresholds"]["notify_on_errors"] = notify_errors != 'n'
    
    # Save configuration
    config.save_config()
    
    print(f"\n✅ Configuration saved to {config.config_file}")
    print("Test the setup by running a scraping job!")

if __name__ == "__main__":
    setup_notifications()