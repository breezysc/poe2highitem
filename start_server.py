import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from backend.api import app

if __name__ == '__main__':
    print("Starting POE2 Unique Monitor Server...")
    app.run(host='0.0.0.0', port=8000, debug=False)
