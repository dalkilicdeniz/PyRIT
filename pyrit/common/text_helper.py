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

def generate_single_turn_html_report(results: list, threshold: float = 0.7) -> str:
    """
    Generates an HTML report for single-turn dataset evaluations where expected_output is inside each score entry.

    Args:
        results (list): A list of dictionaries, each representing a single dataset item.
                        Expected structure:
                          {
                            "conversation_id": str,
                            "prompt": str,
                            "assistant_response": str,
                            "scores": [
                                {
                                  "score_value": str or float,
                                  "score_rationale": str,
                                  "expected_output": str
                                },
                                ...
                            ]
                          }
        threshold (float): A numeric value used to determine pass/fail. Defaults to 0.7.

    Returns:
        str: A complete HTML string containing the report.
    """

    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Single-Turn Dataset Evaluation Report</title>
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500,700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Roboto', sans-serif;
      background: #f8f9fa;
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
    .description {
      text-align: center;
      margin-bottom: 20px;
      font-size: 1rem;
      color: #666;
    }
    details {
      margin-bottom: 15px;
      border: 1px solid #ddd;
      border-radius: 6px;
      background-color: #fcfcfc;
      overflow: hidden;
    }
    summary {
      padding: 12px 18px;
      cursor: pointer;
      background: #e3f2fd;
      color: #01579b;
      font-size: 1rem;
      font-weight: 500;
      border-radius: 6px;
      outline: none;
      border: none;
    }
    summary:hover { background: #bbdefb; }
    summary::-webkit-details-marker { display: none; }
    .metrics {
      background-color: #f1f8e9;
      padding: 12px 18px;
      margin: 0;
      border-bottom: 1px solid #ddd;
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
      vertical-align: top;
    }
    th {
      background-color: #0277bd;
      color: #fff;
      font-size: 0.9rem;
    }
    tr:nth-child(even) { background-color: #f9f9f9; }
    .score-pass {
      color: #1b5e20;
      background-color: #c8e6c9;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: bold;
    }
    .score-fail {
      color: #b71c1c;
      background-color: #ffcdd2;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: bold;
    }
    .explanation-block summary {
      background: #aed581;
      color: #fff;
      padding: 6px 10px;
      font-size: 0.85rem;
      cursor: pointer;
      border-radius: 4px;
      outline: none;
      display: inline-block;
    }
    .explanation-block summary:hover { background: #9ccc65; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Single-Turn Dataset Evaluation Report</h1>
"""

    for index, report in enumerate(results, start=1):
        prompt = report.get("prompt", "N/A")
        assistant_response = report.get("assistant_response", "N/A")
        scores = report.get("scores", [])

        numeric_scores = []
        for s in scores:
            raw_val = s.get("score_value", "0.0")
            try:
                numeric_scores.append(float(raw_val))
            except ValueError:
                numeric_scores.append(0.0)

        main_score = max(numeric_scores) if numeric_scores else None

        if main_score is not None:
            pass_fail_label = "Passed" if main_score >= threshold else "Failed"
            pass_fail_class = "score-pass" if main_score >= threshold else "score-fail"
            summary_text = (
                f"Test Case {index}: "
                f"<strong>User Prompt:</strong> \"{prompt[:100]}...\" | "
                f"Score: {main_score} <span class='{pass_fail_class}'>{pass_fail_label}</span>"
            )
        else:
            summary_text = (
                f"Test Case {index}: <strong>User Prompt:</strong> \"{prompt[:100]}...\""
            )

        html += f"""
    <details>
      <summary>{summary_text}</summary>
      <div class="metrics">
        <p><strong>User Prompt:</strong> {prompt}</p>
        <p><strong>Threshold:</strong> {threshold}</p>
      </div>
      <h3>Transcript</h3>
      <table>
        <thead>
          <tr>
            <th>User Prompt</th>
            <th>Assistant Response</th>
            <th>Expected Output</th>
            <th>Score(s)</th>
          </tr>
        </thead>
        <tbody>
"""

        if scores:
            for s in scores:
                raw_val = s.get("score_value", "0.0")
                expected_output = s.get("expected_output", "N/A")
                try:
                    score_val = float(raw_val)
                except ValueError:
                    score_val = 0.0

                pass_fail_span_class = "score-pass" if score_val >= threshold else "score-fail"
                pass_fail_text = "Pass" if score_val >= threshold else "Fail"

                rationale = s.get("score_rationale", "No rationale provided")

                html += f"""
          <tr>
            <td>{prompt}</td>
            <td>{assistant_response}</td>
            <td>{expected_output}</td>
            <td>
              <ul>
                <li>
                  <strong>{score_val}</strong>
                  <span class='{pass_fail_span_class}'>{pass_fail_text}</span>
                  <details class='explanation-block'><summary>View Explanation</summary>
                    <div>{rationale}</div>
                  </details>
                </li>
              </ul>
            </td>
          </tr>
"""

        else:
            html += f"""
          <tr>
            <td>{prompt}</td>
            <td>{assistant_response}</td>
            <td>N/A</td>
            <td>N/A</td>
          </tr>
"""

        html += """
        </tbody>
      </table>
    </details>
"""

    html += "</div></body></html>"
    return html

def format_execution_time(seconds: float) -> str:
    """
    Convert a duration in seconds to a string formatted as hours, minutes, and seconds.
    """
    seconds = int(round(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours} hours, {minutes} minutes, {secs} seconds"
    elif minutes > 0:
        return f"{minutes} minutes, {secs} seconds"
    else:
        return f"{secs} seconds"

def save_html_report(
        results: list,
        directory: str = ".",
        report_generator=None,
        is_chat_evaluation: bool = True,
        threshold: float = 0.7,
        file_name: str = "report",
        description: str = "",
        execution_time: float = 0.0  # Test execution time provided as a parameter (in seconds)
) -> str:
    """
    Saves an HTML report generated by the specified report generator function.

    Args:
        results (list): A list of report dictionaries.
        directory (str): Directory to save the report.
        report_generator (callable): Function that generates the HTML report.
        is_chat_evaluation (bool): Whether it's a multi-turn chat evaluation.
        threshold (float): Score threshold to determine pass/fail.
        description (str): Optional description to display in the report.
        execution_time (float): Test execution time in seconds.

    Returns:
        str: Path to the saved HTML report.
    """

    # Generate the report content
    if report_generator is None:
        html_content = generate_multi_turn_html_report(results, is_chat_evaluation)
    else:
        if report_generator.__name__ == "generate_single_turn_html_report":
            html_content = report_generator(results, threshold=threshold)
        else:
            html_content = report_generator(results, is_chat_evaluation)

    # Insert description under the title if provided
    if description:
        html_content = html_content.replace(
            "<h1>Single-Turn Dataset Evaluation Report</h1>",
            f"<h1>Single-Turn Dataset Evaluation Report</h1>\n<p class='description'>{description}</p>"
        )
        html_content = html_content.replace(
            "<h1>Multi-turn Chat Report</h1>",
            f"<h1>Multi-turn Chat Report</h1>\n<p class='description'>{description}</p>"
        )

    ### Pass/Fail Distribution Calculation ###
    total_cases = 0
    passed_cases = 0

    for report in results:
        numeric_scores = []

        if is_chat_evaluation:
            # Multi-turn evaluation - loop through transcript & collect scores
            transcript = report.get("transcript", [])
            for turn in transcript:
                pieces = turn.get("pieces", [])
                for piece in pieces:
                    scores = piece.get("scores", [])
                    for s in scores:
                        raw_val = s.get("score", "0.0")
                        try:
                            numeric_scores.append(float(raw_val))
                        except ValueError:
                            numeric_scores.append(0.0)
        else:
            # Single-turn evaluation - use top-level scores
            scores = report.get("scores", [])
            for s in scores:
                raw_val = s.get("score_value", "0.0")
                try:
                    numeric_scores.append(float(raw_val))
                except ValueError:
                    numeric_scores.append(0.0)

        # Pass/Fail logic
        if numeric_scores:
            main_score = max(numeric_scores)
            total_cases += 1
            if main_score >= threshold:
                passed_cases += 1

    failed_cases = total_cases - passed_cases

    # Overview Text (insert into report)
    overview_text = (
        f"<p class='overview'>Total Test Cases: {total_cases} | "
        f"Passed: {passed_cases} | Failed: {failed_cases}</p>"
    )

    ### Execution Time ###
    def format_execution_time(seconds: float) -> str:
        seconds = int(round(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours} hours, {minutes} minutes, {secs} seconds"
        elif minutes > 0:
            return f"{minutes} minutes, {secs} seconds"
        else:
            return f"{secs} seconds"

    formatted_execution_time = format_execution_time(execution_time)
    execution_text = f"<p class='execution-time'>Test Execution Time: {formatted_execution_time}</p>"

    # Insert Overview + Execution Time under the title
    if is_chat_evaluation:
        html_content = html_content.replace(
            "</h1>", f"</h1>\n{overview_text}\n{execution_text}", 1
        )
    else:
        html_content = html_content.replace(
            "</h1>", f"</h1>\n{overview_text}\n{execution_text}", 1
        )

    ### Save HTML file ###
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{file_name}_{timestamp}.html"
    file_path = Path(directory) / file_name

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"\033[92m\n✅ Report saved at: {file_path}\033[0m")
    return str(file_path)




