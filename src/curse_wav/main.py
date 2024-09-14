import curses
import sys
import os
import json
import shutil

CACHE_DIR = os.path.join(".", ".cache")


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
    mid_screen = height // 2 - 1

    while True:
        stdscr.clear()

        # Calculate the range of lines to display
        start_line = max(0, current_line - mid_screen)
        end_line = min(len(lines), start_line + height - 2)

        for i, line_num in enumerate(range(start_line, end_line)):
            line = lines[line_num].strip()

            stdscr.addstr(i, 0, f"{line_num+1:4d} ", curses.A_DIM)

            if line_num == current_line:
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

        if key in (ord("q"), ord("Q")):
            save_last_position(os.path.basename(filepath), current_line)
            break
        elif key in (ord("k"), ord("K"), curses.KEY_UP):
            current_line = max(0, current_line - 1)
        elif key in (ord("j"), ord("J"), curses.KEY_DOWN):
            current_line = min(len(lines) - 1, current_line + 1)
        elif key in (ord("h"), ord("H"), curses.KEY_LEFT):
            # Move to the start of the file
            current_line = 0
        elif key in (ord("l"), ord("L"), curses.KEY_RIGHT):
            # Move to the end of the file
            current_line = len(lines) - 1
        elif key in (ord("f"), ord("F")):
            # Page down (Forward)
            current_line = min(current_line + height - 2, len(lines) - 1)
        elif key in (ord("b"), ord("B")):
            # Page up (Backward)
            current_line = max(0, current_line - (height - 2))
        elif key == ord("g"):
            # Go to the start of the file
            current_line = 0
        elif key in (ord("G"), ord("$")):
            # Go to the end of the file
            current_line = len(lines) - 1
        elif key == ord("/"):
            # Implement search functionality here if needed
            pass


if __name__ == "__main__":
    curses.wrapper(main)
