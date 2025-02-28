# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from typing import List, Union
import re
import yaml


def combine_dict(existing_dict: dict = None, new_dict: dict = None) -> dict:
    """
    Combines two dictionaries containing string keys and values into one.

    Args:
        existing_dict: Dictionary with existing values
        new_dict: Dictionary with new values to be added to the existing dictionary.
            Note if there's a key clash, the value in new_dict will be used.

    Returns:
        dict: combined dictionary
    """
    result = {**(existing_dict or {})}
    result.update(new_dict or {})
    return result


def combine_list(list1: Union[str, List[str]], list2: Union[str, List[str]]) -> list:
    """
    Combines two lists containing string keys, keeping only unique values.

    Args:
        existing_dict: Dictionary with existing values
        new_dict: Dictionary with new values to be added to the existing dictionary.
            Note if there's a key clash, the value in new_dict will be used.

    Returns:
        list: combined dictionary
    """
    if isinstance(list1, str):
        list1 = [list1]
    if isinstance(list2, str):
        list2 = [list2]

    # Merge and keep only unique values
    combined = list(set(list1 + list2))
    return combined

def update_yaml_with_regex(file_path, text, pattern=r'\{.*?\}'):
    with open(file_path, 'r') as file:
        yaml_content = yaml.safe_load(file)

    # Function to replace content inside curly braces with the topic, while keeping the braces
    def replace_with_topic(value):
        # Only apply the replacement if the value is a string
        if isinstance(value, str):
            return re.sub(pattern, f'{{{text}}}', value)
        return value

    # Recursively update all string fields in the YAML content
    def update_fields(data):
        if isinstance(data, dict):
            return {k: update_fields(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [update_fields(item) for item in data]
        else:
            return replace_with_topic(data)

    # Update all fields in the YAML content
    updated_content = update_fields(yaml_content)

    # Write the updated YAML content back to the file
    with open(file_path, 'w') as file:
        yaml.safe_dump(updated_content, file, default_flow_style=False, sort_keys=False)