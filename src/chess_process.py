"""
Chess data processing module.
Processes raw JSON game data and creates a clean CSV dataset.
"""

import logging
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils import setup_logging, load_json_safely, save_csv_safely, parse_pgn_game, list_json_files, validate_chess_data


class ChessProcessor:
    """Processes raw chess game data into structured format."""
    
    def __init__(self, raw_data_dir: str = 'data/raw', processed_data_dir: str = 'data/processed'):
        """
        Initialize the chess processor.
        
        Args:
            raw_data_dir: Directory containing raw JSON files
            processed_data_dir: Directory for processed output
        """
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        
    def extract_game_data(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant fields from a single game record.
        
        Args:
            game: Raw game data from Chess.com API
            
        Returns:
            Dictionary with extracted fields or None if invalid
        """
        try:
            # Validate required fields
            if not validate_chess_data(game):
                return None
            
            # Extract basic game information
            extracted = {
                'white_username': game['white'].get('username', ''),
                'black_username': game['black'].get('username', ''),
                'white_rating': game['white'].get('rating', 0),
                'black_rating': game['black'].get('rating', 0),
                'result': game.get('result', ''),
                'end_time': game.get('end_time', 0),
                'time_control': game.get('time_control', ''),
                'url': game.get('url', ''),
                'pgn': game.get('pgn', '')
            }
            
            # Convert end_time to readable format and extract date parts
            if extracted['end_time']:
                try:
                    dt = datetime.fromtimestamp(extracted['end_time'])
                    extracted['end_date'] = dt.strftime('%Y-%m-%d')
                    extracted['end_datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    extracted['year'] = dt.year
                    extracted['month'] = dt.strftime('%Y-%m')
                except:
                    extracted['end_date'] = ''
                    extracted['end_datetime'] = ''
                    extracted['year'] = 0
                    extracted['month'] = ''
            else:
                extracted['end_date'] = ''
                extracted['end_datetime'] = ''
                extracted['year'] = 0
                extracted['month'] = ''

            # Calculate rating difference
            extracted['rating_diff'] = extracted['white_rating'] - extracted['black_rating']
            
            # Determine Game Type from time_control
            time_control = extracted['time_control']
            try:
                # Handle standard formats like "600" or "600+0"
                base_time = int(time_control.split('+')[0])
                if base_time <= 180:
                    extracted['game_type'] = 'bullet'
                elif base_time <= 600:
                    extracted['game_type'] = 'blitz'
                else:
                    extracted['game_type'] = 'rapid'
            except:
                # Handle daily (e.g., "1/86400") or others
                if '/' in str(time_control):
                    extracted['game_type'] = 'daily'
                else:
                    extracted['game_type'] = 'unknown'
            
            # Parse PGN for additional information
            if extracted['pgn']:
                pgn_info = parse_pgn_game(extracted['pgn'])
                extracted.update({
                    'move_count': pgn_info['move_count'],
                    'eco_code': pgn_info['eco_code'],
                    'opening_name': pgn_info['opening_name'],
                    'pgn_result': pgn_info['result']
                })
            else:
                extracted.update({
                    'move_count': 0,
                    'eco_code': None,
                    'opening_name': None,
                    'pgn_result': None
                })
            
            # Clean up result format and determine winner and result
            white_result = str(game.get('white', {}).get('result', '')).lower()
            black_result = str(game.get('black', {}).get('result', '')).lower()
            
            # Determine winner and formal result (1-0, 0-1, 1/2-1/2)
            if white_result == 'win':
                extracted['winner'] = extracted['white_username']
                extracted['result'] = '1-0'
                extracted['result_category'] = black_result # E.g., checkmated
            elif black_result == 'win':
                extracted['winner'] = extracted['black_username']
                extracted['result'] = '0-1'
                extracted['result_category'] = white_result
            elif any(r in ['agreed', 'repetition', 'stalemate', 'insufficient', '50move', 'timevsinsufficient'] for r in [white_result, black_result]):
                extracted['winner'] = 'draw'
                extracted['result'] = '1/2-1/2'
                extracted['result_category'] = white_result
            else:
                # Fallback to PGN result if available, otherwise draw
                extracted['result'] = extracted.get('pgn_result', '1/2-1/2')
                extracted['winner'] = 'draw' if '1/2-1/2' in extracted['result'] else ''
                extracted['result_category'] = f"{white_result}/{black_result}"
            
            # Add simple dashboard boolean flags
            extracted['white_win'] = (extracted['winner'] == extracted['white_username'])
            extracted['black_win'] = (extracted['winner'] == extracted['black_username'])
            extracted['is_draw'] = (extracted['winner'] == 'draw')
            
            return extracted
            
        except Exception as e:
            logging.warning(f"Error extracting game data: {e}")
            return None
    
    def process_json_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Process a single JSON file containing chess games.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            List of extracted game records
        """
        data = load_json_safely(filepath)
        if not data:
            return []
        
        games = data.get('games', [])
        processed_games = []
        
        for game in games:
            extracted = self.extract_game_data(game)
            if extracted:
                processed_games.append(extracted)
        
        logging.info(f"Processed {len(processed_games)} games from {os.path.basename(filepath)}")
        return processed_games
    
    def process_all_files(self) -> pd.DataFrame:
        """
        Process all JSON files in the raw data directory.
        
        Returns:
            DataFrame with all processed game data
        """
        all_games = []
        json_files = list_json_files(self.raw_data_dir)
        
        if not json_files:
            logging.warning(f"No JSON files found in {self.raw_data_dir}")
            return pd.DataFrame()
        
        logging.info(f"Processing {len(json_files)} JSON files...")
        
        for filepath in json_files:
            games = self.process_json_file(filepath)
            all_games.extend(games)
        
        if not all_games:
            logging.warning("No games extracted from any files")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(all_games)
        
        # Remove duplicates based on game URL (unique identifier)
        initial_count = len(df)
        df = df.drop_duplicates(subset=['url'], keep='first')
        final_count = len(df)
        
        if initial_count > final_count:
            logging.info(f"Removed {initial_count - final_count} duplicate games")
        
        # Sort by end_time
        df = df.sort_values('end_time', ascending=True)
        
        logging.info(f"Successfully processed {final_count} unique games")
        return df
    
    def create_processed_dataset(self, output_filename: str = 'processed.csv') -> bool:
        """
        Create the final processed CSV dataset.
        
        Args:
            output_filename: Name of output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Process all raw data files
            df = self.process_all_files()
            
            if df.empty:
                logging.error("No data to save - DataFrame is empty")
                return False
            
            # Define column order for better readability
            column_order = [
                'end_date', 'white_username', 'black_username',
                'white_rating', 'black_rating', 'result', 'winner', 'result_category',
                'game_type', 'opening_name', 'eco_code', 'move_count',
                'white_win', 'black_win', 'is_draw', 'rating_diff',
                'year', 'month', 'time_control',
                'end_datetime', 'end_time', 'url'
            ]
            
            # Reorder columns if they exist and exclude problematic columns
            existing_columns = [col for col in column_order if col in df.columns]
            other_columns = [col for col in df.columns if col not in column_order and col != 'pgn']
            final_columns = existing_columns + other_columns
            
            # Drop PGN column to avoid CSV formatting issues
            if 'pgn' in df.columns:
                df = df.drop('pgn', axis=1)
                logging.info("Excluded PGN column from CSV for cleaner formatting")
            
            df = df[final_columns]
            
            # Save to CSV
            output_path = os.path.join(self.processed_data_dir, output_filename)
            success = save_csv_safely(df, output_path)
            
            if success:
                logging.info(f"Dataset saved successfully to {output_path}")
                logging.info(f"Dataset shape: {df.shape}")
                logging.info(f"Date range: {df['end_date'].min()} to {df['end_date'].max()}")
                
                # Print some basic stats
                logging.info("\nDataset Summary:")
                logging.info(f"Total games: {len(df)}")
                logging.info(f"Unique players: {len(set(df['white_username'].tolist() + df['black_username'].tolist()))}")
                logging.info(f"Date range: {df['end_date'].min()} to {df['end_date'].max()}")
                
                if 'time_control' in df.columns:
                    logging.info(f"Time controls: {df['time_control'].value_counts().head().to_dict()}")
            
            return success
            
        except Exception as e:
            logging.error(f"Error creating processed dataset: {e}")
            return False


def main():
    """Main function to handle command line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process raw chess game data into CSV')
    parser.add_argument('--raw-dir', default='data/raw', help='Directory containing raw JSON files')
    parser.add_argument('--processed-dir', default='data/processed', help='Directory for processed output')
    parser.add_argument('--output', default='processed.csv', help='Output CSV filename')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create processor and process data
    processor = ChessProcessor(args.raw_dir, args.processed_dir)
    
    logging.info("Starting chess data processing...")
    success = processor.create_processed_dataset(args.output)
    
    if success:
        logging.info("Data processing completed successfully!")
    else:
        logging.error("Data processing failed!")
        exit(1)


if __name__ == "__main__":
    main()