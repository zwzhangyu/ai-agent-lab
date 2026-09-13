"""计算工具（与原示例一致）。

用于让 Agent 做预算相关的数学运算。使用 ast 白名单解析，
只允许基本四则运算，避免 eval 带来的安全风险。
"""

import ast
import operator
import re

from crewai.tools import tool


class CalculatorTools:

    @tool("进行数学计算")
    def calculate(operation):
        """用于执行数学计算，如加、减、乘、除等。
        输入应为一个数学表达式，例如 `200*7` 或 `5000/2*10`。
        """
        try:
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }

            if not re.match(r"^[0-9+\-*/().% ]+$", operation):
                return "错误：数学表达式中包含非法字符"

            tree = ast.parse(operation, mode="eval")

            def _eval_node(node):
                if isinstance(node, ast.Expression):
                    return _eval_node(node.body)
                elif isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    op = allowed_operators.get(type(node.op))
                    if op is None:
                        raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
                    return op(left, right)
                elif isinstance(node, ast.UnaryOp):
                    operand = _eval_node(node.operand)
                    op = allowed_operators.get(type(node.op))
                    if op is None:
                        raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
                    return op(operand)
                else:
                    raise ValueError(f"不支持的节点类型: {type(node).__name__}")

            return _eval_node(tree)

        except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as exc:
            return f"错误：{exc}"
        except Exception:
            return "错误：无效的数学表达式"
