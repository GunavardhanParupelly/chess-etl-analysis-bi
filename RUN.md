# Quick Run Guide

## Specifications
- **Python Version**: 3.8+
- **OS**: Windows / macOS / Linux
- **Output**: `data/processed/processed.csv`

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Execution Steps

1. **Fetch Data**
   ```bash
   python src/chess_fetch.py --user <username>
   # Example: python src/chess_fetch.py --user hikaru
   ```

2. **Process Data**
   ```bash
   python src/chess_process.py
   ```

3. **Result**
   - The verified CSV comes out at: `data/processed/processed.csv`.
   - Import this file into your BI tool (PowerBI, Tableau, etc).
