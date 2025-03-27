import re
import json

class SteijnResponseParser:
    response_fields_regex_dict = [
        {"name": "text_message", "pattern": r"event:TEXT_MESSAGE\s+data:(.*?)(?:\n|$)"},
        {"name": "data_message", "pattern": r"event:DATA_MESSAGE\s+data:(\{.*?\})"},
        {"name": "suggestion_pills", "pattern": r"event:SUGGESTION_CHIPS\s+data:(\{.*?\})"}
    ]

    @staticmethod
    def parse_response(response):
        """Parses the assistant's response content and extracts structured data."""
        response_data = {}
        response_text = response.content.decode("utf-8")

        for field in SteijnResponseParser.response_fields_regex_dict:
            matches = re.findall(field["pattern"], response_text, re.DOTALL)

            if matches:
                if field["name"] == "text_message":
                    # Combine all text messages, clean up whitespace
                    content = "".join(matches)
                else:
                    content = matches[-1].strip()  # Get the latest non-empty match

                    # Try to parse JSON if applicable
                    if "{" in content and "}" in content:
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            pass  # Keep as a string if JSON parsing fails

                response_data[field["name"]] = content

        return response_data
