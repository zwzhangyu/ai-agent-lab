import json

from tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    """Performs arithmetic operations: add, subtract, multiply, divide, power, modulus."""

    def __init__(self):
        super().__init__()
        self.name = "calculator"
        self.description = "Performs mathematical calculations. Supports: add, subtract, multiply, divide, power, modulus."

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            return "Error: Division by zero."
        return a / b

    def power(self, a, b):
        return a ** b

    def modulus(self, a, b):
        if b == 0:
            return "Error: Modulus by zero."
        return a % b

    def run(self, query: str) -> str:
        try:
            data = json.loads(query)
            if "operation" not in data or "params" not in data:
                return "Error: Missing 'operation' or 'params' in request."

            operation = data["operation"]
            params = data["params"]

            if not isinstance(params, dict) or "a" not in params or "b" not in params:
                return "Error: Parameters must be in the format {'a': <num>, 'b': <num>}."

            if hasattr(self, operation):
                method = getattr(self, operation)
                return str(method(**params))
            else:
                return f"Error: Unknown operation '{operation}'. Available operations: add, multiply, subtract, divide, power, modulus."

        except json.JSONDecodeError:
            return "Error: Invalid JSON input."
        except Exception as e:
            return f"Error: {str(e)}"
