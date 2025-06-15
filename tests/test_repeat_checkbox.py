import os
import sys
import json
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.ocr_paddle import detect_repeat_checkbox


def test_detect_repeat_checkbox():
    img = Image.open(os.path.join(os.path.dirname(__file__), '..', 'ocr_debug_output.jpg'))
    with open(os.path.join(os.path.dirname(__file__), '..', 'ocr_debug_output.json'), encoding='utf-8') as f:
        lines = json.load(f)
    assert detect_repeat_checkbox(img, lines) is True

