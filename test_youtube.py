"""
Quick test to reproduce the YouTube automation issue
"""

import asyncio
import sys
from orchestrator import AutomationOrchestrator

# Fix for Windows asyncio event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def test_youtube_automation():
    """Test the YouTube search automation"""
    print("Testing YouTube search automation...")
    print("="*60)
    
    orchestrator = AutomationOrchestrator()
    
    try:
        result = await orchestrator.run_automation(
            description="Open https://www.youtube.com/ on a separate tab and search for 'lima bhairav achala arpanan'",
            url="https://www.youtube.com/",
            headless=False,
            auto_heal=True
        )
        
        print("\n" + "="*60)
        print("TEST RESULT:")
        print(f"Status: {result.final_status}")
        print(f"Executions: {len(result.executions)}")
        print(f"Repairs: {len(result.repairs)}")
        print(f"Total Cost: ${result.total_cost:.4f}")
        
        if result.executions:
            last_exec = result.executions[-1]
            print(f"\nLast Execution:")
            print(f"  Success: {last_exec.success}")
            print(f"  Error: {last_exec.error_message}")
            print(f"  Screenshots: {len(last_exec.screenshots)}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_youtube_automation())
    sys.exit(0 if result and result.executions else 1)
