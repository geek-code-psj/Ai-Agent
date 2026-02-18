"""Python code executor tool with sandboxing."""

import sys
import io
import asyncio
from typing import Dict, Any
from RestrictedPython import compile_restricted, safe_globals
from app.tools.base import BaseTool, ToolOutput


class PythonExecutorTool(BaseTool):
    """Tool for executing Python code in a restricted environment."""
    
    name = "python_executor"
    description = (
        "Execute Python code safely. "
        "Input should be valid Python code as a string. "
        "The code runs in a sandboxed environment with restricted imports. "
        "Returns the output of the code execution or an error message. "
        "Useful for calculations, data processing, and simple algorithms."
    )
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the Python executor tool.
        
        Args:
            timeout: Maximum execution time in seconds
        """
        super().__init__()
        self.timeout = timeout
    
    async def execute(self, code: str, **kwargs) -> ToolOutput:
        """
        Execute Python code in a sandboxed environment.
        
        Args:
            code: Python code to execute
            **kwargs: Additional arguments (ignored)
            
        Returns:
            ToolOutput: Execution output or error
        """
        try:
            # Compile the code with RestrictedPython
            byte_code = compile_restricted(
                code,
                filename='<inline>',
                mode='exec'
            )
            
            # Check for compilation errors
            if byte_code is None:
                return ToolOutput(
                    success=False,
                    result=None,
                    error="Code compilation failed. Check syntax."
                )
            
            # Set up safe execution environment
            safe_globals_dict = self._get_safe_globals()
            
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                # Execute with timeout
                await asyncio.wait_for(
                    self._execute_code(byte_code, safe_globals_dict),
                    timeout=self.timeout
                )
                
                # Get the output
                output = captured_output.getvalue()
                
                return ToolOutput(
                    success=True,
                    result=output if output else "Code executed successfully (no output)",
                    error=None
                )
                
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
        except asyncio.TimeoutError:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Code execution timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Execution error: {str(e)}"
            )
    
    async def _execute_code(self, byte_code, globals_dict: Dict[str, Any]) -> None:
        """
        Execute compiled byte code.
        
        Args:
            byte_code: Compiled restricted Python code
            globals_dict: Global variables dictionary
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, exec, byte_code, globals_dict)
    
    def _get_safe_globals(self) -> Dict[str, Any]:
        """
        Get safe global variables for code execution.
        
        Returns:
            Dictionary of safe global variables
        """
        # Start with RestrictedPython's safe globals
        safe_dict = safe_globals.copy()
        
        # Add safe built-in functions
        safe_dict.update({
            'print': print,
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'any': any,
            'all': all,
        })
        
        # Add safe modules (math, json, etc.)
        import math
        import json
        safe_dict['math'] = math
        safe_dict['json'] = json
        
        return safe_dict
