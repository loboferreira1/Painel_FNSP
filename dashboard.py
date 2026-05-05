"""Streamlit TI Dashboard - Root launcher."""
import sys
from pathlib import Path

# Ensure project root is in path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Import and run the actual app
from src.ti_dashboard import app

if __name__ == "__main__":
    app.main()
