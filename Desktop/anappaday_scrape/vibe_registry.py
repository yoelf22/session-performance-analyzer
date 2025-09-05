#!/usr/bin/env python3
"""
Vibe Registry – local app discovery scraper

This script implements a small command‑line application that helps you discover
apps built on various no‑code/AI platforms.  It was designed to run on a
developer's machine on demand rather than as a long‑running service.  The
program uses Playwright to render pages (so it can handle single page
applications and infinite scrolls) and stores results in a local SQLite
database.  After each run the tool exports a CSV containing only the newly
discovered apps.

The core rules implemented by this scraper come from the "no inference"
requirement: every field persisted must originate from an explicit element on
the page being scraped (or a single, directly linked detail page).  Nothing is
derived from filenames, slugs or heuristics, and there is no fuzzy matching.

Supported platforms:
    - Base44: implemented against https://catalog.base44.com/apps.  It
      iterates over paginated listing pages and follows each entry to a detail
      page to extract metadata via og: tags and canonical links.
    - Bolt, Replit, Lovable, Embeddable: placeholder implementations are
      provided for future expansion.  You can add additional scrapers by
      following the pattern used for Base44.

Usage (once you've installed dependencies):

    # install dependencies and browser
    pip install -r requirements.txt
    playwright install

    # initialise the database (only needed once)
    python vibe_registry.py init-db

    # run a discovery session (interactive prompts guide you through it)
    python vibe_registry.py ingest

    # run with verbose output
    python vibe_registry.py ingest --verbose

    # export the latest run's new records
    python vibe_registry.py export

The script stores its SQLite database under the current working directory in
`data/vibe_registry.db`.  Screenshots captured during scraping live in
`cache/screenshots/` and are never used to backfill publisher‑provided
graphics.
"""

import argparse
import contextlib
import datetime as _dt
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Tuple

# External dependencies.  These imports will fail unless the user installs
# playwright and BeautifulSoup.  They're intentionally localised here so
# that unit tests or dry runs of other commands don't immediately require
# network‑heavy components.  If you only run `init-db` or `export` you
# won't need these libraries.
try:
    from bs4 import BeautifulSoup  # type: ignore
    from playwright.sync_api import Playwright, sync_playwright
except ImportError:
    BeautifulSoup = None  # type: ignore
    sync_playwright = None  # type: ignore


# -----------------------------------------------------------------------------
# Database helper
#

class VibeRegistryDB:
    """Wrapper around SQLite to store apps and runs with provenance."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Establish connection on demand; row_factory returns dict‑like objects
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they do not already exist."""
        cur = self.conn.cursor()
        # Table to hold discovered apps
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                app_name TEXT,
                app_url TEXT NOT NULL,
                download_url TEXT,
                logo_url_original TEXT,
                graphic_url_original TEXT,
                source_url TEXT NOT NULL,
                discovery_method TEXT NOT NULL,
                provenance TEXT NOT NULL,
                screenshot_captured_by_us INTEGER DEFAULT 0,
                screenshot_url_cached TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                ingestion_run_id INTEGER,
                UNIQUE(platform, app_url)
            )
            """
        )
        # Table to log each run
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT,
                new_count INTEGER DEFAULT 0,
                updated_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                log_excerpt TEXT
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Run bookkeeping

    def start_run(self) -> int:
        """Insert a new run record and return its ID."""
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO runs (started_at) VALUES (?)",
            (now,),
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_run(
        self,
        run_id: int,
        status: str,
        new_count: int,
        updated_count: int,
        error_count: int,
        log_excerpt: str,
    ) -> None:
        """Mark a run as finished with summary statistics."""
        finished_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE runs
            SET finished_at=?, status=?, new_count=?, updated_count=?, error_count=?, log_excerpt=?
            WHERE id=?
            """,
            (finished_at, status, new_count, updated_count, error_count, log_excerpt, run_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # App upsert

    def upsert_app(
        self,
        run_id: int,
        platform: str,
        app_name: Optional[str],
        app_url: str,
        download_url: Optional[str],
        logo_url_original: Optional[str],
        graphic_url_original: Optional[str],
        source_url: str,
        discovery_method: str,
        provenance: Dict[str, str],
        screenshot_captured_by_us: bool,
        screenshot_url_cached: Optional[str],
    ) -> Tuple[bool, int]:
        """Insert or update an app record.

        Returns a tuple (is_new, rowid).
        """
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        provenance_json = json.dumps(provenance, ensure_ascii=False)
        cur = self.conn.cursor()
        # Try to insert; if conflict on (platform, app_url) then update
        try:
            cur.execute(
                """
                INSERT INTO apps (
                    platform, app_name, app_url, download_url,
                    logo_url_original, graphic_url_original,
                    source_url, discovery_method, provenance,
                    screenshot_captured_by_us, screenshot_url_cached,
                    first_seen, last_seen, ingestion_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    platform,
                    app_name,
                    app_url,
                    download_url,
                    logo_url_original,
                    graphic_url_original,
                    source_url,
                    discovery_method,
                    provenance_json,
                    int(screenshot_captured_by_us),
                    screenshot_url_cached,
                    now,
                    now,
                    run_id,
                ),
            )
            self.conn.commit()
            return True, cur.lastrowid
        except sqlite3.IntegrityError:
            # Conflict: update existing record
            cur.execute(
                """
                UPDATE apps
                SET app_name=COALESCE(?, app_name),
                    download_url=COALESCE(?, download_url),
                    logo_url_original=COALESCE(?, logo_url_original),
                    graphic_url_original=COALESCE(?, graphic_url_original),
                    source_url=?,
                    discovery_method=?,
                    provenance=?,
                    screenshot_captured_by_us=CASE WHEN ? THEN 1 ELSE screenshot_captured_by_us END,
                    screenshot_url_cached=COALESCE(?, screenshot_url_cached),
                    last_seen=?,
                    ingestion_run_id=?
                WHERE platform=? AND app_url=?
                """,
                (
                    app_name,
                    download_url,
                    logo_url_original,
                    graphic_url_original,
                    source_url,
                    discovery_method,
                    provenance_json,
                    int(screenshot_captured_by_us),
                    screenshot_url_cached,
                    now,
                    run_id,
                    platform,
                    app_url,
                ),
            )
            self.conn.commit()
            # Return False because it's an update
            cur.execute(
                "SELECT id FROM apps WHERE platform=? AND app_url=?",
                (platform, app_url),
            )
            rowid = cur.fetchone()[0]
            return False, rowid

    # ------------------------------------------------------------------
    # Export utilities

    def export_new_rows_csv(self, run_id: int, export_path: Path) -> int:
        """Export only apps whose first_seen corresponds to the given run.

        Returns the number of exported rows.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT * FROM apps WHERE ingestion_run_id = ? AND first_seen = last_seen
            """,
            (run_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return 0
        # Ensure directory exists
        export_path.parent.mkdir(parents=True, exist_ok=True)
        # Write CSV manually to avoid requiring pandas
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            # header
            headers = rows[0].keys()
            f.write(','.join(headers) + '\n')
            for row in rows:
                # Escape commas and quotes appropriately
                values = []
                for col in headers:
                    val = row[col]
                    if val is None:
                        values.append('')
                    else:
                        sval = str(val)
                        # Surround with quotes if contains comma or quote
                        if ',' in sval or '"' in sval or '\n' in sval:
                            sval = '"' + sval.replace('"', '""') + '"'
                        values.append(sval)
                f.write(','.join(values) + '\n')
        return len(rows)


# -----------------------------------------------------------------------------
# Scrapers
#

class Scraper:
    """Scrapes specific platforms.  Each method returns counts of new/updated/error."""

    def __init__(self, db: VibeRegistryDB, run_id: int, capture_screenshots: bool, verbose: bool = False) -> None:
        self.db = db
        self.run_id = run_id
        self.capture_screenshots = capture_screenshots
        self.verbose = verbose
        # Directory for screenshots
        self.screenshot_dir = Path('cache/screenshots')
        if self.capture_screenshots:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[VERBOSE] {message}")

    # -------------------------- Base44 -----------------------------------
    def scrape_base44(self, max_items: Optional[int] = None) -> Tuple[int, int, int]:
        """Scrape apps from Base44's showcase.

        This implementation paginates through catalog.base44.com/apps and follows
        each app link to a detail page.  It extracts name, canonical app URL and
        og:image for graphic.  It does not infer values beyond trimming
        whitespace.

        Parameters
        ----------
        max_items: Optional[int]
            Maximum number of items to process across all pages.  None means no
            cap.

        Returns
        -------
        new_count, updated_count, error_count: Tuple[int, int, int]
        """
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright is required for scraping.  Please install it with 'pip install playwright' and run 'playwright install'."
            )
        
        self._log("Starting Base44 scraper")
        new_count = 0
        updated_count = 0
        error_count = 0
        processed = 0
        
        try:
            with sync_playwright() as p:
                self._log("Launching browser")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page_num = 1
                
                while True:
                    list_url = f'https://catalog.base44.com/apps?page={page_num}'
                    self._log(f"Navigating to page {page_num}: {list_url}")
                    page.goto(list_url)
                    
                    # Wait for page load; if it fails, break
                    try:
                        self._log("Waiting for app links to load...")
                        page.wait_for_selector('a[href^="/apps/"]', timeout=10000)
                        self._log("App links found!")
                    except Exception as e:
                        self._log(f"No app links found on page {page_num}: {e}")
                        break
                    
                    # Collect app detail links; ensure uniqueness
                    self._log("Collecting app detail links...")
                    links = page.eval_on_selector_all(
                        'a[href^="/apps/"]', 'els => els.map(el => el.href)'
                    )
                    self._log(f"Found {len(links)} raw links")
                    
                    # Remove duplicates and extraneous nav links
                    unique_links = []
                    seen = set()
                    for link in links:
                        if '/apps/' not in link:
                            continue
                        if link in seen:
                            continue
                        # Exclude sign up links or login
                        if 'signup' in link or 'login' in link:
                            continue
                        seen.add(link)
                        unique_links.append(link)
                    
                    self._log(f"Filtered to {len(unique_links)} unique app links")
                    
                    if not unique_links:
                        self._log("No valid app links found, stopping pagination")
                        break
                    
                    for i, detail_url in enumerate(unique_links):
                        if max_items is not None and processed >= max_items:
                            self._log(f"Reached max_items limit ({max_items}), stopping")
                            break
                        
                        processed += 1
                        self._log(f"Processing app {i+1}/{len(unique_links)} (total: {processed}): {detail_url}")
                        
                        try:
                            # Use a separate page for each detail to isolate state
                            detail_page = context.new_page()
                            self._log(f"  Loading detail page...")
                            detail_page.goto(detail_url)
                            
                            # Wait for meta tags to load; if not found, skip
                            try:
                                detail_page.wait_for_selector('head meta[property="og:title"]', timeout=10000)
                                self._log(f"  Meta tags loaded successfully")
                            except Exception as e:
                                self._log(f"  ERROR: Meta tags not found: {e}")
                                error_count += 1
                                detail_page.close()
                                continue
                            
                            content = detail_page.content()
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Extract fields explicitly
                            app_name = None
                            app_url = None
                            graphic_url_original = None
                            logo_url_original = None
                            download_url = None
                            # provenance dict; keys correspond to db fields
                            provenance: Dict[str, str] = {}
                            
                            # Name: prefer og:title
                            meta_title = soup.find('meta', property='og:title')
                            if meta_title and meta_title.get('content'):
                                app_name = meta_title['content'].strip()
                                provenance['app_name'] = "meta[property='og:title']"
                                self._log(f"  Found app name: {app_name}")
                            else:
                                self._log(f"  No app name found")
                            
                            # Canonical link for app_url
                            link_canonical = soup.find('link', rel='canonical')
                            if link_canonical and link_canonical.get('href'):
                                app_url = link_canonical['href'].strip()
                                provenance['app_url'] = "link[rel='canonical']"
                                self._log(f"  Found canonical URL: {app_url}")
                            else:
                                self._log(f"  No canonical URL found")
                            
                            # Download link: we look for anchor starting with 'Try '
                            try_link = soup.find('a', string=lambda x: x and x.lower().startswith('try '))
                            if try_link and try_link.get('href'):
                                download_url_candidate = try_link['href'].strip()
                                # Accept only if absolute URL
                                if download_url_candidate.startswith('http'):
                                    download_url = download_url_candidate
                                    provenance['download_url'] = "a[text^='Try ']"
                                    self._log(f"  Found download URL: {download_url}")
                                else:
                                    self._log(f"  Found relative download URL (ignored): {download_url_candidate}")
                            else:
                                self._log(f"  No download URL found")
                            
                            # Graphic: og:image
                            meta_image = soup.find('meta', property='og:image')
                            if meta_image and meta_image.get('content'):
                                graphic_url_original = meta_image['content'].strip()
                                provenance['graphic_url_original'] = "meta[property='og:image']"
                                self._log(f"  Found graphic URL: {graphic_url_original}")
                            else:
                                self._log(f"  No graphic URL found")
                            
                            # Logo: look for apple-touch-icon or shortcut icon that isn't default
                            link_logo = soup.find('link', rel=lambda x: x and 'apple-touch-icon' in x)
                            if link_logo and link_logo.get('href'):
                                logo_candidate = link_logo['href'].strip()
                                if logo_candidate.startswith('http'):
                                    logo_url_original = logo_candidate
                                    provenance['logo_url_original'] = "link[rel*='apple-touch-icon']"
                                    self._log(f"  Found logo URL: {logo_url_original}")
                                else:
                                    self._log(f"  Found relative logo URL (ignored): {logo_candidate}")
                            else:
                                self._log(f"  No logo URL found")
                            
                            # If we didn't get a canonical app_url but have a download_url, fall back
                            if not app_url and download_url:
                                app_url = download_url
                                provenance['app_url'] = provenance.get('download_url', 'download_url')
                                self._log(f"  Using download URL as app URL: {app_url}")
                            
                            # Only proceed if we have a platform and app_url
                            if not app_url:
                                self._log(f"  ERROR: No app URL found, skipping")
                                error_count += 1
                                detail_page.close()
                                continue
                            
                            # Screenshot capturing: only if requested and missing graphic
                            screenshot_captured = False
                            screenshot_cached_path = None
                            if self.capture_screenshots and not graphic_url_original:
                                self._log(f"  Capturing screenshot (no graphic found)...")
                                # Use Playwright's screenshot to capture visible page
                                # Save as PNG under cache/screenshots with timestamp and slug
                                slug = os.path.basename(detail_url.rstrip('/'))
                                filename = f"{slug}_{int(_dt.datetime.now().timestamp())}.png"
                                screenshot_path = self.screenshot_dir / filename
                                try:
                                    detail_page.screenshot(path=str(screenshot_path), full_page=True)
                                    screenshot_captured = True
                                    screenshot_cached_path = str(screenshot_path)
                                    self._log(f"  Screenshot saved: {screenshot_path}")
                                except Exception as e:
                                    # If screenshot fails we ignore and don't set
                                    screenshot_captured = False
                                    screenshot_cached_path = None
                                    self._log(f"  Screenshot failed: {e}")
                            
                            # Insert or update in DB
                            self._log(f"  Saving to database...")
                            is_new, _ = self.db.upsert_app(
                                run_id=self.run_id,
                                platform='Base44',
                                app_name=app_name,
                                app_url=app_url,
                                download_url=download_url,
                                logo_url_original=logo_url_original,
                                graphic_url_original=graphic_url_original,
                                source_url=detail_url,
                                discovery_method='showcase',
                                provenance=provenance,
                                screenshot_captured_by_us=screenshot_captured,
                                screenshot_url_cached=screenshot_cached_path,
                            )
                            if is_new:
                                new_count += 1
                                self._log(f"  ✓ NEW app saved")
                            else:
                                updated_count += 1
                                self._log(f"  ✓ Updated existing app")
                            detail_page.close()
                        except Exception as e:
                            self._log(f"  ERROR processing {detail_url}: {e}")
                            error_count += 1
                            # Ensure page closed on error
                            with contextlib.suppress(Exception):
                                detail_page.close()
                    
                    # Stop if reached max_items
                    if max_items is not None and processed >= max_items:
                        break
                    
                    # Determine if there is a "Next" button; if not, break
                    # Using Playwright to evaluate existence
                    has_next = False
                    try:
                        # Some Next buttons have rel="next", some have text 'Next'
                        next_selector = page.query_selector("a[rel='next']")
                        if next_selector:
                            has_next = True
                            self._log(f"Found 'Next' button (rel='next')")
                        else:
                            next_selector = page.query_selector("a:has-text('Next')")
                            if next_selector:
                                has_next = True
                                self._log(f"Found 'Next' button (text='Next')")
                    except Exception as e:
                        self._log(f"Error checking for Next button: {e}")
                        pass
                    
                    if not has_next:
                        self._log(f"No 'Next' button found, pagination complete")
                        break
                    
                    page_num += 1
                    
                self._log("Closing browser")
                browser.close()
                
        except Exception as e:
            self._log(f"FATAL ERROR in Base44 scraper: {e}")
            error_count += 1
        
        self._log(f"Base44 scraping complete: {new_count} new, {updated_count} updated, {error_count} errors")
        return new_count, updated_count, error_count

    # Placeholder scrapers for other platforms.  These methods simply log that
    # scraping is not yet implemented and return zero counts.
    def scrape_bolt(self, max_items: Optional[int] = None) -> Tuple[int, int, int]:
        print("[Bolt] Scraper not yet implemented.  Please extend this method.")
        return 0, 0, 0

    def scrape_replit(self, max_items: Optional[int] = None) -> Tuple[int, int, int]:
        print("[Replit] Scraper not yet implemented.  Please extend this method.")
        return 0, 0, 0

    def scrape_lovable(self, max_items: Optional[int] = None) -> Tuple[int, int, int]:
        print("[Lovable] Scraper not yet implemented.  Please extend this method.")
        return 0, 0, 0

    def scrape_embeddable(self, max_items: Optional[int] = None) -> Tuple[int, int, int]:
        print("[Embeddable] Scraper not yet implemented.  Please extend this method.")
        return 0, 0, 0


# -----------------------------------------------------------------------------
# CLI
#

def prompt_platforms() -> List[str]:
    """Interactively ask the user to select platforms."""
    platforms = ['Base44', 'Bolt', 'Replit', 'Lovable', 'Embeddable']
    print("Select platforms to scrape (comma separated numbers):")
    for i, p in enumerate(platforms, start=1):
        print(f"  {i}) {p}")
    print("  0) cancel")
    choices = input("Your choice: ").strip()
    if not choices:
        return []
    selected = []
    for part in choices.split(','):
        part = part.strip()
        if part == '0':
            return []
        try:
            idx = int(part)
            if 1 <= idx <= len(platforms):
                selected.append(platforms[idx - 1])
        except ValueError:
            continue
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Vibe registry CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)
    # init-db
    subparsers.add_parser('init-db', help='Initialise the local SQLite database')
    # ingest
    ingest_parser = subparsers.add_parser('ingest', help='Run a discovery session')
    ingest_parser.add_argument('--platforms', nargs='*', help='Platforms to scrape')
    ingest_parser.add_argument('--capture-screenshots', action='store_true', help='Capture screenshots when no graphic is present')
    ingest_parser.add_argument('--max-items', type=int, help='Maximum items per platform')
    ingest_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    # export
    export_parser = subparsers.add_parser('export', help='Export new rows from the latest run')
    export_parser.add_argument('--output', type=str, default=None, help='Path to CSV file')

    args = parser.parse_args()
    db_path = Path('data/vibe_registry.db')
    db = VibeRegistryDB(db_path)

    if args.command == 'init-db':
        print(f"Database initialised at {db_path.resolve()}")
        return

    if args.command == 'ingest':
        # Determine platforms
        if args.platforms:
            platforms = [p.capitalize() for p in args.platforms]
        else:
            platforms = prompt_platforms()
        if not platforms:
            print("No platforms selected.  Exiting.")
            return
        run_id = db.start_run()
        total_new = 0
        total_updated = 0
        total_errors = 0
        logs: List[str] = []
        scraper = Scraper(db, run_id, capture_screenshots=args.capture_screenshots, verbose=args.verbose)
        for platform in platforms:
            print(f"Scraping {platform}…")
            if platform == 'Base44':
                new_count, updated_count, error_count = scraper.scrape_base44(max_items=args.max_items)
            elif platform == 'Bolt':
                new_count, updated_count, error_count = scraper.scrape_bolt(max_items=args.max_items)
            elif platform == 'Replit':
                new_count, updated_count, error_count = scraper.scrape_replit(max_items=args.max_items)
            elif platform == 'Lovable':
                new_count, updated_count, error_count = scraper.scrape_lovable(max_items=args.max_items)
            elif platform == 'Embeddable':
                new_count, updated_count, error_count = scraper.scrape_embeddable(max_items=args.max_items)
            else:
                print(f"Unknown platform: {platform}")
                continue
            logs.append(f"{platform}: {new_count} new, {updated_count} updated, {error_count} errors")
            total_new += new_count
            total_updated += updated_count
            total_errors += error_count
        # Create log excerpt
        log_excerpt = '\n'.join(logs)[:1000]  # limit to 1000 chars
        status = 'partial' if total_errors > 0 else 'success'
        db.finish_run(run_id, status, total_new, total_updated, total_errors, log_excerpt)
        print(f"Run {run_id} finished.  New: {total_new}, Updated: {total_updated}, Errors: {total_errors}.")
        # Export new rows for this run automatically
        export_file = Path('exports') / f'run_{run_id}_{_dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        exported = db.export_new_rows_csv(run_id, export_file)
        print(f"Exported {exported} new rows to {export_file}")
        return

    if args.command == 'export':
        # Determine the latest finished run
        cur = db.conn.cursor()
        cur.execute("SELECT id, finished_at FROM runs WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("No completed runs to export.")
            return
        run_id = row['id']
        # Determine output path
        if args.output:
            out_path = Path(args.output)
        else:
            out_path = Path('exports') / f'run_{run_id}_{_dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        exported = db.export_new_rows_csv(run_id, out_path)
        print(f"Exported {exported} new rows from run {run_id} to {out_path}")
        return


if __name__ == '__main__':
    main()
