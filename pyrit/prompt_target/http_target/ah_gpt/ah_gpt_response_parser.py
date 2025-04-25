import json

class AHGPTResponseParser:
    @staticmethod
    def parse_response(response):
        try:
            # Parse the JSON string directly
            data = json.loads(response.text)
            messages = data.get("messages", [])

            # Find the last assistant message
            for message in reversed(messages):
                if message.get("role") == "assistant":
                    return {"text_message": message.get("content", "").strip()}

            return {"text_message": ""}  # Fallback if no assistant message is found

        except Exception as e:
            print("Failed to parse AI message response:", e)
            return {"text_message": ""}
