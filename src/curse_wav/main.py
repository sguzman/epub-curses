import curses
import os
import json
import shutil
import argparse
from typing import Optional, List, Dict, Tuple
import time

CACHE_DIR = os.path.join(os.getcwd(), ".cache")
TEXTS_JSON = os.path.join(CACHE_DIR, "texts.json")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Text viewer with caching")
    parser.add_argument("--text", help="Path to the text file")
    return parser.parse_args()


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


def display_cached_texts(stdscr, texts: Dict):
    stdscr.clear()
    stdscr.addstr(0, 0, "Select a cached text:")
    for i, (text_id, text_info) in enumerate(texts.items()):
        stdscr.addstr(i + 2, 0, f"{i+1}. {text_id} (Progress: {text_info['progress']})")
    stdscr.refresh()


def select_cached_text(stdscr, texts: Dict) -> Tuple[str, str]:
    while True:
        key = stdscr.getch()
        if ord("1") <= key <= ord(str(len(texts))):
            selected_text = list(texts.keys())[key - ord("1")]
            return selected_text, texts[selected_text]["text"]


def read_file_lines(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        return f.readlines()


def count_total_words(lines: List[str]) -> int:
    return sum(len(line.split()) for line in lines)


def handle_input(
    stdscr, text_id: str, current_line: int, max_line: int, height: int
) -> Tuple[Optional[bool], int]:
    key = stdscr.getch()
    if key in (ord("q"), ord("Q")):
        save_last_position(text_id, current_line)
        return None, current_line
    elif key in (ord("k"), ord("K"), curses.KEY_UP):
        return True, max(0, current_line - 1)
    elif key in (ord("j"), ord("J"), curses.KEY_DOWN):
        current_line = min(max_line, current_line + 1)
    elif key in (ord("h"), ord("H"), curses.KEY_LEFT):
        current_line = max(0, current_line - 10)
    elif key in (ord("l"), ord("L"), curses.KEY_RIGHT):
        current_line = min(max_line, current_line + 10)
    elif key in (ord("f"), ord("F")):
        current_line = min(current_line + height - 2, max_line)
    elif key in (ord("b"), ord("B")):
        current_line = max(0, current_line - (height - 2))
    elif key == ord("g"):
        current_line = 0
    elif key in (ord("G"), ord("$")):
        current_line = max_line
    else:
        return False, current_line
    return True, current_line


def draw_lines(
    stdscr,
    lines: List[str],
    current_line: int,
    start_line: int,
    end_line: int,
    height: int,
    width: int,
):
    for i, line in enumerate(lines[start_line:end_line]):
        line_num = start_line + i
        stdscr.addstr(i, 0, f"{line_num+1:4d} ", curses.A_DIM)
        if line_num == current_line:
            stdscr.addstr(i, 5, line.strip()[: width - 5], curses.A_REVERSE)
        else:
            stdscr.addstr(i, 5, line.strip()[: width - 5])


def draw_status_bar(
    stdscr,
    current_line: int,
    total_lines: int,
    current_word_count: int,
    total_words: int,
    height: int,
    width: int,
):
    percent = (current_line + 1) / total_lines * 100
    status = f"Line: {current_line+1}/{total_lines} ({percent:.1f}%) | "
    status += f"Words: {current_word_count}/{total_words}"
    stdscr.addstr(height - 1, 0, status[:width], curses.A_REVERSE)


def draw(stdscr, lines: List[str], current_line: int, total_words: int):
    height, width = stdscr.getmaxyx()
    mid_screen = height // 2 - 1
    stdscr.clear()
    start_line = max(0, current_line - mid_screen)
    end_line = min(len(lines), start_line + height - 2)

    draw_lines(stdscr, lines, current_line, start_line, end_line, height, width)

    words_before = sum(len(line.split()) for line in lines[:current_line])
    current_word_count = words_before + len(lines[current_line].split())

    draw_status_bar(
        stdscr, current_line, len(lines), current_word_count, total_words, height, width
    )
    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)

    args = parse_arguments()

    if not args.text:
        texts = get_cached_texts()
        if not texts:
            print(
                "No cached texts available. Please provide a text file using --text flag."
            )
            return
        display_cached_texts(stdscr, texts)
        text_id, cached_text = select_cached_text(stdscr, texts)
    else:
        text_id, cached_text = copy_to_cache(args.text)

    lines = read_file_lines(cached_text)
    total_words = count_total_words(lines)
    current_line = get_last_position(text_id)

    draw(stdscr, lines, current_line, total_words)
    while True:
        time.sleep(0.01)
        result, current_line = handle_input(
            stdscr, text_id, current_line, len(lines) - 1, stdscr.getmaxyx()[0]
        )
        if result is None:
            break
        elif result:
            draw(stdscr, lines, current_line, total_words)


if __name__ == "__main__":
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    curses.wrapper(main)
