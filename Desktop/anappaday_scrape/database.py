#!/usr/bin/env python3
"""
Database system for tracking scraped items and managing deduplication
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

class ScrapingDatabase:
    def __init__(self, db_path: str = "scraping_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                last_scraped TIMESTAMP,
                total_items INTEGER DEFAULT 0
            )
        """)
        
        # Create items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                item_hash TEXT UNIQUE NOT NULL,
                title TEXT,
                url TEXT,
                author TEXT,
                description TEXT,
                image_url TEXT,
                metadata TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )
        """)
        
        # Create scraping_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                items_found INTEGER,
                new_items INTEGER,
                updated_items INTEGER,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_hash ON items (item_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_site_id ON items (site_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON items (first_seen)")
        
        conn.commit()
        conn.close()
    
    def register_site(self, name: str, url: str) -> int:
        """Register a site for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO sites (name, url) VALUES (?, ?)
        """, (name, url))
        
        cursor.execute("SELECT id FROM sites WHERE name = ?", (name,))
        site_id = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        return site_id
    
    def generate_item_hash(self, item: Dict[str, Any]) -> str:
        """Generate a unique hash for an item based on key fields"""
        # Use title + url as the unique identifier
        key_fields = [
            str(item.get('title', '')).strip().lower(),
            str(item.get('url', '')).strip(),
            str(item.get('name', '')).strip().lower()  # For different naming conventions
        ]
        
        # Create hash from non-empty key fields
        hash_input = '|'.join(field for field in key_fields if field)
        if not hash_input:
            # Fallback to description or image if no title/url
            hash_input = str(item.get('description', ''))[:100] + str(item.get('image_url', ''))
        
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def find_new_items(self, site_name: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find items that are new since last scraping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get site ID
        cursor.execute("SELECT id FROM sites WHERE name = ?", (site_name,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return items  # All items are new if site not registered
        
        site_id = result[0]
        
        # Get existing item hashes
        cursor.execute("SELECT item_hash FROM items WHERE site_id = ? AND is_active = 1", (site_id,))
        existing_hashes = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        
        # Filter for new items
        new_items = []
        for item in items:
            item_hash = self.generate_item_hash(item)
            if item_hash not in existing_hashes:
                item['_hash'] = item_hash  # Add hash for later use
                new_items.append(item)
        
        return new_items
    
    def save_scraping_results(self, site_name: str, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Save scraping results and return statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure site is registered
        site_id = self.register_site(site_name, "")
        
        # Update site last_scraped timestamp
        cursor.execute("""
            UPDATE sites SET last_scraped = CURRENT_TIMESTAMP, total_items = ?
            WHERE id = ?
        """, (len(items), site_id))
        
        # Process each item
        new_items = 0
        updated_items = 0
        
        for item in items:
            item_hash = item.get('_hash') or self.generate_item_hash(item)
            
            # Check if item exists
            cursor.execute("SELECT id, last_seen FROM items WHERE item_hash = ?", (item_hash,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing item
                cursor.execute("""
                    UPDATE items SET 
                        last_seen = CURRENT_TIMESTAMP,
                        title = ?,
                        url = ?,
                        author = ?,
                        description = ?,
                        image_url = ?,
                        metadata = ?
                    WHERE item_hash = ?
                """, (
                    item.get('title') or item.get('name'),
                    item.get('url') or item.get('app_url'),
                    item.get('author') or item.get('creator'),
                    item.get('description'),
                    item.get('image_url') or item.get('logo_url'),
                    json.dumps({k: v for k, v in item.items() if k not in ['title', 'name', 'url', 'app_url', 'author', 'creator', 'description', 'image_url', 'logo_url']}),
                    item_hash
                ))
                updated_items += 1
            else:
                # Insert new item
                cursor.execute("""
                    INSERT INTO items (
                        site_id, item_hash, title, url, author, description, 
                        image_url, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    site_id,
                    item_hash,
                    item.get('title') or item.get('name'),
                    item.get('url') or item.get('app_url'),
                    item.get('author') or item.get('creator'),
                    item.get('description'),
                    item.get('image_url') or item.get('logo_url'),
                    json.dumps({k: v for k, v in item.items() if k not in ['title', 'name', 'url', 'app_url', 'author', 'creator', 'description', 'image_url', 'logo_url']})
                ))
                new_items += 1
        
        # Record scraping run
        cursor.execute("""
            INSERT INTO scraping_runs (
                site_id, items_found, new_items, updated_items, status
            ) VALUES (?, ?, ?, ?, 'success')
        """, (site_id, len(items), new_items, updated_items))
        
        conn.commit()
        conn.close()
        
        return {
            'total_items': len(items),
            'new_items': new_items,
            'updated_items': updated_items
        }
    
    def get_new_items_since(self, site_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get items that are new within the specified number of days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.title, i.url, i.author, i.description, i.image_url, 
                   i.metadata, i.first_seen
            FROM items i
            JOIN sites s ON i.site_id = s.id
            WHERE s.name = ? 
            AND i.first_seen >= datetime('now', '-{} days')
            AND i.is_active = 1
            ORDER BY i.first_seen DESC
        """.format(days), (site_name,))
        
        results = []
        for row in cursor.fetchall():
            item = {
                'title': row[0],
                'url': row[1],
                'author': row[2],
                'description': row[3],
                'image_url': row[4],
                'first_seen': row[6]
            }
            
            # Add metadata
            if row[5]:
                try:
                    metadata = json.loads(row[5])
                    item.update(metadata)
                except:
                    pass
            
            results.append(item)
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Site statistics
        cursor.execute("""
            SELECT s.name, s.url, s.last_scraped, s.total_items,
                   COUNT(i.id) as tracked_items,
                   COUNT(CASE WHEN i.first_seen >= datetime('now', '-7 days') THEN 1 END) as new_this_week
            FROM sites s
            LEFT JOIN items i ON s.id = i.site_id AND i.is_active = 1
            GROUP BY s.id, s.name, s.url, s.last_scraped, s.total_items
        """)
        
        sites = []
        for row in cursor.fetchall():
            sites.append({
                'name': row[0],
                'url': row[1],
                'last_scraped': row[2],
                'total_items': row[3],
                'tracked_items': row[4],
                'new_this_week': row[5]
            })
        
        # Recent runs
        cursor.execute("""
            SELECT s.name, r.run_timestamp, r.items_found, r.new_items, r.status
            FROM scraping_runs r
            JOIN sites s ON r.site_id = s.id
            ORDER BY r.run_timestamp DESC
            LIMIT 10
        """)
        
        recent_runs = []
        for row in cursor.fetchall():
            recent_runs.append({
                'site': row[0],
                'timestamp': row[1],
                'items_found': row[2],
                'new_items': row[3],
                'status': row[4]
            })
        
        conn.close()
        
        return {
            'sites': sites,
            'recent_runs': recent_runs
        }