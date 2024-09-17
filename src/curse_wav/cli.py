import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="Text viewer with caching")
    parser.add_argument("--text", help="Path to the text file")
    return parser.parse_args()
