"""Code agent specialized for Python code execution and analysis."""

from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.tools.base import BaseTool
from app.tools.python_executor import PythonExecutorTool
from app.tools.calculator import CalculatorTool
from app.memory.conversation_buffer import ConversationBufferMemory


class CodeAgent(BaseAgent):
    """
    Code agent specialized in Python code execution and problem-solving.
    
    This agent excels at:
    - Writing and executing Python code
    - Solving algorithmic problems
    - Data processing and analysis
    - Mathematical computations
    """
    
    def __init__(
        self,
        memory: Optional[ConversationBufferMemory] = None,
        additional_tools: Optional[List[BaseTool]] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize the code agent.
        
        Args:
            memory: Conversation memory
            additional_tools: Additional tools beyond default code tools
            max_iterations: Maximum reasoning iterations
        """
        # Set up default code tools
        tools = [
            PythonExecutorTool(timeout=30),
            CalculatorTool(),
        ]
        
        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)
        
        super().__init__(
            name="CodeAgent",
            description=(
                "a coding specialist that can write and execute Python code, "
                "solve algorithmic problems, and perform data analysis"
            ),
            tools=tools,
            memory=memory,
            max_iterations=max_iterations,
            temperature=0.2,  # Lower temperature for more precise code
        )
    
    def _build_system_prompt(self) -> str:
        """
        Build specialized system prompt for code agent.
        
        Returns:
            System prompt string
        """
        base_prompt = super()._build_system_prompt()
        
        code_instructions = """

CODING GUIDELINES:
- Write clean, well-commented Python code
- Test your code with the python_executor tool before providing final answers
- Handle edge cases and errors gracefully
- Use the calculator tool for simple math, python_executor for complex computations
- Explain your code and results clearly
- Follow Python best practices and PEP 8 style guidelines
"""
        
        return base_prompt + code_instructions
