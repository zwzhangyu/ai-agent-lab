from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all ReAct agent tools.

    Each tool must implement:
    - A unique name used for lookup
    - A description to help understand what the tool does
    - A run() method that takes a string input and returns a string result
    """

    def __init__(self):
        self.name = ""
        self.description = ""

    @abstractmethod
    def run(self, query: str) -> str:
        """Execute the tool with the given query and return the result."""
        raise NotImplementedError("Each tool must implement its own run() method.")


class BaseTool(ABC):

    def __int__(self):
        self.name = ""
        self.description = ""

    def run(self, query: str) ->str:
        raise NotImplementedError("")



