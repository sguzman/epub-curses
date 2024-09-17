import curses
import time
from cache import get_cached_texts, get_last_position, copy_to_cache
from file_operations import read_file_lines, count_total_words
from ui import draw, handle_input
from text_selection import display_cached_texts, select_cached_text
from cli import parse_arguments


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
    curses.wrapper(main)
