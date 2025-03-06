# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, List
import datetime
from pathlib import Path

def read_txt(file) -> List[Dict[str, str]]:
    return [{"prompt": line.strip()} for line in file.readlines()]


def write_txt(file, examples: List[Dict[str, str]]):
    file.write("\n".join([ex["prompt"] for ex in examples]))

def generate_multi_turn_html_report(
        reports: list,
        is_chat_evaluation: bool = True
) -> str:
    """
    Generates an HTML report with a modern, accessible design.

    Features:
    - Light color scheme for better readability
    - Cumulative score labeling for chat evaluations
    - Cleaner, minimalist approach without search/export features

    Args:
        reports (list): A list of report dictionaries (multi-turn or single-turn).
        is_chat_evaluation (bool): If True, scores reflect the entire conversation (cumulative score).

    Returns:
        str: A complete HTML string.
    """

    # Set the score column label based on evaluation type
    score_column_label = "Cumulative Score" if is_chat_evaluation else "Score"

    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Report</title>
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500,700&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      font-family: 'Roboto', sans-serif;
      background: #f8f9fa; /* Light gray background */
      margin: 0;
      padding: 20px;
      color: #333;
    }
    .container {
      max-width: 1100px;
      margin: 0 auto;
      background: #fff;
      padding: 25px;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    h1 {
      text-align: center;
      font-size: 1.8rem;
      color: #2c3e50;
    }
    details {
      margin-bottom: 15px;
      border: 1px solid #ddd;
      border-radius: 6px;
      background-color: #fcfcfc;
      transition: all 0.3s ease;
      overflow: hidden;
    }
    details[open] {
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    summary {
      padding: 12px 18px;
      cursor: pointer;
      background: #e3f2fd; /* Light blue */
      color: #01579b;
      font-size: 1rem;
      font-weight: 500;
      border-radius: 6px;
      outline: none;
      transition: background 0.3s ease;
      border: none;
    }
    summary:hover {
      background: #bbdefb;
    }
    summary::-webkit-details-marker {
      display: none;
    }
    .metrics {
      background-color: #f1f8e9; /* Light green */
      padding: 12px 18px;
      margin: 0;
      border-bottom: 1px solid #ddd;
    }
    .objective-text {
      color: #0277bd;
      font-weight: bold;
    }
    .achieved-yes {
      color: #1b5e20;
      background-color: #c8e6c9;
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: bold;
    }
    .achieved-no {
      color: #b71c1c;
      background-color: #ffcdd2;
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: bold;
    }
    h3 {
      padding: 10px 18px;
      margin: 0;
      background: #e3f2fd;
      border-top: 1px solid #ddd;
      font-size: 1rem;
      font-weight: 500;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid #eee;
    }
    th {
      background-color: #0277bd;
      color: #fff;
      font-size: 0.9rem;
    }
    tr:nth-child(even) {
      background-color: #f9f9f9;
    }
    .metadata {
      font-size: 0.85rem;
      color: #666;
      padding: 10px 18px;
      border-top: 1px solid #ddd;
    }
    .score-list {
      list-style-type: none;
      padding: 0;
      margin: 0;
    }
    .score-list li {
      margin-bottom: 4px;
    }
    .explanation-block {
      display: inline-block;
      border: none;
      border-radius: 4px;
      background: transparent;
    }
    .explanation-block summary {
      background: #aed581;
      color: #fff;
      padding: 6px 10px;
      font-size: 0.85rem;
      cursor: pointer;
      border-radius: 4px;
      outline: none;
      border: none;
      display: inline-block;
      margin-bottom: 4px;
    }
    .explanation-block summary:hover {
      background: #9ccc65;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Multi-turn Chat Report</h1>
"""

    for index, report in enumerate(reports, start=1):
        objective = report.get("objective", "N/A")
        achieved = report.get("achieved_objective", False)
        aggregated = report.get("aggregated_metrics", {})
        total_turns = aggregated.get("total_turns", "N/A")
        final_score = aggregated.get("final_score", "N/A")
        final_score_rationale = aggregated.get("final_score_rationale", "")

        achieved_text = '<span class="achieved-yes">Yes</span>' if achieved else '<span class="achieved-no">No</span>'
        conversation_id = report.get("additional_metadata", {}).get("conversation_id", "N/A")

        summary_text = (
            f"Test Case {index}: Objective: <span class='objective-text'>{objective}</span> "
            f"| Achieved: {achieved_text} | Turns: {total_turns} | Final Score: {final_score}"
        )

        html += f"""
    <details>
      <summary>
        {summary_text}
      </summary>
      <div class="metrics">
        <p><strong>Objective:</strong> <span class="objective-text">{objective}</span></p>
        <p><strong>Achieved Objective:</strong> {achieved_text}</p>
        <p><strong>Total Turns:</strong> {total_turns}</p>
        <p><strong>Final Score:</strong> {final_score}</p>
"""
        if final_score_rationale:
            html += f"<p><strong>Final Score Rationale:</strong> {final_score_rationale}</p>"

        html += f"""
      </div>
      <h3>Transcript</h3>
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>Assistant</th>
            <th>{score_column_label}</th>
          </tr>
        </thead>
        <tbody>
"""

        transcript = report.get("transcript", [])
        for turn in transcript:
            user_text = "N/A"
            assistant_text = "N/A"
            score_html = "N/A"

            for piece in turn.get("pieces", []):
                role = piece.get("role", "").lower()
                converted_val = piece.get("converted_value", "")
                scores = piece.get("scores", [])

                if role == "user":
                    user_text = converted_val
                elif role == "assistant":
                    assistant_text = converted_val
                    if scores:
                        bullet_points = "".join(
                            f"<li><strong>{sc['score']}</strong> <details><summary>View Explanation</summary><div>{sc['rationale']}</div></details></li>"
                            for sc in scores
                        )
                        score_html = f"<ul class='score-list'>{bullet_points}</ul>"

            html += f"""
          <tr>
            <td>{user_text}</td>
            <td>{assistant_text}</td>
            <td>{score_html}</td>
          </tr>
"""

        html += "</tbody></table></details>"

    html += "</div></body></html>"
    return html

def generate_single_turn_html_report(results: list) -> str:
    """
    Generates an HTML report for single-turn dataset evaluations.

    Each entry in `reports` is expected to represent a single user prompt,
    a single assistant response, and any associated scoring metadata.

    Features:
    - Light color scheme for better readability
    - Cleaner, minimalist approach without search/export features
    - Summaries expand to show the user prompt, assistant response, and scoring details

    Args:
        results (list): A list of dictionaries, each representing a single dataset item
                        or single-turn conversation. Expected structure:
                          {
                            "conversation_id": str,
                            "prompt": str,
                            "assistant_response": str,
                            "scores": [
                                {
                                  "score_value": float,
                                  "score_rationale": str
                                },
                                ...
                            ]
                          }

    Returns:
        str: A complete HTML string containing the report.
    """

    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Single-Turn Dataset Report</title>
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500,700&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      font-family: 'Roboto', sans-serif;
      background: #f8f9fa; /* Light gray background */
      margin: 0;
      padding: 20px;
      color: #333;
    }
    .container {
      max-width: 1100px;
      margin: 0 auto;
      background: #fff;
      padding: 25px;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    h1 {
      text-align: center;
      font-size: 1.8rem;
      color: #2c3e50;
    }
    details {
      margin-bottom: 15px;
      border: 1px solid #ddd;
      border-radius: 6px;
      background-color: #fcfcfc;
      transition: all 0.3s ease;
      overflow: hidden;
    }
    details[open] {
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    summary {
      padding: 12px 18px;
      cursor: pointer;
      background: #e3f2fd; /* Light blue */
      color: #01579b;
      font-size: 1rem;
      font-weight: 500;
      border-radius: 6px;
      outline: none;
      transition: background 0.3s ease;
      border: none;
    }
    summary:hover {
      background: #bbdefb;
    }
    summary::-webkit-details-marker {
      display: none;
    }
    .metrics {
      background-color: #f1f8e9; /* Light green */
      padding: 12px 18px;
      margin: 0;
      border-bottom: 1px solid #ddd;
    }
    .conversation-id {
      color: #0277bd;
      font-weight: bold;
    }
    h3 {
      padding: 10px 18px;
      margin: 0;
      background: #e3f2fd;
      border-top: 1px solid #ddd;
      font-size: 1rem;
      font-weight: 500;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid #eee;
    }
    th {
      background-color: #0277bd;
      color: #fff;
      font-size: 0.9rem;
    }
    tr:nth-child(even) {
      background-color: #f9f9f9;
    }
    .score-list {
      list-style-type: none;
      padding: 0;
      margin: 0;
    }
    .score-list li {
      margin-bottom: 4px;
    }
    .explanation-block {
      display: inline-block;
      border: none;
      border-radius: 4px;
      background: transparent;
    }
    .explanation-block summary {
      background: #aed581;
      color: #fff;
      padding: 6px 10px;
      font-size: 0.85rem;
      cursor: pointer;
      border-radius: 4px;
      outline: none;
      border: none;
      display: inline-block;
      margin-bottom: 4px;
    }
    .explanation-block summary:hover {
      background: #9ccc65;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Single-Turn Dataset Evaluation Report</h1>
"""

    # Loop through each single-turn report
    for index, report in enumerate(results, start=1):
        conversation_id = report.get("conversation_id", f"SingleTurn-{index}")
        prompt = report.get("prompt", "N/A")
        assistant_response = report.get("assistant_response", "N/A")
        scores = report.get("scores", [])

        # Build a short summary text
        # e.g., "Test Case 1: Conversation ID: SingleTurn-1 | Score: 0.9"
        # If multiple scores, you might pick the first or combine them as needed
        if scores:
            # Example: take the average or highest
            main_score = max(float(s["score_value"]) for s in scores)
            summary_text = f"Test Case {index}: Conversation ID <span class='conversation-id'>{conversation_id}</span> | Score: {main_score}"
        else:
            summary_text = f"Test Case {index}: Conversation ID <span class='conversation-id'>{conversation_id}</span>"

        # Start the <details> block for this test case
        html += f"""
    <details>
      <summary>
        {summary_text}
      </summary>
      <div class="metrics">
        <p><strong>Conversation ID:</strong> <span class="conversation-id">{conversation_id}</span></p>
      </div>
      <h3>Transcript</h3>
      <table>
        <thead>
          <tr>
            <th>User Prompt</th>
            <th>Assistant Response</th>
            <th>Score(s)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{prompt}</td>
            <td>{assistant_response}</td>
            <td>
"""

        # If there are scores, display them in a bullet list
        if scores:
            bullet_points = []
            for s in scores:
                score_val = s.get("score_value", "N/A")
                rationale = s.get("score_rationale", "No rationale provided")
                bullet_points.append(
                    f"<li><strong>{score_val}</strong> "
                    f"<details class='explanation-block'><summary>View Explanation</summary>"
                    f"<div>{rationale}</div></details></li>"
                )
            html += f"<ul class='score-list'>{''.join(bullet_points)}</ul>"
        else:
            html += "N/A"

        # Close out the row, table, and details
        html += """
            </td>
          </tr>
        </tbody>
      </table>
    </details>
"""

    html += "</div></body></html>"
    return html


def save_html_report(
        results: list,
        directory: str = ".",
        report_generator=None,
        is_chat_evaluation: bool = True
) -> str:
    """
    Saves an HTML report generated by the specified report generator function.

    Args:
        results (list): A list of result dictionaries.
        directory (str): Directory where the report file will be saved.
        report_generator (callable): A function that takes `results` (and possibly
            `is_chat_evaluation`) and returns an HTML string. Defaults to None,
            in which case `generate_multi_turn_html_report` is used.
        is_chat_evaluation (bool): If True, scores reflect the entire conversation
            (cumulative score). Only used by the multi-turn generator.

    Returns:
        str: The full file path where the HTML report was saved.
    """
    # If no custom report generator is provided, default to multi-turn
    if report_generator is None:
        html_content = generate_multi_turn_html_report(results, is_chat_evaluation)
    else:
        # For single-turn or any custom generator, call it directly
        # (Some generators might not need `is_chat_evaluation`.)
        try:
            # If the generator expects two arguments
            html_content = report_generator(results, is_chat_evaluation)
        except TypeError:
            # If it only expects one argument (e.g., single-turn)
            html_content = report_generator(results)

    # Create a timestamp string for the file name (format: YYYYMMDD_HHMMSS)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"report_{timestamp}.html"

    # Define the full file path
    file_path = Path(directory) / file_name

    # Write the HTML content to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    return str(file_path)