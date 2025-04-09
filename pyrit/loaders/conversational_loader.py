# conversational_loader.py
import yaml
from pathlib import Path
from typing import List, Tuple, Union


def extract_conversational_tests(
    file_path: Union[str, Path]
) -> Tuple[List[str], List[str]]:
    """Parses conversational format YAML files into flattened prompt/expected lists."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not all("conversation" in item for item in data):
        raise ValueError("Invalid conversational QA format")

    prompt_list = []
    expected_output_list = []

    for case in data:
        for turn in case["conversation"]:
            prompt_list.append(turn["question"])
            expected_output_list.append(turn["expected_outcome"])

    return prompt_list, expected_output_list