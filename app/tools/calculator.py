"""Calculator tool for mathematical operations."""

import ast
import operator
from typing import Dict, Any
from app.tools.base import BaseTool, ToolOutput


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""
    
    name = "calculator"
    description = (
        "Perform mathematical calculations. "
        "Input should be a mathematical expression as a string. "
        "Supports basic operations: +, -, *, /, **, (), and common functions. "
        "Example: '2 + 2', '(10 * 5) / 2', '2 ** 8'"
    )
    
    # Supported operators
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def __init__(self):
        """Initialize the calculator tool."""
        super().__init__()
    
    async def execute(self, expression: str, **kwargs) -> ToolOutput:
        """
        Execute a mathematical calculation.
        
        Args:
            expression: Mathematical expression to evaluate
            **kwargs: Additional arguments (ignored)
            
        Returns:
            ToolOutput: Calculation result or error
        """
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate the expression safely
            result = self._eval_node(tree.body)
            
            return ToolOutput(
                success=True,
                result=f"The result is: {result}",
                error=None
            )
            
        except (SyntaxError, ValueError, KeyError) as e:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Invalid mathematical expression: {str(e)}"
            )
        except ZeroDivisionError:
            return ToolOutput(
                success=False,
                result=None,
                error="Division by zero error"
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Calculation failed: {str(e)}"
            )
    
    def _eval_node(self, node: ast.AST) -> float:
        """
        Safely evaluate an AST node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluation result
            
        Raises:
            ValueError: If node type is not supported
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            operand = self._eval_node(node.operand)
            return op(operand)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
