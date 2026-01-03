import pandas as pd
import os
import logging
from typing import List, Optional

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_perspective_data(
    input_path: str, 
    output_path: str, 
    subjects: Optional[List[str]] = None
):
    """
    Transforms a standard Chess.com 'White/Black' CSV into a 'Subject-Perspective' CSV.
    Each game results in 1 or 2 rows depending on whether the player is in the 'subjects' list.
    """
    if not os.path.exists(input_path):
        logging.error(f"Input file not found: {input_path}")
        return False

    logging.info(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # If no subjects provided, use the most frequent players
    if subjects is None:
        all_players = pd.concat([df['white_username'], df['black_username']])
        # Default to top 5 players by game count
        subjects = all_players.value_counts().head(5).index.tolist()
        logging.info(f"No subjects provided. Auto-selected top players: {subjects}")

    perspective_rows = []

    logging.info(f"Generating perspective rows for {len(df)} games...")

    for _, row in df.iterrows():
        # Check if White is a subject
        if row['white_username'] in subjects:
            perspective_rows.append(generate_row(row, 'white'))
        
        # Check if Black is a subject
        if row['black_username'] in subjects:
            perspective_rows.append(generate_row(row, 'black'))

    if not perspective_rows:
        logging.warning("No perspective rows generated. Check if subjects exist in the dataset.")
        return False

    perspective_df = pd.DataFrame(perspective_rows)
    
    # Pre-compute some convenient BI flags
    perspective_df['is_win'] = (perspective_df['result_status'] == 'Win').astype(int)
    perspective_df['is_loss'] = (perspective_df['result_status'] == 'Loss').astype(int)
    perspective_df['is_draw'] = (perspective_df['result_status'] == 'Draw').astype(int)
    
    # Sort by date for BI time series
    perspective_df = perspective_df.sort_values('game_time', ascending=True)

    logging.info(f"Saving perspective data ({len(perspective_df)} rows) to {output_path}...")
    perspective_df.to_csv(output_path, index=False)
    return True

def generate_row(row: pd.Series, perspective: str) -> dict:
    """Creates a single dictionary representing a game from a specific player's view."""
    is_white = perspective == 'white'
    player = row['white_username'] if is_white else row['black_username']
    opponent = row['black_username'] if is_white else row['white_username']
    player_rating = row['white_rating'] if is_white else row['black_rating']
    opponent_rating = row['black_rating'] if is_white else row['white_rating']
    
    # Calculate player-relative results
    winner = str(row['winner'])
    if winner == 'draw':
        result_status = 'Draw'
    elif winner == player:
        result_status = 'Win'
    else:
        result_status = 'Loss'
        
    # Rating Difference (Positive means player is higher rated)
    rating_diff = player_rating - opponent_rating
    
    # Difficulty Buckets
    if rating_diff >= 100: difficulty = 'Much Stronger (+100+)'
    elif rating_diff >= 25: difficulty = 'Stronger (+25 to +99)'
    elif rating_diff > -25: difficulty = 'Similar (±25)'
    elif rating_diff > -100: difficulty = 'Weaker (-25 to -99)'
    else: difficulty = 'Much Weaker (-100+)'

    return {
        'game_date': row['end_date'],
        'game_time': row['end_time'],
        'end_datetime': row['end_datetime'],
        'player_name': player,
        'opponent_name': opponent,
        'player_rating': player_rating,
        'opponent_rating': opponent_rating,
        'rating_diff': rating_diff,
        'difficulty_category': difficulty,
        'result_status': result_status,
        'game_type': row['game_type'],
        'opening_name': row['opening_name'],
        'move_count': row['move_count'],
        'player_color': perspective,
        'game_url': row['url']
    }

if __name__ == "__main__":
    # Define paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT = os.path.join(BASE_DIR, 'data', 'processed', 'processed.csv')
    OUTPUT = os.path.join(BASE_DIR, 'data', 'processed', 'bi_perspective_data.csv')
    
    # Target subjects from the user's known players
    TARGETS = ["MagnusCarlsen", "FabianoCaruana", "hikaru", "GHANDEEVAM2003"]
    
    create_perspective_data(INPUT, OUTPUT, subjects=TARGETS)
