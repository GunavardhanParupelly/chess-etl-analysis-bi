"""
Utility functions for the chess ETL project.
Provides safe file operations, JSON handling, CSV operations, and PGN parsing.
"""

import json
import logging
import os
import pandas as pd
import chess
import chess.pgn
from io import StringIO
from typing import Dict, List, Optional, Any


def setup_logging(log_level: str = 'INFO') -> None:
    """Setup logging configuration for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_json_safely(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Safely load JSON from file with error handling.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error loading {filepath}: {e}")
        return None


def save_json_safely(data: Dict[str, Any], filepath: str) -> bool:
    """
    Safely save data to JSON file with error handling.
    
    Args:
        data: Data to save
        filepath: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving to {filepath}: {e}")
        return False


def save_csv_safely(df: pd.DataFrame, filepath: str) -> bool:
    """
    Safely save DataFrame to CSV with error handling.
    
    Args:
        df: DataFrame to save
        filepath: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Save with proper CSV formatting
        df.to_csv(filepath, index=False, encoding='utf-8', quoting=1, escapechar='\\')
        logging.info(f"Saved {len(df)} records to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Error saving CSV to {filepath}: {e}")
        return False


def parse_pgn_game(pgn_string: str) -> Dict[str, Any]:
    """
    Parse a PGN string and extract game information using python-chess.
    
    Args:
        pgn_string: PGN string of the chess game
        
    Returns:
        Dictionary with parsed game information
    """
    game_info = {
        'move_count': 0,
        'eco_code': None,
        'opening_name': None,
        'result': None
    }
    
    try:
        # Parse PGN
        pgn_io = StringIO(pgn_string)
        game = chess.pgn.read_game(pgn_io)
        
        if game is None:
            return game_info
            
        # Extract basic information
        game_info['eco_code'] = game.headers.get('ECO', None)
        game_info['opening_name'] = game.headers.get('Opening', None)
        game_info['result'] = game.headers.get('Result', None)
        
        # If opening name is missing but ECOUrl is present (common in Chess.com)
        if not game_info['opening_name']:
            eco_url = game.headers.get('ECOUrl', '')
            if eco_url:
                # Extract part after /openings/
                parts = eco_url.split('/openings/')
                if len(parts) > 1:
                    # Clean up: replace hyphens with spaces and capitalize
                    raw_name = parts[1].replace('-', ' ')
                    # Remove trailing numeric stuff if any or just title case it
                    game_info['opening_name'] = raw_name.replace('...', ' ').strip().title()
        
        # Count moves
        board = game.board()
        move_count = 0
        for move in game.mainline_moves():
            board.push(move)
            move_count += 1
        
        game_info['move_count'] = move_count
        
    except Exception as e:
        logging.warning(f"Error parsing PGN: {e}")
    
    return game_info


def ensure_directory_exists(filepath: str) -> None:
    """
    Ensure the directory for a file path exists.
    
    Args:
        filepath: File path to check/create directory for
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_relative_path(base_path: str, target_path: str) -> str:
    """
    Get relative path from base to target, using forward slashes.
    
    Args:
        base_path: Base directory path
        target_path: Target file/directory path
        
    Returns:
        Relative path string
    """
    rel_path = os.path.relpath(target_path, base_path)
    return rel_path.replace(os.sep, '/')


def list_json_files(directory: str) -> List[str]:
    """
    List all JSON files in a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of JSON file paths
    """
    json_files = []
    try:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.lower().endswith('.json'):
                    json_files.append(os.path.join(directory, filename))
    except Exception as e:
        logging.error(f"Error listing JSON files in {directory}: {e}")
    
    return json_files


def validate_chess_data(game_data: Dict[str, Any]) -> bool:
    """
    Validate that game data has required fields.
    
    Args:
        game_data: Game data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['white', 'black', 'end_time', 'pgn']
    
    for field in required_fields:
        if field not in game_data:
            return False
            
    return True