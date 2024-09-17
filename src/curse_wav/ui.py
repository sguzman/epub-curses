import curses
from typing import List, Optional, Tuple
from cache import save_last_position


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
