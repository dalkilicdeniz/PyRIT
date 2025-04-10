# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 🚀 Automated QA Testing for Steijn Assistant using PyRIT
#
# ## 📌 Overview
# This notebook automates **QA testing** for the **Steijn Assistant** using the **PyRIT** framework. It sends predefined prompts to the assistant, evaluates its responses, and generates a report.
#
# ## 🛠️ Steps in this Notebook
# - **🔧 Setup Configuration** - Define API endpoints, authentication, and request templates.
# - **📋 Load QA Dataset** - Define test questions and expected answers.
# - **⚙️ Initialize PyRIT** - Configure the testing environment.
# - **📡 Send Prompts & Evaluate Responses** - Run the main test loop.
# - **📊 Generate Report** - Save the results for analysis.
#
# ## 📝 How to Use This Notebook
# 1. **▶️ Run each cell in order** from top to bottom.
# 2. **✏️ Modify the `qa_pairs` list** to test different questions and expected outcomes.
# 3. **📂 Inspect the HTML report** at the end for detailed evaluation results.
#

# %%
import uuid
import asyncio  # Needed for asynchronous operations
from pathlib import Path
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# PyRIT Imports
from pyrit.common import IN_MEMORY, initialize_pyrit
from pyrit.prompt_target import OpenAIChatTarget, SteijnHTTPTarget
from pyrit.score.evaluator import Evaluator
from pyrit.orchestrator import SteijnPromptSendingOrchestrator
from pyrit.common.text_helper import generate_dataset_report
from pyrit.prompt_target import SteijnResponseParser


# %%
# Use an in-memory database for a clean testing environment
initialize_pyrit(memory_db_type=IN_MEMORY)


# %%
# Load environment variables
load_dotenv()

# Define Member ID and API credentials
member_id = os.getenv("STEIJN_NONPRD_MEMBER_ID")
url = os.getenv("STEIJN_ENDPOINT").rstrip("/") + "/" + member_id
token = os.getenv("STEIJN_NONPRD_TOKEN")

# Define a raw HTTP POST request template with headers and a placeholder for the prompt
start_chat_request_raw = f"""
    POST {url}
    Content-Type: application/json
    X-Authorization: {token}
    Accept: text/event-stream
    x-rate-limiter-enabled: false
    x-message-length-validation-enabled: false
    x-user-message-evaluator-enabled: false

{{
    "data": "{{PROMPT}}"
}}
"""

# %%
from pyrit.loaders.test_data_loader import load_test_data

# === Dataset Configuration ===
DATASET_PATH = "tests/data/dataset"
available_datasets = {
    "general": "qa_general_dataset.yaml",
    "products": "qa_products_dataset.yaml",
    "non_food": "qa_non_food_products_dataset.yaml",
    "recipes": "qa_recipes_dataset.yaml",
    "health": "qa_health_dataset.yaml",
    "conversational": "qa_conversational_dataset.yaml",
    "regression": "qa_regression_dataset.yaml"
}

# === Evaluator Configuration ===
available_evaluators = {
    "general": "assets/AH_Evaluators/ah_assistant/qa_general.yaml",
    "products": "assets/AH_Evaluators/ah_assistant/qa_products.yaml",
    "recipes": "assets/AH_Evaluators/ah_assistant/qa_recipes.yaml",
    "relevance": "assets/AH_Evaluators/relevance_evaluator.yaml",
}

# Select which dataset and evaluator you want to test
selected_dataset = "regression"
selected_evaluator = "general"

# Load the dataset
current_dataset = available_datasets[selected_dataset]
qa_pairs = load_test_data(f"{DATASET_PATH}/{current_dataset}")

# Set evaluator path
evaluator_path = available_evaluators[selected_evaluator]

# Preview laodeded data
print(f"Dataset: {selected_dataset} → {len(qa_pairs)} cases loaded")
print(f"Evaluator: {selected_evaluator}")

# %%
# Create an HTTP target that sends prompts using the defined request template.
http_prompt_target = SteijnHTTPTarget(
    http_request=start_chat_request_raw,
    prompt_regex_string="{PROMPT}",
    timeout=60.0,
    callback_function=SteijnResponseParser.parse_response
)

# Create an evaluator that uses a YAML configuration for scoring suggestions.
scorer = Evaluator(
    chat_target=OpenAIChatTarget(),
    evaluator_yaml_path=Path(evaluator_path),
    scorer_type="float_scale"
)

# Create the orchestrator for sending prompts and evaluating responses.
orchestrator = SteijnPromptSendingOrchestrator(
    objective_target=http_prompt_target,
    scorers=[scorer],
    batch_size=4
)


# %%
async def generate_report(results, execution_time):
    # Define the report directory path and create it if it doesn't exist.
    report_dir = Path("tests/E2E/reports/DataSet").resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    # Create a timestamp string
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Construct the filename with timestamp after the extension
    filename = f"{selected_dataset}_dataset_report_{timestamp}.html"
    
    generate_dataset_report(
        results=results,
        save_path=report_dir / filename,
        description="Mixed evaluation of single-turn and multi-turn prompt responses.",
        execution_time=execution_time,
    )



# %%
async def main():
    # Start the timer before sending prompts.
    start_time = time.time()
    
    # Send the list of prompts asynchronously.
    await orchestrator.send_qa_pairs_async(qa_pairs)  
    
    results = orchestrator.get_all_chat_results()  # Or use your combined method.

    # Calculate the total execution time.
    execution_time = time.time() - start_time
    
    await generate_report(results, execution_time)


# %%
await main()


# %%
