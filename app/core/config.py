"""Configuration management using Pydantic Settings."""

from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    llm_provider: str = Field(default="gemini", description="LLM provider: 'openai' or 'gemini'")

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    
    # Gemini Configuration
    google_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini model to use")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./agent_framework.db",
        description="Database connection URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_key: Optional[str] = Field(default=None, description="API authentication key")
    
    # Agent Configuration
    max_iterations: int = Field(default=10, description="Maximum agent iterations")
    max_execution_time: int = Field(default=300, description="Maximum execution time in seconds")
    conversation_memory_size: int = Field(default=10, description="Number of messages to keep in memory")
    
    # Feature Flags
    enable_web_search: bool = Field(default=True, description="Enable web search tool")
    enable_code_execution: bool = Field(default=True, description="Enable code execution tool")
    enable_file_operations: bool = Field(default=True, description="Enable file operations")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # CORS
    cors_origins: str = Field(default="*", description="Comma-separated CORS origins")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v, values):
        if values.get("llm_provider") == "openai" and not v:
            raise ValueError("OpenAI API key is required when provider is 'openai'")
        return v

    @validator("google_api_key")
    def validate_google_key(cls, v, values):
        if values.get("llm_provider") == "gemini" and not v:
            raise ValueError("Google API key is required when provider is 'gemini'")
        return v
    
    @validator("database_url", pre=True, always=True)
    def adjust_database_url(cls, v, values):
        # Check if running in a cloud function environment (Vercel or Netlify/AWS)
        is_serverless = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("NETLIFY")
        
        # If using default SQLite path and in serverless env, use /tmp
        if is_serverless and "sqlite" in v and "agent_framework.db" in v:
            return "sqlite+aiosqlite:////tmp/agent_framework.db"
        return v

    @validator("cors_origins")
    def parse_cors_origins(cls, v: str) -> list:
        """Parse comma-separated CORS origins into list."""
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.database_url.lower()
    
    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.database_url.lower()


# Global settings instance
settings = Settings()
