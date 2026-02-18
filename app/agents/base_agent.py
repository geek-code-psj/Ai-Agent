from typing import List, Optional, Dict, Any, Union
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.core.config import settings
from app.tools.base import BaseTool, ToolRegistry, ToolOutput
from app.memory.conversation_buffer import ConversationBufferMemory


class BaseAgent:
    """
    Base agent implementing ReAct (Reasoning + Acting) architecture.
    
    The agent follows a loop:
    1. Thought: Reason about the current state and what to do next
    2. Action: Execute a tool or provide final answer
    3. Observation: Observe the result
    4. Repeat until task completion
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[ConversationBufferMemory] = None,
        max_iterations: int = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name
            description: Agent description
            tools: List of tools available to the agent
            memory: Conversation memory
            max_iterations: Maximum reasoning iterations
            temperature: LLM temperature
        """
        self.name = name
        self.description = description
        self.max_iterations = max_iterations or settings.max_iterations
        
        # Initialize LLM based on provider
        self.llm = self._create_llm(temperature)
        
        # Set up tools
        self.tool_registry = ToolRegistry()
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)
        
        # Set up memory
        self.memory = memory or ConversationBufferMemory(
            max_messages=settings.conversation_memory_size
        )
        
        # System prompt for ReAct
        self.system_prompt = self._build_system_prompt()

    def _create_llm(self, temperature: float) -> Union[ChatOpenAI, ChatGoogleGenerativeAI]:
        """Create LLM instance based on configuration."""
        if settings.llm_provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=temperature,
                google_api_key=settings.google_api_key,
                convert_system_message_to_human=True, # Gemini quirk handling
            )
        else:
            return ChatOpenAI(
                model=settings.openai_model,
                temperature=temperature,
                openai_api_key=settings.openai_api_key,
            )
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the agent.
        
        Returns:
            System prompt string
        """
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tool_registry.list_tools()
        ])
        
        prompt = f"""You are {self.name}, {self.description}

You have access to the following tools:
{tool_descriptions}

Use the ReAct format to reason and act:

Thought: Think about what to do next
Action: tool_name(argument)
Observation: [Tool execution result will be provided]

Continue this loop until you can provide a Final Answer.

When you have enough information, provide:
Final Answer: [Your complete response]

IMPORTANT:
- Always start with a Thought
- Use Action: tool_name(argument) format exactly
- Wait for Observation before next Thought
- Only provide Final Answer when you're confident
- Be concise in your thoughts
"""
        return prompt
    
    async def run(self, query: str) -> str:
        """
        Run the agent with a query using ReAct loop.
        
        Args:
            query: User query
            
        Returns:
            Agent's final response
        """
        # Add user query to memory
        self.memory.add_message("user", query)
        
        # Initialize conversation with system prompt
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=query)
        ]
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            agent_response = response.content
            
            # Check if agent provided final answer
            if "Final Answer:" in agent_response:
                final_answer = self._extract_final_answer(agent_response)
                self.memory.add_message("assistant", final_answer)
                return final_answer
            
            # Extract action if present
            action_match = self._extract_action(agent_response)
            
            if action_match:
                tool_name, tool_input = action_match
                
                # Execute tool
                observation = await self._execute_tool(tool_name, tool_input)
                
                # Add action and observation to conversation
                messages.append(AIMessage(content=agent_response))
                messages.append(HumanMessage(content=f"Observation: {observation}"))
            else:
                # No action found, ask agent to continue
                messages.append(AIMessage(content=agent_response))
                messages.append(
                    HumanMessage(content="Continue with your reasoning or provide Final Answer.")
                )
        
        # Max iterations reached
        fallback = "I've reached my maximum iteration limit. Let me provide what I know so far."
        self.memory.add_message("assistant", fallback)
        return fallback
    
    def _extract_final_answer(self, text: str) -> str:
        """
        Extract final answer from agent response.
        
        Args:
            text: Agent response text
            
        Returns:
            Extracted final answer
        """
        match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text
    
    def _extract_action(self, text: str) -> Optional[tuple[str, str]]:
        """
        Extract action from agent response.
        
        Args:
            text: Agent response text
            
        Returns:
            Tuple of (tool_name, tool_input) or None
        """
        # Pattern: Action: tool_name(argument)
        match = re.search(r"Action:\s*(\w+)\((.+?)\)", text, re.IGNORECASE)
        if match:
            tool_name = match.group(1).strip()
            tool_input = match.group(2).strip().strip('"').strip("'")
            return (tool_name, tool_input)
        return None
    
    async def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input for the tool
            
        Returns:
            Tool execution result
        """
        tool = self.tool_registry.get(tool_name)
        
        if not tool:
            return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join([t.name for t in self.tool_registry.list_tools()])}"
        
        try:
            # Execute tool with appropriate parameter name
            if tool_name == "web_search":
                result = await tool.execute(query=tool_input)
            elif tool_name == "calculator":
                result = await tool.execute(expression=tool_input)
            elif tool_name == "file_reader":
                result = await tool.execute(file_path=tool_input)
            elif tool_name == "python_executor":
                result = await tool.execute(code=tool_input)
            else:
                result = await tool.execute(input=tool_input)
            
            if result.success:
                return str(result.result)
            else:
                return f"Error: {result.error}"
                
        except Exception as e:
            return f"Error executing tool: {str(e)}"
