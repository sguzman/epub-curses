import curses
import os
import json
import shutil
import argparse

CACHE_DIR = os.path.join(os.getcwd(), ".cache")
TEXTS_JSON = os.path.join(CACHE_DIR, "texts.json")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Text viewer with caching")
    parser.add_argument("--text", help="Path to the text file")
    return parser.parse_args()


def get_cached_texts():
    if os.path.exists(TEXTS_JSON):
        with open(TEXTS_JSON, "r") as f:
            return json.load(f)
    return {}


def save_cached_texts(texts):
    with open(TEXTS_JSON, "w") as f:
        json.dump(texts, f, indent=2)


def get_last_position(text_id):
    texts = get_cached_texts()
    return texts.get(text_id, {}).get("progress", 0)


def save_last_position(text_id, last_line):
    texts = get_cached_texts()
    if text_id not in texts:
        texts[text_id] = {}
    texts[text_id]["progress"] = last_line
    save_cached_texts(texts)


def copy_to_cache(text_file):
    text_id = os.path.splitext(os.path.basename(text_file))[0]
    text_dir = os.path.join(CACHE_DIR, text_id)

    if not os.path.exists(text_dir):
        os.makedirs(text_dir)

    cached_text = os.path.join(text_dir, "text.txt")
    shutil.copy2(text_file, cached_text)

    texts = get_cached_texts()
    texts[text_id] = {
        "text": cached_text,
        "progress": 0,
    }
    save_cached_texts(texts)

    return text_id, cached_text


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

        stdscr.clear()
        stdscr.addstr(0, 0, "Select a cached text:")
        for i, (text_id, text_info) in enumerate(texts.items()):
            stdscr.addstr(
                i + 2, 0, f"{i+1}. {text_id} (Progress: {text_info['progress']})"
            )
        stdscr.refresh()

        while True:
            key = stdscr.getch()
            if ord("1") <= key <= ord(str(len(texts))):
                selected_text = list(texts.keys())[key - ord("1")]
                text_id = selected_text
                cached_text = texts[selected_text]["text"]
                break
    else:
        text_id, cached_text = copy_to_cache(args.text)

    with open(cached_text, "r") as f:
        lines = f.readlines()

    total_words = sum(len(line.split()) for line in lines)
    current_line = get_last_position(text_id)
    height, width = stdscr.getmaxyx()
    mid_screen = height // 2 - 1

    while True:
        stdscr.clear()

        start_line = max(0, current_line - mid_screen)
        end_line = min(len(lines), start_line + height - 2)

        visible_lines = lines[start_line:end_line]
        for i, line in enumerate(visible_lines):
            line_num = start_line + i
            stdscr.addstr(i, 0, f"{line_num+1:4d} ", curses.A_DIM)
            if line_num == current_line:
                stdscr.addstr(i, 5, line.strip()[: width - 5], curses.A_REVERSE)
            else:
                stdscr.addstr(i, 5, line.strip()[: width - 5])

        words_before = sum(len(line.split()) for line in lines[:current_line])
        current_word_count = words_before + len(lines[current_line].split())
        percent = (current_line + 1) / len(lines) * 100

        status = f"Line: {current_line+1}/{len(lines)} ({percent:.1f}%) | "
        status += f"Words: {current_word_count}/{total_words}"

        stdscr.addstr(height - 1, 0, status[:width], curses.A_REVERSE)

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            save_last_position(text_id, current_line)
            break
        elif key in (ord("k"), ord("K"), curses.KEY_UP):
            current_line = max(0, current_line - 1)
        elif key in (ord("j"), ord("J"), curses.KEY_DOWN):
            current_line = min(len(lines) - 1, current_line + 1)
        elif key in (ord("h"), ord("H"), curses.KEY_LEFT):
            current_line = max(0, current_line - 10)
        elif key in (ord("l"), ord("L"), curses.KEY_RIGHT):
            current_line = min(len(lines) - 1, current_line + 10)
        elif key in (ord("f"), ord("F")):
            current_line = min(current_line + height - 2, len(lines) - 1)
        elif key in (ord("b"), ord("B")):
            current_line = max(0, current_line - (height - 2))
        elif key == ord("g"):
            current_line = 0
        elif key in (ord("G"), ord("$")):
            current_line = len(lines) - 1


if __name__ == "__main__":
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    curses.wrapper(main)
