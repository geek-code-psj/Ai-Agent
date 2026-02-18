"""Code chain for LangServe integration."""

from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from app.agents.code_agent import CodeAgent


async def code_agent_wrapper(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper function for code agent.
    
    Args:
        input_dict: Input dictionary with 'input' key
        
    Returns:
        Dictionary with 'output' key
    """
    agent = CodeAgent()
    query = input_dict.get("input", "")
    result = await agent.run(query)
    
    return {"output": result}


def create_code_chain():
    """
    Create a LangServe-compatible code chain.
    
    Returns:
        Runnable chain for code agent
    """
    return RunnableLambda(code_agent_wrapper)
