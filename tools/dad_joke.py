import json
from typing import Any, Dict

import requests

from tools.base_tool import BaseTool


class DadJokeTool(BaseTool):
    """Tells a random dad joke fetched from icanhazdadjoke.com."""

    def _get_tool_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __call__(self, **kwargs: Any) -> str:
        try:
            headers = {"Accept": "application/json"}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            joke_data = response.json()
            return joke_data.get(
                "joke", "Sorry, I couldn't fetch a dad joke right now."
            )
        except requests.exceptions.RequestException as e:
            return f"Error fetching dad joke: {e}"
        except json.JSONDecodeError:
            return "Error decoding dad joke response."


if __name__ == "__main__":
    tool = DadJokeTool()
    print(tool())
    print(tool.get_tool_definition())
