"""
Design System Manager for Trading Bot
Manages and integrates the design replica with the trading system.
Provides centralized access to design assets and specifications.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DesignManager:
    """Manager for design system assets and specifications."""
    
    def __init__(self, design_replica_path: Optional[str] = None):
        """
        Initialize the Design Manager.
        
        Args:
            design_replica_path: Path to the design_replica folder. 
                                If None, uses default location relative to project root.
        """
        if design_replica_path is None:
            # Default to design_replica folder in project root
            project_root = Path(__file__).parent.parent
            design_replica_path = project_root / "design_replica"
        else:
            design_replica_path = Path(design_replica_path)
        
        self.design_root = Path(design_replica_path)
        self.design_components = {
            'technical_trading_interface': self.design_root / 'technical_trading_interface',
            'configuration_settings': self.design_root / 'configuration_settings',
            'executive_dashboard': self.design_root / 'executive_dashboard',
            'positions_order_book': self.design_root / 'positions_order_book',
            'strategy_analytics': self.design_root / 'strategy_analytics',
            'system_logs_monitoring': self.design_root / 'system_logs_monitoring',
        }
        
        self._validate_design_structure()
        logger.info(f"Design Manager initialized with replica at: {self.design_root}")
    
    def _validate_design_structure(self) -> None:
        """Validate that all required design components exist."""
        if not self.design_root.exists():
            raise ValueError(f"Design replica root directory not found: {self.design_root}")
        
        missing_components = []
        for component_name, component_path in self.design_components.items():
            if not component_path.exists():
                missing_components.append(component_name)
        
        if missing_components:
            logger.warning(f"Missing design components: {missing_components}")
        else:
            logger.info("All design components validated successfully")
    
    def get_design_file(self, component: str, filename: str) -> Optional[Path]:
        """
        Get the path to a design file.
        
        Args:
            component: Design component name
            filename: Name of the file within the component
            
        Returns:
            Path object if file exists, None otherwise
        """
        if component not in self.design_components:
            logger.warning(f"Unknown design component: {component}")
            return None
        
        file_path = self.design_components[component] / filename
        if file_path.exists():
            return file_path
        else:
            logger.warning(f"Design file not found: {file_path}")
            return None
    
    def read_design_file(self, component: str, filename: str) -> Optional[str]:
        """
        Read the contents of a design file.
        
        Args:
            component: Design component name
            filename: Name of the file within the component
            
        Returns:
            File contents as string, or None if file doesn't exist
        """
        file_path = self.get_design_file(component, filename)
        if file_path is None:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading design file {file_path}: {e}")
            return None
    
    def get_design_spec(self, component: str = 'technical_trading_interface') -> Optional[Dict[str, Any]]:
        """
        Parse and return the design specification.
        
        Args:
            component: Design component (default: technical_trading_interface)
            
        Returns:
            Dictionary containing design specifications or None
        """
        spec_content = self.read_design_file(component, 'DESIGN.md')
        if spec_content is None:
            return None
        
        # Parse YAML-like specification
        try:
            import yaml
            # Extract YAML frontmatter
            if spec_content.startswith('---'):
                _, frontmatter, _ = spec_content.split('---', 2)
                spec = yaml.safe_load(frontmatter)
                return spec
        except ImportError:
            logger.warning("PyYAML not available for design spec parsing")
        except Exception as e:
            logger.error(f"Error parsing design spec: {e}")
        
        return None
    
    def get_all_components(self) -> List[str]:
        """Get list of all available design components."""
        return list(self.design_components.keys())
    
    def get_component_files(self, component: str) -> List[str]:
        """
        Get list of all files in a design component.
        
        Args:
            component: Design component name
            
        Returns:
            List of filenames in the component
        """
        if component not in self.design_components:
            logger.warning(f"Unknown design component: {component}")
            return []
        
        component_path = self.design_components[component]
        if not component_path.exists():
            return []
        
        return [f.name for f in component_path.iterdir() if f.is_file()]
    
    def get_design_status(self) -> Dict[str, Any]:
        """
        Get status information about the design system.
        
        Returns:
            Dictionary with design system status information
        """
        status = {
            'root_path': str(self.design_root),
            'exists': self.design_root.exists(),
            'components': {},
        }
        
        for component_name, component_path in self.design_components.items():
            status['components'][component_name] = {
                'path': str(component_path),
                'exists': component_path.exists(),
                'files': self.get_component_files(component_name) if component_path.exists() else []
            }
        
        return status
    
    def export_design_status(self, output_file: Optional[str] = None) -> Optional[str]:
        """
        Export design system status to JSON file.
        
        Args:
            output_file: Optional path to save status JSON
            
        Returns:
            JSON string of status, or None if export fails
        """
        try:
            status = self.get_design_status()
            json_str = json.dumps(status, indent=2)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                logger.info(f"Design status exported to: {output_file}")
            
            return json_str
        except Exception as e:
            logger.error(f"Error exporting design status: {e}")
            return None


# Global design manager instance
_design_manager: Optional[DesignManager] = None


def get_design_manager(design_replica_path: Optional[str] = None) -> DesignManager:
    """
    Get or create the global design manager instance.
    
    Args:
        design_replica_path: Optional path to design_replica folder
        
    Returns:
        DesignManager instance
    """
    global _design_manager
    
    if _design_manager is None:
        _design_manager = DesignManager(design_replica_path)
    
    return _design_manager


def initialize_design_manager(design_replica_path: Optional[str] = None) -> None:
    """Initialize the global design manager."""
    global _design_manager
    _design_manager = DesignManager(design_replica_path)
    logger.info("Design manager initialized")
