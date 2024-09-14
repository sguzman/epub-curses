import curses
import sys
import os
import json
import shutil
import threading
import time
from pydub import AudioSegment
from pydub.playback import play

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
TEXTS_JSON = os.path.join(CACHE_DIR, 'texts.json')

def get_cached_texts():
    if os.path.exists(TEXTS_JSON):
        with open(TEXTS_JSON, 'r') as f:
            return json.load(f)
    return {}

def save_cached_texts(texts):
    with open(TEXTS_JSON, 'w') as f:
        json.dump(texts, f, indent=2)

def get_last_position(text_id):
    texts = get_cached_texts()
    return texts.get(text_id, {}).get('progress', 0)

def save_last_position(text_id, last_line):
    texts = get_cached_texts()
    if text_id not in texts:
        texts[text_id] = {}
    texts[text_id]['progress'] = last_line
    save_cached_texts(texts)

def copy_to_cache(text_file, audio_file, alignment_file):
    text_id = os.path.splitext(os.path.basename(text_file))[0]
    text_dir = os.path.join(CACHE_DIR, text_id)
    
    if not os.path.exists(text_dir):
        os.makedirs(text_dir)
    
    cached_text = os.path.join(text_dir, 'text.txt')
    cached_audio = os.path.join(text_dir, 'audio' + os.path.splitext(audio_file)[1])
    cached_alignment = os.path.join(text_dir, 'alignment.json')
    
    shutil.copy2(text_file, cached_text)
    shutil.copy2(audio_file, cached_audio)
    shutil.copy2(alignment_file, cached_alignment)
    
    texts = get_cached_texts()
    texts[text_id] = {
        'text': cached_text,
        'audio': cached_audio,
        'alignment': cached_alignment,
        'progress': 0
    }
    save_cached_texts(texts)
    
    return text_id, cached_text, cached_audio, cached_alignment

def play_audio(audio, start_time, stop_event):
    segment = audio[start_time:]
    play(segment)
    stop_event.set()

def main(stdscr):
    curses.curs_set(0)

    if len(sys.argv) < 4:
        texts = get_cached_texts()
        if not texts:
            print("No cached texts available. Please provide text, audio, and alignment files as arguments.")
            return
        
        stdscr.clear()
        stdscr.addstr(0, 0, "Select a cached text:")
        for i, (text_id, text_info) in enumerate(texts.items()):
            stdscr.addstr(i+2, 0, f"{i+1}. {text_id} (Progress: {text_info['progress']})")
        stdscr.refresh()
        
        while True:
            key = stdscr.getch()
            if ord('1') <= key <= ord(str(len(texts))):
                selected_text = list(texts.keys())[key - ord('1')]
                text_id = selected_text
                cached_text = texts[selected_text]['text']
                cached_audio = texts[selected_text]['audio']
                cached_alignment = texts[selected_text]['alignment']
                break
    else:
        text_file, audio_file, alignment_file = sys.argv[1:4]
        text_id, cached_text, cached_audio, cached_alignment = copy_to_cache(text_file, audio_file, alignment_file)

    # Load files
    with open(cached_text, 'r') as f:
        lines = f.readlines()
    
    audio = AudioSegment.from_file(cached_audio)
    
    try:
        with open(cached_alignment, 'r', encoding='utf-8') as f:
            alignment = json.load(f)
    except UnicodeDecodeError:
        with open(cached_alignment, 'r', encoding='utf-8', errors='ignore') as f:
            alignment = json.load(f)

    total_words = sum(len(line.split()) for line in lines)
    current_line = get_last_position(text_id)
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
                stdscr.addstr(i, 5, line[:width-5], curses.A_REVERSE)
            else:
                stdscr.addstr(i, 5, line[:width-5])

        words_before = sum(len(line.split()) for line in lines[:current_line])
        current_word_count = words_before + len(lines[current_line].split())
        percent = (current_line + 1) / len(lines) * 100

        status = f"Line: {current_line+1}/{len(lines)} ({percent:.1f}%) | "
        status += f"Words: {current_word_count}/{total_words}"
        audio_status = f"Audio: {current_time:.1f}s / {total_time:.1f}s"
        
        stdscr.addstr(height-1, 0, status[:width-len(audio_status)-1], curses.A_REVERSE)
        stdscr.addstr(height-1, width-len(audio_status), audio_status, curses.A_REVERSE)

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            save_last_position(text_id, current_line)
            if audio_thread and audio_thread.is_alive():
                stop_event.set()
                audio_thread.join()
            break
        elif key == ord(' '):
            if audio_thread and audio_thread.is_alive():
                stop_event.set()
                audio_thread.join()
            else:
                current_fragment = next((f for f in alignment['fragments'] if f['lines'][0] == current_line), None)
                if current_fragment:
                    start_time = current_fragment['begin'] * 1000  # convert to milliseconds
                    stop_event.clear()
                    audio_thread = threading.Thread(target=play_audio, args=(audio, start_time, stop_event))
                    audio_thread.start()
        elif key in (ord('k'), ord('K'), curses.KEY_UP):
            current_line = max(0, current_line - 1)
        elif key in (ord('j'), ord('J'), curses.KEY_DOWN):
            current_line = min(len(lines) - 1, current_line + 1)
        elif key in (ord('h'), ord('H'), curses.KEY_LEFT):
            current_line = 0
        elif key in (ord('l'), ord('L'), curses.KEY_RIGHT):
            current_line = len(lines) - 1
        elif key in (ord('f'), ord('F')):
            current_line = min(current_line + height - 2, len(lines) - 1)
        elif key in (ord('b'), ord('B')):
            current_line = max(0, current_line - (height - 2))
        elif key == ord('g'):
            current_line = 0
        elif key in (ord('G'), ord('$')):
            current_line = len(lines) - 1

        if audio_thread and audio_thread.is_alive():
            for fragment in alignment['fragments']:
                if fragment['begin'] <= current_time < fragment['end']:
                    current_line = fragment['lines'][0]
                    break
            current_time += 0.1  # Update every 100ms
        else:
            current_time = 0

        time.sleep(0.1)

if __name__ == "__main__":
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    curses.wrapper(main)