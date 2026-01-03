# Chess ETL Project

A comprehensive chess data pipeline that fetches player games from Chess.com API, processes the raw data, and generates insightful analysis with visualizations.

## 📋 Project Overview

This project provides a complete ETL (Extract, Transform, Load) system to prepare chess game data for external BI tools (e.g., PowerBI, Tableau). It consists of two main components:

1. **Data Fetcher** - Downloads chess games from Chess.com public API
2. **Data Processor** - Cleans and transforms raw JSON data into structured, BI-ready CSV format

## 📁 Project Structure

> **Note**: Raw data (`data/raw/`) and virtual environments are excluded from the repository. They will be created locally when you run the setup/scripts.

```
./
├── data/
│   ├── raw/                    # Raw JSON files (ignored by git)
│   └── processed/              # Processed CSV data and visualizations
├── src/
│   ├── chess_fetch.py          # Data fetching from Chess.com API
│   ├── chess_process.py        # Data processing and cleaning
│   └── utils.py                # Utility functions and helpers
├── notebooks/                  # Jupyter notebooks for exploration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd chess-project
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv chess_env
   
   # Windows
   chess_env\Scripts\activate
   
   # macOS/Linux
   source chess_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### 1. Fetch Chess Game Data

Download games for a specific Chess.com user:

```bash
python src/chess_fetch.py --user <username>
```

**Example:**
```bash
python src/chess_fetch.py --user hikaru
```

**Options:**
- `--user`: Chess.com username (required)
- `--data-dir`: Directory to save raw data (default: `data/raw`)
- `--delay`: Delay between API calls in seconds (default: 1.0)
- `--log-level`: Logging level (default: INFO)

**Output:** Raw JSON files saved as `data/raw/username_YYYY_MM.json`

#### 2. Process Raw Data

Transform raw JSON files into clean CSV format:

```bash
python src/chess_process.py
```

**Options:**
-   `--raw-dir`: Directory containing raw JSON files (default: `data/raw`)
-   `--processed-dir`: Directory for processed output (default: `data/processed`)
-   `--output`: Output CSV filename (default: `processed.csv`)
-   `--log-level`: Logging level (default: INFO)

**Output:** Clean CSV file at `data/processed/processed.csv` ready for import into your BI tool.

## 📊 Data Schema

The processed CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `white_username` | White player's username |
| `black_username` | Black player's username |
| `white_rating` | White player's rating |
| `black_rating` | Black player's rating |
| `result` | Game result from Chess.com |
| `result_category` | Standardized result category |
| `end_date` | Game end date (YYYY-MM-DD) |
| `end_datetime` | Full game end timestamp |
| `end_time` | Unix timestamp |
| `time_control` | Time control format |
| `move_count` | Number of moves in the game |
| `eco_code` | ECO opening classification |
| `opening_name` | Opening name |
| `url` | Chess.com game URL |
| `pgn_result` | Result from PGN parsing |



## 🔧 Advanced Usage

### Custom Data Directory

```bash
# Fetch data to custom directory
python src/chess_fetch.py --user magnus --data-dir custom_data/raw

# Process from custom directory
python src/chess_process.py --raw-dir custom_data/raw --processed-dir custom_data/processed
```

### Batch Processing Multiple Users

Create a simple batch script:

```bash
# Windows batch file (fetch_multiple.bat)
python src/chess_fetch.py --user hikaru
python src/chess_fetch.py --user magnus
python src/chess_fetch.py --user gothamchess
python src/chess_process.py
```

### Rate Limiting

To avoid hitting API rate limits, adjust the delay:

```bash
python src/chess_fetch.py --user hikaru --delay 2.0
```

## 📚 Example Outputs

### Sample Console Output

```
2024-01-15 10:30:15 - INFO - Starting download for user: hikaru
2024-01-15 10:30:16 - INFO - Found 24 monthly archives for user hikaru
2024-01-15 10:30:17 - INFO - Saved 89 games to hikaru_2024_01.json
2024-01-15 10:30:19 - INFO - Saved 95 games to hikaru_2023_12.json
...
2024-01-15 10:35:22 - INFO - Download completed!
2024-01-15 10:35:22 - INFO - Archives found: 24
2024-01-15 10:35:22 - INFO - Archives downloaded: 24
2024-01-15 10:35:22 - INFO - Total games: 2,156
```

### Generated Files

After running all three steps, you'll have:

```
data/
├── raw/
│   ├── hikaru_2024_01.json
│   ├── hikaru_2023_12.json
│   └── ...
└── processed/
    └── processed.csv
```

## 🛠️ Dependencies

- **requests** - HTTP library for Chess.com API calls
- **pandas** - Data manipulation and analysis
- **python-chess** - Chess game parsing and analysis
- **matplotlib** - Plotting and visualization

## ⚠️ Important Notes

### API Rate Limiting
- Chess.com API has rate limits
- Default 1-second delay between requests
- Increase delay if you encounter rate limit errors

### Data Validation
- Games with missing required fields are skipped
- Duplicate games are automatically removed
- Invalid ratings and dates are handled gracefully

### File Management
- Existing files are not re-downloaded (saves time and API calls)
- Use relative paths only (no hardcoded absolute paths)
- All directories are created automatically

## 🔍 Troubleshooting

### Common Issues

1. **No games found for user**
   - Verify the username is correct and public
   - Check if the user has played rated games

2. **API connection errors**
   - Check internet connection
   - Increase delay between requests
   - Verify Chess.com API is accessible

3. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Permission errors**
   - Ensure write permissions to data directories
   - Run from project root directory

### Debug Mode

Enable debug logging for more detailed output:

```bash
python src/chess_fetch.py --user hikaru --log-level DEBUG
```

## 🚀 Future Enhancements

Potential improvements and extensions:

- **FastAPI Web Service** - RESTful API for data access
- **Streamlit Dashboard** - Interactive web-based analytics
- **Incremental Updates** - Fetch only new games since last run
- **Database Integration** - Store data in PostgreSQL/SQLite
- **Advanced Analytics** - ELO prediction, opening analysis
- **Multi-platform Support** - Lichess.org integration

## 📄 License

This project is for educational purposes. Please respect Chess.com's API terms of service and rate limits.

## 🤝 Contributing

1. Follow the existing code structure and style
2. Add proper error handling and logging
3. Update documentation for new features
4. Test with different usernames and data sizes

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review console output and logs
3. Verify all dependencies are installed
4. Ensure proper file permissions and directory structure