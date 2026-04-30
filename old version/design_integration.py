"""
Design System Integration with Trading Bot
This module ensures the design system is properly integrated and accessible
throughout the trading bot application.
"""

from pathlib import Path
from utils import initialize_design_manager, get_design_manager
import logging

logger = logging.getLogger(__name__)


def init_design_system():
    """Initialize the design system for the trading bot."""
    try:
        # Get project root
        project_root = Path(__file__).parent
        design_replica_path = project_root / 'design_replica'
        
        # Initialize design manager with the replica path
        initialize_design_manager(str(design_replica_path))
        
        # Get manager and verify status
        dm = get_design_manager()
        status = dm.get_design_status()
        
        # Log design system status
        logger.info("=" * 60)
        logger.info("DESIGN SYSTEM INITIALIZATION")
        logger.info("=" * 60)
        logger.info(f"Design Replica Path: {status['root_path']}")
        logger.info(f"Replica Exists: {status['exists']}")
        logger.info(f"Components Loaded: {len(status['components'])}")
        
        for component_name, component_info in status['components'].items():
            exists_status = "✓" if component_info['exists'] else "✗"
            file_count = len(component_info['files'])
            logger.info(f"  {exists_status} {component_name}: {file_count} files")
        
        logger.info("=" * 60)
        logger.info("Design system initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize design system: {e}")
        logger.error("Continuing without design system...")
        return False


def get_design_component_info(component_name: str) -> dict:
    """
    Get information about a specific design component.
    
    Args:
        component_name: Name of the design component
        
    Returns:
        Dictionary with component information
    """
    try:
        dm = get_design_manager()
        status = dm.get_design_status()
        
        if component_name in status['components']:
            return status['components'][component_name]
        else:
            logger.warning(f"Component not found: {component_name}")
            return {}
    except Exception as e:
        logger.error(f"Error getting component info: {e}")
        return {}


def list_design_components() -> list:
    """
    List all available design components.
    
    Returns:
        List of component names
    """
    try:
        dm = get_design_manager()
        return dm.get_all_components()
    except Exception as e:
        logger.error(f"Error listing components: {e}")
        return []


def verify_design_system() -> bool:
    """
    Verify that the design system is properly set up.
    
    Returns:
        True if all components exist, False otherwise
    """
    try:
        dm = get_design_manager()
        status = dm.get_design_status()
        
        all_exist = all(
            component_info['exists'] 
            for component_info in status['components'].values()
        )
        
        if all_exist:
            logger.info("Design system verification: OK")
        else:
            logger.warning("Design system verification: INCOMPLETE")
            missing = [
                name for name, info in status['components'].items() 
                if not info['exists']
            ]
            logger.warning(f"Missing components: {missing}")
        
        return all_exist
        
    except Exception as e:
        logger.error(f"Error verifying design system: {e}")
        return False


# Initialize design system when this module is imported
if __name__ != '__main__':
    init_design_system()
