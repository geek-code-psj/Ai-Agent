"""Main application entry point."""

import uvicorn
from app.core.config import settings


def main():
    """Run the application."""
    uvicorn.run(
        "app.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
