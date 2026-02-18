"""File reader tool for reading files."""

import os
import json
import csv
from pathlib import Path
from typing import Optional
from app.tools.base import BaseTool, ToolOutput


class FileReaderTool(BaseTool):
    """Tool for reading files from the filesystem."""
    
    name = "file_reader"
    description = (
        "Read contents of a file. "
        "Input should be a file path. "
        "Supports text files (.txt, .md, .json, .csv). "
        "Returns the file contents or an error message."
    )
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.json', '.csv', '.log', '.py', '.js', '.html', '.css'}
    
    def __init__(self, base_path: Optional[str] = None, max_file_size: int = 1_000_000):
        """
        Initialize the file reader tool.
        
        Args:
            base_path: Base directory for file operations (for security)
            max_file_size: Maximum file size in bytes (default: 1MB)
        """
        super().__init__()
        self.base_path = Path(base_path) if base_path else None
        self.max_file_size = max_file_size
    
    async def execute(self, file_path: str, **kwargs) -> ToolOutput:
        """
        Read a file from the filesystem.
        
        Args:
            file_path: Path to the file to read
            **kwargs: Additional arguments (ignored)
            
        Returns:
            ToolOutput: File contents or error
        """
        try:
            # Convert to Path object
            path = Path(file_path)
            
            # Security: Check if path is absolute and trying to escape base_path
            if self.base_path:
                # Resolve both paths to absolute
                resolved_path = path.resolve()
                resolved_base = self.base_path.resolve()
                
                # Check if the resolved path is within base_path
                try:
                    resolved_path.relative_to(resolved_base)
                except ValueError:
                    return ToolOutput(
                        success=False,
                        result=None,
                        error=f"Access denied: File path outside allowed directory"
                    )
            
            # Check if file exists
            if not path.exists():
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"File not found: {file_path}"
                )
            
            # Check if it's a file (not directory)
            if not path.is_file():
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"Path is not a file: {file_path}"
                )
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"File too large: {file_size} bytes (max: {self.max_file_size})"
                )
            
            # Check file extension
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                return ToolOutput(
                    success=False,
                    result=None,
                    error=f"Unsupported file type: {path.suffix}. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                )
            
            # Read file based on extension
            content = self._read_file(path)
            
            return ToolOutput(
                success=True,
                result=f"File: {file_path}\n\n{content}",
                error=None
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                result=None,
                error=f"Failed to read file: {str(e)}"
            )
    
    def _read_file(self, path: Path) -> str:
        """
        Read file contents based on file type.
        
        Args:
            path: Path to the file
            
        Returns:
            File contents as string
        """
        extension = path.suffix.lower()
        
        if extension == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        
        elif extension == '.csv':
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                # Format as table
                return '\n'.join([', '.join(row) for row in rows])
        
        else:
            # Read as plain text
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
