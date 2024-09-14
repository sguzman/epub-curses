import curses
import sys
import os
import json
import shutil

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")


def get_cached_files():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    return [f for f in os.listdir(CACHE_DIR) if f.endswith(".txt")]


def get_last_position(filename):
    position_file = os.path.join(CACHE_DIR, f"{filename}.json")
    if os.path.exists(position_file):
        with open(position_file, "r") as f:
            return json.load(f)["last_line"]
    return 0


def save_last_position(filename, last_line):
    position_file = os.path.join(CACHE_DIR, f"{filename}.json")
    with open(position_file, "w") as f:
        json.dump({"last_line": last_line}, f)


def main(stdscr):
    curses.curs_set(0)

    if len(sys.argv) < 2:
        cached_files = get_cached_files()
        if not cached_files:
            print(
                "No cached files available. Please provide a file name as an argument."
            )
            return

        stdscr.clear()
        stdscr.addstr(0, 0, "Select a cached file:")
        for i, file in enumerate(cached_files):
            stdscr.addstr(i + 2, 0, f"{i+1}. {file}")
        stdscr.refresh()

        while True:
            key = stdscr.getch()
            if ord("1") <= key <= ord(str(len(cached_files))):
                selected_file = cached_files[key - ord("1")]
                filepath = os.path.join(CACHE_DIR, selected_file)
                break
    else:
        filepath = sys.argv[1]
        filename = os.path.basename(filepath)
        cache_path = os.path.join(CACHE_DIR, filename)

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        shutil.copy2(filepath, cache_path)
        filepath = cache_path

    try:
        with open(filepath, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"File '{filepath}' not found.")
        return

    total_words = sum(len(line.split()) for line in lines)
    current_line = get_last_position(os.path.basename(filepath))
    height, width = stdscr.getmaxyx()

    while True:
        stdscr.clear()

        for i in range(height - 2):
            if current_line + i < len(lines):
                line_num = current_line + i + 1
                line = lines[current_line + i].strip()

                stdscr.addstr(i, 0, f"{line_num:4d} ", curses.A_DIM)

                if i == 0:
                    stdscr.addstr(i, 5, line[: width - 5], curses.A_REVERSE)
                else:
                    stdscr.addstr(i, 5, line[: width - 5])

        words_before = sum(len(line.split()) for line in lines[:current_line])
        current_word_count = words_before + len(lines[current_line].split())
        percent = (current_line + 1) / len(lines) * 100

        status = f"Line: {current_line+1}/{len(lines)} ({percent:.1f}%) | "
        status += f"Words: {current_word_count}/{total_words}"
        stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_REVERSE)

        key = stdscr.getch()

        if key == ord("q"):
            save_last_position(os.path.basename(filepath), current_line)
            break
        elif key == curses.KEY_UP and current_line > 0:
            current_line -= 1
        elif key == curses.KEY_DOWN and current_line < len(lines) - 1:
            current_line += 1
        elif key == ord(" "):
            new_line = min(current_line + height - 2, len(lines) - 1)
            current_line = new_line


if __name__ == "__main__":
    curses.wrapper(main)
