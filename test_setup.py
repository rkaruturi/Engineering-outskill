"""
Quick test to verify OpenAI client initialization is working
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all agents can be imported"""
    print("Testing imports...")
    
    try:
        from config import Config
        print("✓ Config imported")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from models import AutomationTask
        print("✓ Models imported")
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False
    
    try:
        from agents.script_generator import ScriptGeneratorAgent
        print("✓ ScriptGeneratorAgent imported")
    except Exception as e:
        print(f"✗ ScriptGeneratorAgent import failed: {e}")
        return False
    
    try:
        from agents.execution_engine import ExecutionEngineAgent
        print("✓ ExecutionEngineAgent imported")
    except Exception as e:
        print(f"✗ ExecutionEngineAgent import failed: {e}")
        return False
    
    try:
        from agents.error_diagnosis import ErrorDiagnosisAgent
        print("✓ ErrorDiagnosisAgent imported")
    except Exception as e:
        print(f"✗ ErrorDiagnosisAgent import failed: {e}")
        return False
    
    try:
        from agents.adaptive_repair import AdaptiveRepairAgent
        print("✓ AdaptiveRepairAgent imported")
    except Exception as e:
        print(f"✗ AdaptiveRepairAgent import failed: {e}")
        return False
    
    return True


def test_agent_initialization():
    """Test that agents can be initialized"""
    print("\nTesting agent initialization...")
    
    try:
        from agents.script_generator import ScriptGeneratorAgent
        agent = ScriptGeneratorAgent()
        print("✓ ScriptGeneratorAgent initialized")
    except Exception as e:
        print(f"✗ ScriptGeneratorAgent initialization failed: {e}")
        return False
    
    try:
        from agents.execution_engine import ExecutionEngineAgent
        agent = ExecutionEngineAgent()
        print("✓ ExecutionEngineAgent initialized")
    except Exception as e:
        print(f"✗ ExecutionEngineAgent initialization failed: {e}")
        return False
    
    try:
        from agents.error_diagnosis import ErrorDiagnosisAgent
        agent = ErrorDiagnosisAgent()
        print("✓ ErrorDiagnosisAgent initialized")
    except Exception as e:
        print(f"✗ ErrorDiagnosisAgent initialization failed: {e}")
        return False
    
    try:
        from agents.adaptive_repair import AdaptiveRepairAgent
        agent = AdaptiveRepairAgent()
        print("✓ AdaptiveRepairAgent initialized")
    except Exception as e:
        print(f"✗ AdaptiveRepairAgent initialization failed: {e}")
        return False
    
    return True


def test_orchestrator():
    """Test orchestrator initialization"""
    print("\nTesting orchestrator...")
    
    try:
        from orchestrator import AutomationOrchestrator
        orch = AutomationOrchestrator()
        print("✓ AutomationOrchestrator initialized")
        return True
    except Exception as e:
        print(f"✗ AutomationOrchestrator initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("SELF-HEALING BROWSER AUTOMATION - VERIFICATION TEST")
    print("="*60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test agent initialization
    if not test_agent_initialization():
        all_passed = False
    
    # Test orchestrator
    if not test_orchestrator():
        all_passed = False
    
    # Final result
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe system is ready to use.")
        print("Run: streamlit run dashboard.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above.")
    print()
    
    sys.exit(0 if all_passed else 1)
