from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract base class for all chatbot tools."""

    def get_tool_definition(self) -> Dict:
        """Returns the tool definition for OpenAI.
        Subclasses should override the 'parameters' part.
        """
        return {
            "type": "function",
            "function": {
                "name": self._get_tool_name(),
                "description": self.__doc__ or "No description provided.",
                "parameters": self._get_tool_parameters(),
            },
        }

    def _get_tool_name(self) -> str:
        """Returns the name of the tool. Defaults to snake_case of the class name."""
        name = self.__class__.__name__.replace("Tool", "")
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip(
            "_"
        )

    @abstractmethod
    def _get_tool_parameters(self) -> Dict:
        """Returns the parameter schema for the tool.
        Subclasses MUST implement this method.
        """
        pass

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Any:
        """Executes the tool's functionality.
        Subclasses MUST implement this method.
        """
        pass
