from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from app.agents.base_agent import BaseAgent
from app.agents.research_agent import ResearchAgent
from app.agents.code_agent import CodeAgent
from app.memory.conversation_buffer import ConversationBufferMemory


class MultiAgentOrchestrator:
    """
    Orchestrator for coordinating multiple specialized agents.
    
    This orchestrator:
    - Analyzes incoming queries
    - Routes tasks to appropriate specialist agents
    - Combines results from multiple agents
    - Provides unified responses
    """
    
    def __init__(
        self,
        memory: Optional[ConversationBufferMemory] = None,
    ):
        """
        Initialize the multi-agent orchestrator.
        
        Args:
            memory: Shared conversation memory
        """
        self.memory = memory or ConversationBufferMemory(
            max_messages=settings.conversation_memory_size
        )
        
        # Initialize specialized agents
        self.agents: Dict[str, BaseAgent] = {
            "research": ResearchAgent(memory=self.memory),
            "code": CodeAgent(memory=self.memory),
        }
        
        # LLM for routing decisions
        if settings.llm_provider == "gemini":
            self.router_llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=0.1,
                google_api_key=settings.google_api_key,
                convert_system_message_to_human=True,
            )
        else:
            self.router_llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.1,
                openai_api_key=settings.openai_api_key,
            )
    
    async def run(self, query: str) -> str:
        """
        Process a query by routing to appropriate agent(s).
        
        Args:
            query: User query
            
        Returns:
            Combined response from agent(s)
        """
        # Add query to memory
        self.memory.add_message("user", query)
        
        # Determine which agent(s) to use
        routing_decision = await self._route_query(query)
        
        # Execute with selected agent(s)
        if routing_decision["type"] == "single":
            agent_name = routing_decision["agent"]
            response = await self.agents[agent_name].run(query)
            return response
        
        elif routing_decision["type"] == "multi":
            # Execute with multiple agents and combine results
            responses = {}
            for agent_name in routing_decision["agents"]:
                agent_response = await self.agents[agent_name].run(query)
                responses[agent_name] = agent_response
            
            # Synthesize responses
            final_response = await self._synthesize_responses(query, responses)
            return final_response
        
        else:
            # Fallback to research agent
            return await self.agents["research"].run(query)
    
    async def _route_query(self, query: str) -> Dict[str, Any]:
        """
        Determine which agent(s) should handle the query.
        
        Args:
            query: User query
            
        Returns:
            Routing decision dictionary
        """
        routing_prompt = f"""Analyze this query and determine which specialist agent should handle it:

Query: "{query}"

Available agents:
- research: For web searches, factual questions, current events, general knowledge
- code: For programming tasks, code execution, algorithmic problems, data analysis

Respond with ONLY ONE of these formats:
SINGLE: agent_name
MULTI: agent1, agent2

Examples:
"What is the capital of France?" -> SINGLE: research
"Write a Python function to calculate fibonacci" -> SINGLE: code
"Search for recent AI papers and analyze their complexity" -> MULTI: research, code
"""
        
        messages = [SystemMessage(content=routing_prompt)]
        response = await self.router_llm.ainvoke(messages)
        decision_text = response.content.strip()
        
        # Parse response
        if decision_text.startswith("SINGLE:"):
            agent_name = decision_text.replace("SINGLE:", "").strip()
            return {"type": "single", "agent": agent_name}
        
        elif decision_text.startswith("MULTI:"):
            agents_text = decision_text.replace("MULTI:", "").strip()
            agent_names = [a.strip() for a in agents_text.split(",")]
            return {"type": "multi", "agents": agent_names}
        
        else:
            # Default to research
            return {"type": "single", "agent": "research"}
    
    async def _synthesize_responses(
        self, 
        query: str, 
        responses: Dict[str, str]
    ) -> str:
        """
        Synthesize responses from multiple agents.
        
        Args:
            query: Original query
            responses: Dictionary of agent responses
            
        Returns:
            Synthesized response
        """
        synthesis_prompt = f"""Synthesize these responses from different specialist agents into a cohesive answer:

Original Query: "{query}"

"""
        for agent_name, response in responses.items():
            synthesis_prompt += f"\n{agent_name.upper()} Agent Response:\n{response}\n"
        
        synthesis_prompt += "\nProvide a unified, coherent response that combines the best insights from each agent:"
        
        messages = [SystemMessage(content=synthesis_prompt)]
        response = await self.router_llm.ainvoke(messages)
        
        synthesized = response.content
        self.memory.add_message("assistant", synthesized)
        
        return synthesized
