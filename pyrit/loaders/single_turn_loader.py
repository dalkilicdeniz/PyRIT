# single_turn_loader.py
import yaml
from pathlib import Path
from typing import List, Tuple, Union


def extract_single_turn_tests(
    file_path: Union[str, Path]
) -> Tuple[List[str], List[str]]:
    """Parses single QA format YAML files into prompt/expected lists."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not all("question" in item and "expected_outcome" in item for item in data):
        raise ValueError("Invalid single-turn QA format")

    prompt_list = [item["question"] for item in data]
    expected_output_list = [item["expected_outcome"] for item in data]

    return prompt_list, expected_output_list