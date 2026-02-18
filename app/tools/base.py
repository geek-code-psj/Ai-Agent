"""Base tool interface and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base model for tool input validation."""
    pass


class ToolOutput(BaseModel):
    """Base model for tool output."""
    success: bool = Field(description="Whether the tool execution was successful")
    result: Any = Field(description="The result of the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Tools are actions that agents can take to interact with the world.
    Each tool should implement the execute method and provide a description.
    """
    
    name: str
    description: str
    
    def __init__(self):
        """Initialize the tool."""
        if not hasattr(self, 'name') or not hasattr(self, 'description'):
            raise NotImplementedError("Tools must define 'name' and 'description' attributes")
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolOutput: The result of the tool execution
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: The tool to register
        """
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[BaseTool]:
        """
        List all registered tools.
        
        Returns:
            List of all registered tools
        """
        return list(self._tools.values())
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get descriptions of all registered tools.
        
        Returns:
            List of tool descriptions
        """
        return [tool.to_dict() for tool in self._tools.values()]
