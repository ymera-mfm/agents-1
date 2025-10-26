"""
YMERA Enterprise - API Gateway Core Routes Module
Production-Ready Module Initialization - v4.0.0
Fixed: Database wrapper import and all dependencies
"""

# ===============================================================================
# CRITICAL FIX: Database wrapper import added
# ===============================================================================

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ===============================================================================
# CORE IMPORTS WITH ERROR HANDLING
# ===============================================================================

try:
    # Database wrapper - CRITICAL FIX
    from . import database
    
    # API Gateway components
    from .ymera_api_gateway import (
        APIGateway,
        GatewayConfig,
        APIRequest,
        APIResponse,
        GatewayStats,
        LoadBalancer,
        RateLimitManager,
        router as gateway_router
    )
    
    # Route modules with proper error handling
    from .ymera_auth_routes import router as auth_router
    from .ymera_agent_routes import router as agent_router
    from .ymera_file_routes import router as file_router
    from .project_routes import router as project_router
    from .websocket_routes import router as websocket_router
    
except ImportError as e:
    import logging
    logging.error(f"CRITICAL: Failed to import API Gateway components: {e}")
    logging.error(f"Import error details: {type(e).__name__}: {str(e)}")
    raise ImportError(
        f"Failed to initialize API Gateway Core Routes. "
        f"Missing dependency: {e}. "
        f"Ensure all required modules are installed and paths are correct."
    ) from e

# ===============================================================================
# MODULE METADATA
# ===============================================================================

__version__ = "4.0.0"
__author__ = "YMERA Enterprise Team"
__status__ = "Production"

# ===============================================================================
# EXPORTS
# ===============================================================================

__all__ = [
    # Database wrapper - CRITICAL
    "database",
    
    # API Gateway core
    "APIGateway",
    "GatewayConfig",
    "APIRequest",
    "APIResponse",
    "GatewayStats",
    "LoadBalancer",
    "RateLimitManager",
    
    # Routers
    "gateway_router",
    "auth_router",
    "agent_router",
    "file_router",
    "project_router",
    "websocket_router",
    
    # Module info
    "__version__",
]

# ===============================================================================
# HEALTH CHECK FUNCTION
# ===============================================================================

def verify_imports() -> Dict[str, Any]:
    """
    Verify all critical imports are working.
    
    Returns:
        Dict with import status for each component
    """
    import_status = {
        "database": False,
        "api_gateway": False,
        "auth_routes": False,
        "agent_routes": False,
        "file_routes": False,
        "project_routes": False,
        "websocket_routes": False,
    }
    
    try:
        # Check database
        import_status["database"] = hasattr(database, 'get_db_session')
        
        # Check API Gateway
        import_status["api_gateway"] = APIGateway is not None
        
        # Check routers
        import_status["auth_routes"] = auth_router is not None
        import_status["agent_routes"] = agent_router is not None
        import_status["file_routes"] = file_router is not None
        import_status["project_routes"] = project_router is not None
        import_status["websocket_routes"] = websocket_router is not None
        
    except Exception as e:
        import logging
        logging.error(f"Import verification failed: {e}")
    
    return import_status

# ===============================================================================
# INITIALIZATION CHECK
# ===============================================================================

# Run verification on import
_import_status = verify_imports()
_failed_imports = [k for k, v in _import_status.items() if not v]

if _failed_imports:
    import logging
    logging.warning(
        f"API Gateway initialized with missing components: {', '.join(_failed_imports)}"
    )
else:
    import logging
    logging.info("API Gateway Core Routes initialized successfully - All components loaded")
