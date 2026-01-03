import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PLAYERS = [
    "MagnusCarlsen",
    "FabianoCaruana",
    "hikaru",
    "GukeshDommaraju",
    "rpragchess",
    "GHANDEEVAM2003"
]

START_YEAR = 2020
END_YEAR = 2025

def fetch_player(username):
    logging.info(f"--- Fetching data for {username} ---")
    cmd = [
        "python", "src/chess_fetch.py",
        "--user", username,
        "--start-year", str(START_YEAR),
        "--end-year", str(END_YEAR)
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fetch data for {username}: {e}")

def main():
    logging.info(f"Starting fresh ETL for players: {', '.join(PLAYERS)}")
    logging.info(f"Range: {START_YEAR}-{END_YEAR}")
    
    for player in PLAYERS:
        fetch_player(player)

if __name__ == "__main__":
    main()
