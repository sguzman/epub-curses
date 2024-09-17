from typing import Dict, Tuple


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
