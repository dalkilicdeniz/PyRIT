# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Dict, Union
from pathlib import Path

def read_txt(file) -> List[Dict[str, str]]:
    return [{"prompt": line.strip()} for line in file.readlines()]

def write_txt(file, examples: List[Dict[str, str]]):
    file.write("\n".join([ex["prompt"] for ex in examples]))

def sanitize(text: str) -> str:
    return str(text).replace("<", "&lt;").replace(">", "&gt;")

def format_execution_time(seconds: float) -> str:
    seconds = int(round(seconds))
    mins, secs = divmod(seconds, 60)
    return f"{mins}m {secs}s" if mins else f"{secs}s"


def _render_report_html(
        title: str,
        description: str,
        results: list,
        threshold: float,
        execution_time: float,
        is_chat_eval: bool,
        strict_step_failures: bool
) -> str:
    passed_cases = 0
    total_cases = len(results)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
    .container {{ background: #fff; padding: 30px; border-radius: 10px; max-width: 1100px; margin: auto; }}
    h1 {{ text-align: center; color: #2c3e50; }}
    .summary {{ font-size: 1rem; text-align: center; color: #444; margin-bottom: 30px; }}
    details {{ border: 1px solid #ccc; border-radius: 6px; background: #eaf4fe; margin-bottom: 15px; }}
    summary {{ padding: 12px; font-weight: bold; cursor: pointer; color: #01579b; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #eee; vertical-align: top; }}
    th {{ background: #0277bd; color: #fff; }}
    .score-pass {{ color: green; font-weight: bold; }}
    .score-fail {{ color: red; font-weight: bold; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 5px; font-weight: bold; }}
    .badge.pass {{ background: #c8e6c9; color: #1b5e20; }}
    .badge.fail {{ background: #ffcdd2; color: #b71c1c; }}
    .explanation {{ font-size: 0.9rem; margin-top: 6px; color: #555; }}
  </style>
</head>
<body>
<div class='container'>
  <h1>{title}</h1>
  <p class='overview'>{description}</p>
  <div class='summary'>
    Total Test Cases: {total_cases} |
    Passed: {{passed}} |
    Failed: {{failed}} |
    Execution Time: {format_execution_time(execution_time)}
  </div>
"""

    for idx, result in enumerate(results, start=1):
        transcript = []
        turns = 1
        final_score = 0.0

        # Use explicit objective, or fallback to prompt or first user message
        objective = sanitize(result.get("objective", result.get("prompt", "N/A")))
        if "conversation" in result and not result.get("objective"):
            first_user_msg = next((m.get("message", "") for m in result["conversation"] if m.get("role") == "user"), "")
            if first_user_msg:
                objective = sanitize(first_user_msg)

        if is_chat_eval:
            transcript = result.get("transcript", [])
            if not transcript and "conversation" in result:
                conv = result["conversation"]
                for i in range(0, len(conv), 2):
                    turn = {"turn_index": (i // 2) + 1, "pieces": []}
                    if i < len(conv):
                        turn["pieces"].append({
                            "role": conv[i].get("role", ""),
                            "converted_value": conv[i].get("message", ""),
                            "scores": conv[i].get("scores", [])
                        })
                    if i + 1 < len(conv):
                        turn["pieces"].append({
                            "role": conv[i + 1].get("role", ""),
                            "converted_value": conv[i + 1].get("message", ""),
                            "scores": conv[i + 1].get("scores", [])
                        })
                    transcript.append(turn)

            turns = result.get("aggregated_metrics", {}).get("total_turns", len(transcript))
            final_score = result.get("aggregated_metrics", {}).get("final_score", 0.0)

            score_values = []
            for turn in transcript:
                for piece in turn["pieces"]:
                    for score in piece.get("scores", []):
                        try:
                            score_values.append(float(score.get("score", score.get("score_value", 0.0))))
                        except:
                            continue

            if strict_step_failures:
                passed = all(s >= threshold for s in score_values)
            else:
                try:
                    passed = float(final_score) >= threshold
                except:
                    passed = False

        else:
            if "conversation" in result:
                conv = result["conversation"]
                transcript = []
                for i in range(0, len(conv), 2):
                    turn = {"turn_index": (i // 2) + 1, "pieces": []}
                    if i < len(conv):
                        turn["pieces"].append({
                            "role": conv[i].get("role", ""),
                            "converted_value": conv[i].get("message", ""),
                            "scores": conv[i].get("scores", [])
                        })
                    if i + 1 < len(conv):
                        turn["pieces"].append({
                            "role": conv[i + 1].get("role", ""),
                            "converted_value": conv[i + 1].get("message", ""),
                            "scores": conv[i + 1].get("scores", [])
                        })
                    transcript.append(turn)
                turns = len(transcript)
            else:
                transcript = [{
                    "turn_index": 1,
                    "pieces": [
                        {"role": "user", "converted_value": result.get("prompt", "")},
                        {
                            "role": "assistant",
                            "converted_value": result.get("assistant_response", ""),
                            "scores": result.get("scores", [])
                        }
                    ]
                }]
                turns = 1

            score_values = []
            for turn in transcript:
                for piece in turn["pieces"]:
                    for score in piece.get("scores", []):
                        try:
                            score_values.append(float(score.get("score", score.get("score_value", 0.0))))
                        except:
                            continue

            final_score = min(score_values, default=0.0)
            passed = all(s >= threshold for s in score_values) if strict_step_failures else final_score >= threshold

        if passed:
            passed_cases += 1

        badge = "pass" if passed else "fail"
        label = "Pass" if passed else "Fail"

        html += f"""
<details>
  <summary>Test Case {idx}: <strong>Objective:</strong> {objective} |
  <strong>Achieved:</strong> <span class='badge {badge}'>{label}</span> |
  <strong>Turns:</strong> {turns} |
  <strong>Final Score:</strong> {float(final_score):.2f}</summary>
  <table>
    <thead><tr><th>User</th><th>Assistant</th><th>Cumulative Score</th></tr></thead>
    <tbody>
"""

        for turn in transcript:
            user_piece = next((p for p in turn["pieces"] if p["role"] == "user"), {"converted_value": ""})
            assistant_piece = next((p for p in turn["pieces"] if p["role"] == "assistant"), {"converted_value": "", "scores": []})

            user_text = sanitize(user_piece["converted_value"])
            assistant_text = sanitize(assistant_piece["converted_value"])

            scores_html = ""
            for score in assistant_piece.get("scores", []):
                try:
                    val = float(score.get("score", score.get("score_value", 0.0)))
                    rationale = sanitize(score.get("rationale", score.get("score_rationale", "")))
                    cls = "score-pass" if val >= threshold else "score-fail"
                    scores_html += f"<div><strong class='{cls}'>{val:.2f}</strong><div class='explanation'>{rationale}</div></div>"
                except:
                    continue

            html += f"<tr><td>{user_text}</td><td>{assistant_text}</td><td>{scores_html}</td></tr>"

        html += "</tbody></table></details>"

    html = html.replace("{passed}", str(passed_cases))
    html = html.replace("{failed}", str(total_cases - passed_cases))
    html += "</div></body></html>"
    return html


def generate_simulation_report(
        results: list,
        threshold: float = 0.9,
        title: str = "Comprehensive Simulation Report",
        description: str = "",
        execution_time: float = 0.0,
        save_path: Union[str, Path] = "simulation_report.html"
):
    html = _render_report_html(
        title=title,
        description=description,
        results=results,
        threshold=threshold,
        execution_time=execution_time,
        is_chat_eval=True,
        strict_step_failures=False
    )
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Simulation report saved to: {save_path}")


def generate_dataset_report(
        results: list,
        threshold: float = 0.7,
        title: str = "Comprehensive Dataset Report",
        description: str = "",
        execution_time: float = 0.0,
        save_path: Union[str, Path] = "dataset_report.html"
):
    html = _render_report_html(
        title=title,
        description=description,
        results=results,
        threshold=threshold,
        execution_time=execution_time,
        is_chat_eval=False,
        strict_step_failures=True
    )
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Dataset report saved to: {save_path}")
