import json

class AHAssistantResponseParser:
    @staticmethod
    def parse_response(response):
        try:
            lines = response.text.splitlines()
            tokens = []

            for line in lines:
                # We only care about lines starting with `data:` — `event:` lines can be skipped
                if line.startswith("data:"):
                    data_part = line.split("data:", 1)[1].strip()
                    if not data_part:
                        continue  # skip empty lines

                    try:
                        data = json.loads(data_part)
                        token = data.get("token", "")
                        if token:
                            tokens.append(token)
                    except json.JSONDecodeError as e:
                        print("JSON parse error:", e)
                        continue

            message = "".join(tokens).strip()
            return {"text_message": message}

        except Exception as e:
            print("Failed to parse AI message response:", e)
            return {"text": ""}
