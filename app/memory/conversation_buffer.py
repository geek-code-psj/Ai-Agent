from typing import List, Dict, Any, Optional
from collections import deque
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class ConversationBufferMemory:
    """In-memory conversation buffer with size limit."""
    
    def __init__(self, max_messages: int = 10):
        """
        Initialize conversation buffer memory.
        
        Args:
            max_messages: Maximum number of messages to keep in buffer
        """
        self.max_messages = max_messages
        self._messages: deque = deque(maxlen=max_messages)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the buffer.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata
        """
        message = self._create_message(role, content, metadata)
        self._messages.append(message)
    
    def get_messages(self) -> List[BaseMessage]:
        """
        Get all messages in the buffer.
        
        Returns:
            List of messages
        """
        return list(self._messages)
    
    def get_formatted_messages(self) -> str:
        """
        Get messages formatted as a string.
        
        Returns:
            Formatted conversation history
        """
        formatted = []
        for msg in self._messages:
            role = self._get_role_name(msg)
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
    
    def clear(self) -> None:
        """Clear all messages from buffer."""
        self._messages.clear()
    
    def get_message_count(self) -> int:
        """
        Get the number of messages in buffer.
        
        Returns:
            Number of messages
        """
        return len(self._messages)
    
    def _create_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> BaseMessage:
        """
        Create a LangChain message object.
        
        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata
            
        Returns:
            LangChain message object
        """
        if role == "user":
            return HumanMessage(content=content, additional_kwargs=metadata or {})
        elif role == "assistant":
            return AIMessage(content=content, additional_kwargs=metadata or {})
        elif role == "system":
            return SystemMessage(content=content, additional_kwargs=metadata or {})
        else:
            raise ValueError(f"Unknown message role: {role}")
    
    def _get_role_name(self, message: BaseMessage) -> str:
        """
        Get role name from message object.
        
        Args:
            message: LangChain message
            
        Returns:
            Role name
        """
        if isinstance(message, HumanMessage):
            return "User"
        elif isinstance(message, AIMessage):
            return "Assistant"
        elif isinstance(message, SystemMessage):
            return "System"
        else:
            return "Unknown"
