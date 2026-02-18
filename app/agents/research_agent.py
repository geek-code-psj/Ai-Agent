"""Research agent specialized for web search and summarization."""

from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.tools.base import BaseTool
from app.tools.web_search import WebSearchTool
from app.tools.calculator import CalculatorTool
from app.memory.conversation_buffer import ConversationBufferMemory


class ResearchAgent(BaseAgent):
    """
    Research agent specialized in web search and information synthesis.
    
    This agent excels at:
    - Finding information from web searches
    - Synthesizing multiple sources
    - Providing well-sourced answers
    - Fact-checking and verification
    """
    
    def __init__(
        self,
        memory: Optional[ConversationBufferMemory] = None,
        additional_tools: Optional[List[BaseTool]] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize the research agent.
        
        Args:
            memory: Conversation memory
            additional_tools: Additional tools beyond default research tools
            max_iterations: Maximum reasoning iterations
        """
        # Set up default research tools
        tools = [
            WebSearchTool(max_results=5),
            CalculatorTool(),
        ]
        
        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)
        
        super().__init__(
            name="ResearchAgent",
            description=(
                "a research specialist that can search the web, "
                "find relevant information, and synthesize answers from multiple sources"
            ),
            tools=tools,
            memory=memory,
            max_iterations=max_iterations,
            temperature=0.3,  # Lower temperature for more factual responses
        )
    
    def _build_system_prompt(self) -> str:
        """
        Build specialized system prompt for research agent.
        
        Returns:
            System prompt string
        """
        base_prompt = super()._build_system_prompt()
        
        research_instructions = """

RESEARCH GUIDELINES:
- Always search for current information when asked about recent events
- Cite sources in your final answer when possible
- Cross-reference multiple sources for accuracy
- Be clear about uncertainty or conflicting information
- Provide comprehensive answers with relevant details
"""
        
        return base_prompt + research_instructions
