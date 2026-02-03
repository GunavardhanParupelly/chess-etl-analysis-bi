# Dashboard link

https://analytics.zoho.in/open-view/497352000000045923


# Chess ETL Project

A ETL pipeline to fetch and analyze Chess.com games.

## 🚀 Quick Start

### 1. Installation

Clone the repo and install dependencies:

```bash
git clone <your-repo-url>
cd chess-project

# Windows
python -m venv chess_env
chess_env\Scripts\activate

# macOS/Linux
# python -m venv chess_env
# source chess_env/bin/activate

pip install -r requirements.txt
```

### 2. Fetch Data

Download games for a user (e.g., `hikaru`):

```bash
python src/chess_fetch.py --user hikaru
```

### 3. Process Data

Convert the downloaded games into a clean CSV:

```bash
python src/chess_process.py
```

## 📊 Output

The final data is saved to: `data/processed/processed.csv`.

You can import this CSV directly into **PowerBI**, **Tableau**, or **Excel** for analysis.

## 🛠️ Options

- **Fetch with delay** (to avoid rate limits):
  ```bash
  python src/chess_fetch.py --user hikaru --delay 2.0
  ```

- **Debug mode** (for more details):
  ```bash
  python src/chess_fetch.py --user hikaru --log-level DEBUG
