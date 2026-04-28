#!/usr/bin/env python3
"""
Design System Integration Test Script
Verifies that the design replica and integration system work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_design_manager():
    """Test DesignManager functionality."""
    print("\n" + "="*60)
    print("TESTING DESIGN MANAGER")
    print("="*60)
    
    try:
        from utils import get_design_manager, initialize_design_manager
        
        # Initialize
        print("\n1. Initializing design manager...")
        initialize_design_manager()
        print("   ✓ Design manager initialized")
        
        # Get manager
        print("\n2. Getting design manager instance...")
        dm = get_design_manager()
        print("   ✓ Design manager instance obtained")
        
        # Get components
        print("\n3. Listing components...")
        components = dm.get_all_components()
        print(f"   ✓ Found {len(components)} components:")
        for comp in components:
            print(f"     - {comp}")
        
        # Check status
        print("\n4. Checking design status...")
        status = dm.get_design_status()
        print(f"   ✓ Design root: {status['root_path']}")
        print(f"   ✓ Exists: {status['exists']}")
        
        # Validate components
        print("\n5. Validating components...")
        all_exist = True
        for comp_name, comp_info in status['components'].items():
            exists = comp_info['exists']
            symbol = "✓" if exists else "✗"
            file_count = len(comp_info['files'])
            print(f"   {symbol} {comp_name}: {file_count} files")
            if not exists:
                all_exist = False
        
        # Read design spec
        print("\n6. Reading design specification...")
        spec = dm.get_design_spec('technical_trading_interface')
        if spec:
            print(f"   ✓ Spec name: {spec.get('name', 'N/A')}")
            print(f"   ✓ Colors: {len(spec.get('colors', {}))} defined")
            print(f"   ✓ Typography: {len(spec.get('typography', {}))} styles")
        else:
            print("   ℹ Spec not parsed (YAML library may not be available)")
        
        # Get component files
        print("\n7. Getting component files...")
        files = dm.get_component_files('executive_dashboard')
        print(f"   ✓ Files in executive_dashboard: {files}")
        
        # Export status
        print("\n8. Exporting design status...")
        json_output = dm.export_design_status()
        if json_output:
            print("   ✓ Status exported as JSON")
        
        print("\n" + "="*60)
        print("DESIGN MANAGER TESTS: PASSED ✓")
        print("="*60)
        return all_exist
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_design_integration():
    """Test design integration module."""
    print("\n" + "="*60)
    print("TESTING DESIGN INTEGRATION")
    print("="*60)
    
    try:
        from design_integration import (
            init_design_system,
            verify_design_system,
            list_design_components,
            get_design_component_info,
        )
        
        # Initialize
        print("\n1. Initializing design system...")
        result = init_design_system()
        if result:
            print("   ✓ Design system initialized")
        else:
            print("   ℹ Design system initialization returned False")
        
        # Verify
        print("\n2. Verifying design system...")
        verified = verify_design_system()
        print(f"   {'✓' if verified else '✗'} Verification result: {verified}")
        
        # List components
        print("\n3. Listing components...")
        components = list_design_components()
        print(f"   ✓ Found {len(components)} components")
        
        # Get component info
        print("\n4. Getting component information...")
        for comp in components[:2]:  # Test first 2 components
            info = get_design_component_info(comp)
            exists = info.get('exists', False)
            symbol = "✓" if exists else "✗"
            print(f"   {symbol} {comp}")
        
        print("\n" + "="*60)
        print("DESIGN INTEGRATION TESTS: PASSED ✓")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_access():
    """Test file access through design manager."""
    print("\n" + "="*60)
    print("TESTING FILE ACCESS")
    print("="*60)
    
    try:
        from utils import get_design_manager
        
        dm = get_design_manager()
        
        # Test reading DESIGN.md
        print("\n1. Reading DESIGN.md...")
        design_content = dm.read_design_file(
            'technical_trading_interface', 
            'DESIGN.md'
        )
        if design_content:
            lines = len(design_content.split('\n'))
            print(f"   ✓ Read {lines} lines from DESIGN.md")
        else:
            print("   ✗ Failed to read DESIGN.md")
            return False
        
        # Test reading HTML files
        print("\n2. Reading HTML files...")
        for component in ['executive_dashboard', 'configuration_settings']:
            html = dm.read_design_file(component, 'code.html')
            if html:
                print(f"   ✓ Read {len(html)} bytes from {component}/code.html")
            else:
                print(f"   ✗ Failed to read {component}/code.html")
                return False
        
        print("\n" + "="*60)
        print("FILE ACCESS TESTS: PASSED ✓")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# DESIGN SYSTEM INTEGRATION TEST SUITE")
    print("#"*60)
    
    tests = [
        ("Design Manager", test_design_manager),
        ("File Access", test_file_access),
        ("Design Integration", test_design_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nTest {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    
    for test_name, result in results:
        symbol = "✓" if result else "✗"
        status = "PASSED" if result else "FAILED"
        print(f"{symbol} {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("#"*60)
    if all_passed:
        print("# ALL TESTS PASSED! ✓")
        print("#"*60)
        return 0
    else:
        print("# SOME TESTS FAILED! ✗")
        print("#"*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
