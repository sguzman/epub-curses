import curses
import sys
import os
import json
import shutil
import threading
import time
from pydub import AudioSegment
from pydub.playback import play

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


def play_audio(audio, start_time, stop_event):
    segment = audio[start_time:]
    play(segment)
    stop_event.set()


def main(stdscr):
    curses.curs_set(0)

    if len(sys.argv) < 4:
        print("Usage: python script.py <text_file> <audio_file> <alignment_file>")
        return

    text_file, audio_file, alignment_file = sys.argv[1:4]

    # Copy files to cache
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cached_text = os.path.join(CACHE_DIR, os.path.basename(text_file))
    cached_audio = os.path.join(CACHE_DIR, os.path.basename(audio_file))
    cached_alignment = os.path.join(CACHE_DIR, os.path.basename(alignment_file))

    shutil.copy2(text_file, cached_text)
    shutil.copy2(audio_file, cached_audio)
    shutil.copy2(alignment_file, cached_alignment)

    # Load files
    with open(cached_text, "r") as f:
        lines = f.readlines()

    audio = AudioSegment.from_file(cached_audio)

    with open(cached_alignment, "r") as f:
        alignment = json.load(f)

    total_words = sum(len(line.split()) for line in lines)
    current_line = get_last_position(os.path.basename(cached_text))
    height, width = stdscr.getmaxyx()
    mid_screen = height // 2 - 1

    audio_thread = None
    stop_event = threading.Event()
    current_time = 0
    total_time = len(audio) / 1000  # in seconds

    while True:
        stdscr.clear()

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
        audio_status = f"Audio: {current_time:.1f}s / {total_time:.1f}s"

        stdscr.addstr(
            height - 1, 0, status[: width - len(audio_status) - 1], curses.A_REVERSE
        )
        stdscr.addstr(
            height - 1, width - len(audio_status), audio_status, curses.A_REVERSE
        )

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            save_last_position(os.path.basename(cached_text), current_line)
            if audio_thread and audio_thread.is_alive():
                stop_event.set()
                audio_thread.join()
            break
        elif key == ord(" "):
            if audio_thread and audio_thread.is_alive():
                stop_event.set()
                audio_thread.join()
            else:
                current_fragment = next(
                    (
                        f
                        for f in alignment["fragments"]
                        if f["lines"][0] == current_line
                    ),
                    None,
                )
                if current_fragment:
                    start_time = (
                        current_fragment["begin"] * 1000
                    )  # convert to milliseconds
                    stop_event.clear()
                    audio_thread = threading.Thread(
                        target=play_audio, args=(audio, start_time, stop_event)
                    )
                    audio_thread.start()

        # ... (keep the other navigation commands as they are) ...

        if audio_thread and audio_thread.is_alive():
            for fragment in alignment["fragments"]:
                if fragment["begin"] <= current_time < fragment["end"]:
                    current_line = fragment["lines"][0]
                    break
            current_time += 0.1  # Update every 100ms
        else:
            current_time = 0

        time.sleep(0.1)


if __name__ == "__main__":
    curses.wrapper(main)
