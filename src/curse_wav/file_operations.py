from typing import List


def read_file_lines(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        return f.readlines()


def count_total_words(lines: List[str]) -> int:
    return sum(len(line.split()) for line in lines)
