import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'rooms.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    rooms_by_bz: dict[str, list[str]] = json.load(f)
