"""Research chain for LangServe integration."""

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from app.agents.research_agent import ResearchAgent


async def research_agent_wrapper(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper function for research agent.
    
    Args:
        input_dict: Input dictionary with 'input' key
        
    Returns:
        Dictionary with 'output' key
    """
    agent = ResearchAgent()
    query = input_dict.get("input", "")
    result = await agent.run(query)
    
    return {"output": result}


def create_research_chain():
    """
    Create a LangServe-compatible research chain.
    
    Returns:
        Runnable chain for research agent
    """
    return RunnableLambda(research_agent_wrapper)
