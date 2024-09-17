import os
import json
import shutil
from typing import Dict, Tuple

CACHE_DIR = os.path.join(os.getcwd(), ".cache")
TEXTS_JSON = os.path.join(CACHE_DIR, "texts.json")

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def get_cached_texts() -> Dict:
    if os.path.exists(TEXTS_JSON):
        with open(TEXTS_JSON, "r") as f:
            return json.load(f)
    return {}


def save_cached_texts(texts: Dict):
    with open(TEXTS_JSON, "w") as f:
        json.dump(texts, f, indent=2)


def get_last_position(text_id: str) -> int:
    texts = get_cached_texts()
    return texts.get(text_id, {}).get("progress", 0)


def save_last_position(text_id: str, last_line: int):
    texts = get_cached_texts()
    if text_id not in texts:
        texts[text_id] = {}
    texts[text_id]["progress"] = last_line
    save_cached_texts(texts)


def copy_to_cache(text_file: str) -> Tuple[str, str]:
    text_id = os.path.splitext(os.path.basename(text_file))[0]
    text_dir = os.path.join(CACHE_DIR, text_id)
    os.makedirs(text_dir, exist_ok=True)
    cached_text = os.path.join(text_dir, "text.txt")
    shutil.copy2(text_file, cached_text)
    texts = get_cached_texts()
    texts[text_id] = {"text": cached_text, "progress": 0}
    save_cached_texts(texts)
    return text_id, cached_text
