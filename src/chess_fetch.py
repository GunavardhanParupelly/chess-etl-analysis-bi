"""
Chess.com data fetcher module.
Downloads chess game data from Chess.com public API for a given user.
"""

import argparse
import logging
import os
import requests
import time
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse

from utils import setup_logging, save_json_safely


class ChessFetcher:
    """Fetches chess game data from Chess.com API."""
    
    def __init__(self, base_data_dir: str = 'data/raw'):
        """
        Initialize the chess fetcher.
        
        Args:
            base_data_dir: Base directory for storing raw data
        """
        self.base_data_dir = base_data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess ETL Project (Educational Purpose)'
        })
        
    def get_user_archives(self, username: str) -> List[str]:
        """
        Get list of monthly archive URLs for a user.
        
        Args:
            username: Chess.com username
            
        Returns:
            List of archive URLs
        """
        url = f"https://api.chess.com/pub/player/{username}/games/archives"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            archives = data.get('archives', [])
            
            logging.info(f"Found {len(archives)} monthly archives for user {username}")
            return archives
            
        except requests.RequestException as e:
            logging.error(f"Error fetching archives for {username}: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return []
    
    def extract_date_from_url(self, archive_url: str) -> tuple:
        """
        Extract year and month from archive URL.
        
        Args:
            archive_url: Archive URL like https://api.chess.com/pub/player/username/games/2024/01
            
        Returns:
            Tuple of (year, month) as strings
        """
        try:
            # Parse URL to get the path
            path = urlparse(archive_url).path
            # Split path and get last two components (year, month)
            parts = path.strip('/').split('/')
            if len(parts) >= 2:
                year = parts[-2]
                month = parts[-1]
                return year, month
        except Exception as e:
            logging.warning(f"Could not extract date from URL {archive_url}: {e}")
        
        # Fallback: use current date
        now = datetime.now()
        return str(now.year), f"{now.month:02d}"
    
    def get_archive_filename(self, username: str, archive_url: str) -> str:
        """
        Generate filename for archive data.
        
        Args:
            username: Chess.com username
            archive_url: Archive URL
            
        Returns:
            Filename like username_YYYY_MM.json
        """
        year, month = self.extract_date_from_url(archive_url)
        return f"{username}_{year}_{month}.json"
    
    def download_archive(self, username: str, archive_url: str) -> bool:
        """
        Download games from a monthly archive.
        
        Args:
            username: Chess.com username
            archive_url: Archive URL to download
            
        Returns:
            True if successful, False otherwise
        """
        filename = self.get_archive_filename(username, archive_url)
        filepath = os.path.join(self.base_data_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            logging.info(f"Archive already exists, skipping: {filename}")
            return True
        
        try:
            logging.info(f"Downloading archive: {archive_url}")
            
            response = self.session.get(archive_url)
            response.raise_for_status()
            
            data = response.json()
            games = data.get('games', [])
            
            # Save to file
            if save_json_safely(data, filepath):
                logging.info(f"Saved {len(games)} games to {filename}")
                return True
            else:
                return False
                
        except requests.RequestException as e:
            logging.error(f"Error downloading archive {archive_url}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error downloading {archive_url}: {e}")
            return False
    
    def fetch_user_games(self, username: str, start_year: int = None, end_year: int = None, delay: float = 1.0) -> Dict[str, int]:
        """
        Fetch all available games for a user within an optional year range.
        
        Args:
            username: Chess.com username
            start_year: Only fetch archives from this year onwards
            end_year: Only fetch archives up to this year
            delay: Delay between API calls in seconds
            
        Returns:
            Dictionary with download statistics
        """
        stats = {
            'archives_found': 0,
            'archives_downloaded': 0,
            'archives_skipped': 0,
            'total_games': 0
        }
        
        # Get archive URLs
        archives = self.get_user_archives(username)
        
        # Filter archives by year if specified
        filtered_archives = []
        for arch in archives:
            year_str, _ = self.extract_date_from_url(arch)
            year = int(year_str)
            
            if start_year and year < start_year:
                continue
            if end_year and year > end_year:
                continue
            filtered_archives.append(arch)
            
        stats['archives_found'] = len(filtered_archives)
        
        if not filtered_archives:
            logging.warning(f"No archives found for user {username} in the specified range")
            return stats
        
        # Download each archive
        for i, archive_url in enumerate(filtered_archives):
            success = self.download_archive(username, archive_url)
            
            if success:
                stats['archives_downloaded'] += 1
            else:
                stats['archives_skipped'] += 1
            
            # Rate limiting - wait between requests
            if i < len(filtered_archives) - 1:  # Don't wait after last request
                time.sleep(delay)
        
        # Count total games downloaded
        try:
            for filename in os.listdir(self.base_data_dir):
                if filename.startswith(f"{username}_") and filename.endswith('.json'):
                    # Check if filename year is in range
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        file_year = int(parts[1])
                        if start_year and file_year < start_year:
                            continue
                        if end_year and file_year > end_year:
                            continue
                            
                    filepath = os.path.join(self.base_data_dir, filename)
                    with open(filepath, 'r') as f:
                        import json
                        data = json.load(f)
                        stats['total_games'] += len(data.get('games', []))
        except Exception as e:
            logging.warning(f"Error counting total games: {e}")
        
        return stats


def main():
    """Main function to handle command line execution."""
    parser = argparse.ArgumentParser(description='Fetch chess games from Chess.com API')
    parser.add_argument('--user', required=True, help='Chess.com username')
    parser.add_argument('--data-dir', default='data/raw', help='Directory to save raw data')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls (seconds)')
    parser.add_argument('--start-year', type=int, help='Start year for data collection')
    parser.add_argument('--end-year', type=int, help='End year for data collection')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create fetcher and download games
    fetcher = ChessFetcher(args.data_dir)
    
    logging.info(f"Starting download for user: {args.user}")
    if args.start_year or args.end_year:
        logging.info(f"Year range: {args.start_year or 'Start'} to {args.end_year or 'End'}")
        
    stats = fetcher.fetch_user_games(args.user, args.start_year, args.end_year, args.delay)
    
    # Print summary
    logging.info("Download completed!")
    logging.info(f"Archives found: {stats['archives_found']}")
    logging.info(f"Archives downloaded: {stats['archives_downloaded']}")
    logging.info(f"Archives skipped: {stats['archives_skipped']}")
    logging.info(f"Total games: {stats['total_games']}")


if __name__ == "__main__":
    main()