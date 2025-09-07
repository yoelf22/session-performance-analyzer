# 🔔 Cron Jobs & Notifications Setup Guide

Complete guide for setting up automated weekly scraping with notifications on Mac and Linux.

## 🎯 What You Need Running

**Nothing needs to be running continuously!** ✨ The system works as **one-off processes**:

### ✅ Requirements (Always Needed)
- **Python 3.8+** installed on your system
- **Playwright browsers** (installed via `playwright install`)
- **Network connection** during scraping
- **Disk space** (~10MB, grows slowly over time)

### ❌ What You DON'T Need Running
- No servers or daemons required
- No database servers (uses SQLite files)
- No web browsers open (headless mode)
- No terminal windows open continuously

## 🚀 Quick Setup (Recommended Path)

### 1. Initial Setup
```bash
# Install dependencies and browsers
python manage_scraping.py setup

# Configure notifications  
python manage_scraping.py setup-notifications

# Install cron job for weekly execution
python manage_scraping.py setup-cron
```

### 2. Test Everything
```bash
# Run once to test (this will trigger notifications)
python manage_scraping.py run-once
```

That's it! 🎉 Your system will now run weekly and send notifications.

## 📱 Notification Types

### 1. Mac System Notifications (macOS)
- Native macOS notification center alerts
- Shows number of new apps found
- Appears in notification center
- **No setup required** - works automatically

### 2. Email Notifications 
- Detailed HTML reports sent via email
- Works with Gmail, Outlook, any SMTP server
- Includes tables of new apps with links
- **Setup required** - see configuration below

### 3. Console Output
- Detailed results printed to terminal/logs
- Always enabled for debugging
- Saved to `logs/cron.log` when run via cron

## 🔧 Notification Configuration

### Interactive Setup
```bash
python manage_scraping.py setup-notifications
```

This will ask for:
- Enable system notifications? (recommended: yes)
- Enable email notifications? (optional)
- Email server settings (if email enabled)
- Minimum items threshold for notifications
- Error notification preferences

### Manual Email Configuration (Gmail Example)

1. **Enable 2-Factor Authentication** in Gmail
2. **Generate App Password**: 
   - Go to Google Account settings
   - Security → App passwords
   - Create password for "Mail"
3. **Run notification setup**:
   ```bash
   python manage_scraping.py setup-notifications
   ```
   When prompted:
   - SMTP server: `smtp.gmail.com`
   - SMTP port: `587` 
   - Username: `your.email@gmail.com`
   - Password: `your-16-character-app-password`
   - Recipients: Enter email addresses to notify

### Configuration File
Settings saved to `notification_config.json`:

```json
{
  "notifications": {
    "system": {
      "enabled": true,
      "platform": "auto"
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your.email@gmail.com",
      "password": "app-password-here",
      "to_emails": ["recipient@gmail.com"]
    }
  },
  "thresholds": {
    "min_new_items_to_notify": 1,
    "notify_on_errors": true
  }
}
```

## ⏰ Cron Job Setup

### Automatic Setup (Recommended)
```bash
python manage_scraping.py setup-cron
```

Choose from:
- **Option 1**: Monday 9:00 AM (default)
- **Option 2**: Custom schedule

### Manual Cron Setup
```bash
# Edit your crontab
crontab -e

# Add one of these lines:

# Every Monday at 9:00 AM
0 9 * * 1 cd /path/to/anappaday_scrape && python manage_scraping.py run-once >> logs/cron.log 2>&1

# Every Friday at 6:00 PM  
0 18 * * 5 cd /path/to/anappaday_scrape && python manage_scraping.py run-once >> logs/cron.log 2>&1

# Every 3 days at 2:00 PM
0 14 */3 * * cd /path/to/anappaday_scrape && python manage_scraping.py run-once >> logs/cron.log 2>&1
```

### Advanced Cron Management
```bash
# Install specific schedule
python cron_setup.py install --hour 14 --minute 30 --day 2  # Tuesday 2:30 PM

# List current cron jobs
python cron_setup.py list

# Remove scraping cron jobs
python cron_setup.py uninstall

# Generate cron entry without installing
python cron_setup.py generate
```

## 🍎 macOS Alternative: LaunchAgent

For macOS users who prefer LaunchAgent over cron:

```bash
# Create LaunchAgent plist
python cron_setup.py launchd --hour 9 --minute 0 --day 1

# Load the agent
launchctl load ~/Library/LaunchAgents/com.user.weekly-scraper.plist

# Start immediately (for testing)
launchctl start com.user.weekly-scraper
```

## 📊 What You'll Receive

### Mac System Notification Example
```
🆕 5 New Apps Found!
Weekly scraping found 5 new items in 45.2s
```

### Email Report Example
```
Subject: 🆕 5 New Apps Found!

📊 Weekly App Scraping Report
Run Time: 2025-08-26 09:00:15
Duration: 45.2 seconds
Total New Items: 5

🌐 Site Results:
┌─────────────────┬───────────┬─────────────┬────────┐
│ Site            │ New Items │ Total Items │ Status │
├─────────────────┼───────────┼─────────────┼────────┤
│ Bolt.new Gallery│     3     │     255     │   ✅   │
│ Lovable Launched│     2     │     109     │   ✅   │
│ Base44 Catalog  │     0     │     160     │   ✅   │
│ Replit Gallery  │     0     │      19     │   ✅   │
└─────────────────┴───────────┴─────────────┴────────┘
```

### Console/Log Output
```
📊 WEEKLY SCRAPING REPORT
==================================================
Total new items this week: 5

🌐 SITES SUMMARY:
  • Bolt.new Gallery: 3 new items
  • Lovable Launched: 2 new items

📋 DETAILED RESULTS:
  • Bolt.new Gallery: 3 new (of 255 total)
  • Lovable Launched: 2 new (of 109 total)
```

## 🔍 Monitoring & Debugging

### Check if Cron Job is Running
```bash
# View cron logs
tail -f logs/cron.log

# Check cron job is installed
crontab -l | grep manage_scraping

# Test the exact command cron will run
cd /path/to/anappaday_scrape && python manage_scraping.py run-once
```

### View Notification Logs
```bash
# Application logs
tail -f scraping.log

# Cron execution logs  
tail -f logs/cron.log

# Mac system logs (for LaunchAgent)
tail -f logs/launchd.log
```

### Common Issues & Solutions

**1. Cron Job Not Running**
```bash
# Check cron service is running (Linux)
sudo systemctl status cron

# Check cron job syntax
python cron_setup.py list

# Test command manually
cd /full/path/to/anappaday_scrape && python manage_scraping.py run-once
```

**2. Notifications Not Working**
```bash
# Test notifications manually
python -c "
from notifications import NotificationManager
nm = NotificationManager()
nm.send_system_notification('Test', 'Testing notifications')
"

# Check config file
cat notification_config.json
```

**3. Mac Notifications Not Appearing**
```bash
# Check notification permissions
# Go to: System Preferences > Notifications > Terminal (or your terminal app)
# Enable "Allow Notifications"

# Test with osascript directly
osascript -e 'display notification "Test message" with title "Test Title"'
```

**4. Email Not Sending**
```bash
# Check email config
python -c "
import json
with open('notification_config.json') as f:
    config = json.load(f)
print('Email enabled:', config['notifications']['email']['enabled'])
print('SMTP server:', config['notifications']['email']['smtp_server'])
print('Recipients:', config['notifications']['email']['to_emails'])
"

# Test email manually (replace with your settings)
python -c "
from notifications import NotificationManager
nm = NotificationManager()
nm.send_email('Test Subject', 'Test message body')
"
```

## 📅 Schedule Examples

| Schedule | Cron Format | Description |
|----------|-------------|-------------|
| Every Monday 9:00 AM | `0 9 * * 1` | Weekly, start of work week |
| Every Friday 6:00 PM | `0 18 * * 5` | Weekly, end of work week |
| Every 3 days 2:00 PM | `0 14 */3 * *` | More frequent checking |
| Twice a week | `0 9 * * 1,5` | Monday and Friday 9 AM |
| Monthly (1st) | `0 9 1 * *` | First day of month 9 AM |

## 🎛️ Customization

### Change Notification Thresholds
Edit `notification_config.json`:
```json
{
  "thresholds": {
    "min_new_items_to_notify": 5,      // Only notify if ≥5 new items
    "notify_on_errors": true,           // Notify on scraping errors  
    "notify_on_zero_results": false     // Don't notify when 0 new items
  }
}
```

### Custom Notification Messages
Modify `notifications.py` methods:
- `notify_scraping_results()` - Main completion notification
- `notify_error()` - Error notifications  
- `_generate_email_body()` - Email HTML template

### Different Email Providers

**Outlook/Hotmail:**
- SMTP server: `smtp-mail.outlook.com`
- Port: `587`
- Use your email and password

**Yahoo:**
- SMTP server: `smtp.mail.yahoo.com`  
- Port: `587`
- Use app password

**Custom SMTP:**
- Use your organization's SMTP settings
- May need different ports (25, 465, 587)

## 🚨 Security Notes

### Email Security
- **Never commit passwords** to version control
- Use **app passwords** instead of account passwords
- Consider using **environment variables**:
  ```bash
  export SCRAPER_EMAIL_PASSWORD="your-app-password"
  ```
  
### File Permissions
```bash
# Secure the config file
chmod 600 notification_config.json

# Secure the entire directory
chmod 755 /path/to/anappaday_scrape
chmod 600 /path/to/anappaday_scrape/*.json
```

---

## 🎉 Summary

Once set up, your system will:

1. **Run automatically** every week via cron
2. **Scrape all sites** for new apps/projects  
3. **Send Mac notification** with count of new items
4. **Email detailed report** to your recipients
5. **Log everything** to files for debugging
6. **Require no ongoing maintenance** ✨

The beauty of this approach is **zero ongoing maintenance** - just set it up once and receive weekly notifications about new discoveries! 🚀