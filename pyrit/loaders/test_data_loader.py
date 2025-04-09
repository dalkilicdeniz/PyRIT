# test_data_loader.py
from pathlib import Path
from typing import List, Tuple, Union
from .single_turn_loader import extract_single_turn_tests
from .conversational_loader import extract_conversational_tests


def load_test_data(
    file_path: Union[str, Path]
) -> Tuple[List[str], List[str]]:
    """
    Auto-detects YAML format (single-turn or conversational) and returns prompt/expected pairs.
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline()

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Use a basic heuristic to decide format
    if "conversation:" in content:
        return extract_conversational_tests(file_path)
    elif "question:" in content and "expected_outcomes:" in content:
        return extract_single_turn_tests(file_path)
    else:
        raise ValueError(f"Unknown test format in file: {file_path}")