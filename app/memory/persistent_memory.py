"""Persistent memory implementation with database backing."""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.session import Session, Message
from app.memory.conversation_buffer import ConversationBufferMemory


class PersistentMemory:
    """Database-backed persistent memory for conversations."""
    
    def __init__(
        self, 
        db_session: AsyncSession, 
        session_id: Optional[str] = None,
        agent_type: str = "base_agent",
        user_id: Optional[str] = None,
        max_buffer_size: int = 10
    ):
        """
        Initialize persistent memory.
        
        Args:
            db_session: Database session
            session_id: Existing session ID or None to create new
            agent_type: Type of agent using this memory
            user_id: Optional user ID
            max_buffer_size: Maximum messages in buffer
        """
        self.db_session = db_session
        self.session_id = session_id or str(uuid.uuid4())
        self.agent_type = agent_type
        self.user_id = user_id
        self.buffer = ConversationBufferMemory(max_messages=max_buffer_size)
        self._loaded = False
    
    async def load(self) -> None:
        """Load conversation history from database."""
        if self._loaded:
            return
        
        # Try to load existing session
        result = await self.db_session.execute(
            select(Session).where(Session.id == self.session_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            # Load messages from database
            result = await self.db_session.execute(
                select(Message)
                .where(Message.session_id == self.session_id)
                .order_by(Message.timestamp.asc())
            )
            messages = result.scalars().all()
            
            # Add to buffer
            for msg in messages:
                metadata = json.loads(msg.metadata_json) if msg.metadata_json else None
                self.buffer.add_message(msg.role, msg.content, metadata)
        else:
            # Create new session
            session = Session(
                id=self.session_id,
                user_id=self.user_id,
                agent_type=self.agent_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db_session.add(session)
            await self.db_session.flush()
        
        self._loaded = True
    
    async def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to memory and persist to database.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata
        """
        # Ensure session is loaded
        await self.load()
        
        # Add to buffer
        self.buffer.add_message(role, content, metadata)
        
        # Persist to database
        message = Message(
            session_id=self.session_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata_json=json.dumps(metadata) if metadata else None
        )
        self.db_session.add(message)
        
        # Update session timestamp
        result = await self.db_session.execute(
            select(Session).where(Session.id == self.session_id)
        )
        session = result.scalar_one()
        session.updated_at = datetime.utcnow()
        
        await self.db_session.flush()
    
    async def get_messages(self):
        """
        Get conversation messages.
        
        Returns:
            List of messages
        """
        await self.load()
        return self.buffer.get_messages()
    
    async def get_formatted_messages(self) -> str:
        """
        Get formatted conversation history.
        
        Returns:
            Formatted messages
        """
        await self.load()
        return self.buffer.get_formatted_messages()
    
    async def clear(self) -> None:
        """Clear memory buffer (does not delete from database)."""
        self.buffer.clear()
