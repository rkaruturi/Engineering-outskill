"""
Simple test automation that should work reliably.
Use this to test the dashboard and see successful execution.
"""

import asyncio
from orchestrator import AutomationOrchestrator

async def test_simple_automation():
    """Test with a simple, reliable automation task"""
    
    print("\n" + "="*60)
    print("TESTING WITH SIMPLE AUTOMATION")
    print("="*60)
    
    orchestrator = AutomationOrchestrator()
    
    # This should work reliably
    result = await orchestrator.run_automation(
        description="Navigate to example.com and take a screenshot",
        url="https://example.com",
        headless=False,
        auto_heal=True
    )
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print(f"Status: {result.final_status}")
    print(f"Executions: {len(result.executions)}")  
    print(f"Success: {result.executions[-1].success if result.executions else False}")
    print(f"Cost: ${result.total_cost:.4f}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_simple_automation())
