import curses
import sys


def main(stdscr):
    # Hide the cursor
    curses.curs_set(0)

    # Get the file contents
    try:
        with open(sys.argv[1], "r") as file:
            lines = file.readlines()
    except IndexError:
        print("Please provide a file name as an argument.")
        return
    except FileNotFoundError:
        print(f"File '{sys.argv[1]}' not found.")
        return

    # Calculate total words
    total_words = sum(len(line.split()) for line in lines)

    # Initialize variables
    current_line = 0
    height, width = stdscr.getmaxyx()

    while True:
        stdscr.clear()

        # Display text
        for i in range(height - 2):
            if current_line + i < len(lines):
                line_num = current_line + i + 1
                line = lines[current_line + i].strip()

                # Line number column
                stdscr.addstr(i, 0, f"{line_num:4d} ", curses.A_DIM)

                # Highlight current line
                if i == 0:
                    stdscr.addstr(i, 5, line[: width - 5], curses.A_REVERSE)
                else:
                    stdscr.addstr(i, 5, line[: width - 5])

        # Calculate statistics
        words_before = sum(len(line.split()) for line in lines[:current_line])
        words_left = total_words - words_before
        percent = (current_line + 1) / len(lines) * 100

        # Display status bar
        status = f"Line: {current_line+1}/{len(lines)} ({percent:.1f}%) | "
        status += f"Words: {total_words} | Before: {words_before} | Left: {words_left}"
        stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_REVERSE)

        # Get user input
        key = stdscr.getch()

        if key == ord("q"):
            break
        elif key == curses.KEY_UP and current_line > 0:
            current_line -= 1
        elif key == curses.KEY_DOWN and current_line < len(lines) - 1:
            current_line += 1


if __name__ == "__main__":
    curses.wrapper(main)
