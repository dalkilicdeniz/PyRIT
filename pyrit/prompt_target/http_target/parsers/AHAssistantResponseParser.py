import json

class AHAssistantResponseParser:
    @staticmethod
    def parse_response(response):
        """Parses the assistant's response content and extracts structured data."""
        response_data = {"ai_message": ""}
        response_text = response.content.decode("utf-8")

        # Split the response text by newlines to process each line
        lines = response_text.splitlines()
        tokens = []

        for line in lines:
            if line.startswith("event:AI_MESSAGE"):
                # Extract the JSON part of the line
                json_part = line.split("data:", 1)[1]
                try:
                    data = json.loads(json_part)
                    tokens.append(data.get("token", ""))
                except json.JSONDecodeError:
                    continue

        # Combine all AI message tokens
        response_data["ai_message"] = "".join(tokens)

        return response_data