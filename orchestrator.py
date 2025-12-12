"""
Orchestrator - Coordinates all agents for end-to-end automation.
Manages the complete workflow: generate → execute → diagnose → repair → retry
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json

from config import Config
from models import (
    AutomationTask, GeneratedScript, ExecutionResult,
    ErrorDiagnosis, RepairAttempt, TestRun, TaskStatus
)
from agents import (
    ScriptGeneratorAgent, ExecutionEngineAgent,
    ErrorDiagnosisAgent, AdaptiveRepairAgent
)
from utils import get_cost_tracker


class AutomationOrchestrator:
    """Orchestrates the complete automation workflow"""
    
    def __init__(self):
        self.script_generator = ScriptGeneratorAgent()
        self.execution_engine = ExecutionEngineAgent()
        self.error_diagnosis = ErrorDiagnosisAgent()
        self.adaptive_repair = AdaptiveRepairAgent()
        self.cost_tracker = get_cost_tracker()
    
    async def run_automation(
        self,
        description: str,
        url: Optional[str] = None,
        headless: Optional[bool] = None,
        auto_heal: Optional[bool] = None
    ) -> TestRun:
        """
        Run complete automation workflow with self-healing
        
        Args:
            description: Natural language task description
            url: Optional starting URL
            headless: Run browser in headless mode
            auto_heal: Enable automatic repair on failures
        
        Returns:
            TestRun with complete execution history
        """
        
        if auto_heal is None:
            auto_heal = Config.AUTO_HEAL
        
        print("="*60)
        print("🚀 STARTING AUTOMATION WORKFLOW")
        print("="*60)
        print(f"Task: {description}")
        if url:
            print(f"URL: {url}")
        print(f"Auto-heal: {'Enabled' if auto_heal else 'Disabled'}")
        print("="*60 + "\n")
        
        # Create task
        task = AutomationTask(
            description=description,
            url=url
        )
        
        # Initialize test run
        test_run = TestRun(task=task)
        
        try:
            # ========== STEP 1: GENERATE SCRIPT ==========
            print("\n📝 STEP 1: Script Generation")
            print("-" * 60)
            
            script = await self.script_generator.generate_script(task)
            test_run.scripts.append(script)
            test_run.add_cost(script.cost)
            
            # ========== STEP 2: EXECUTE SCRIPT ==========
            current_script = script
            attempt = 0
            max_attempts = Config.MAX_REPAIR_ATTEMPTS + 1  # Initial + repairs
            
            while attempt < max_attempts:
                attempt += 1
                
                print(f"\n▶️  STEP 2.{attempt}: Execution (Script v{current_script.version})")
                print("-" * 60)
                
                try:
                    result = await self.execution_engine.execute_script(
                        current_script,
                        headless=headless
                    )
                    test_run.executions.append(result)
                except Exception as exec_error:
                    # If execution fails to start, create a failed ExecutionResult
                    print(f"✗ Execution failed to start: {exec_error}")
                    import traceback
                    traceback.print_exc()
                    
                    result = ExecutionResult(
                        task_id=task.id,
                        script_version=current_script.version,
                        success=False,
                        error_message=f"Execution failed to start: {str(exec_error)}",
                        console_logs=[traceback.format_exc()]
                    )
                    test_run.executions.append(result)
                
                # Check if successful
                if result.success:
                    print("\n" + "="*60)
                    print("✅ AUTOMATION COMPLETED SUCCESSFULLY!")
                    print("="*60)
                    test_run.mark_complete(TaskStatus.SUCCESS)
                    break
                
                # Execution failed
                print(f"\n❌ Execution failed: {result.error_message}")
                
                # Check if we should attempt repair
                if not auto_heal or attempt >= max_attempts:
                    print("\n" + "="*60)
                    print("❌ AUTOMATION FAILED")
                    if not auto_heal:
                        print("(Auto-heal disabled)")
                    else:
                        print(f"(Max repair attempts reached: {Config.MAX_REPAIR_ATTEMPTS})")
                    print("="*60)
                    test_run.mark_complete(TaskStatus.FAILED)
                    break
                
                # ========== STEP 3: DIAGNOSE ERROR ==========
                print(f"\n🔍 STEP 3.{attempt}: Error Diagnosis")
                print("-" * 60)
                
                diagnosis = await self.error_diagnosis.diagnose_error(result)
                test_run.diagnoses.append(diagnosis)
                
                print(f"Error Type: {diagnosis.error_type.value}")
                print(f"Confidence: {diagnosis.confidence * 100:.0f}%")
                
                # ========== STEP 4: REPAIR SCRIPT ==========
                print(f"\n🔧 STEP 4.{attempt}: Adaptive Repair")
                print("-" * 60)
                
                try:
                    repair = await self.adaptive_repair.repair_script(
                        current_script,
                        diagnosis,
                        attempt_number=attempt
                    )
                    test_run.repairs.append(repair)
                    test_run.add_cost(repair.repaired_script.cost)
                    
                    # Use repaired script for next attempt
                    current_script = repair.repaired_script
                    test_run.scripts.append(current_script)
                    
                    print(f"Strategy: {repair.repair_strategy}")
                    
                except Exception as e:
                    print(f"✗ Repair failed: {e}")
                    test_run.mark_complete(TaskStatus.FAILED)
                    break
            
            # Save test run
            self._save_test_run(test_run)
            
            # Print summary
            print("\n" + "="*60)
            print("📊 EXECUTION SUMMARY")
            print("="*60)
            print(self.get_summary(test_run))
            
            return test_run
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            test_run.mark_complete(TaskStatus.FAILED)
            return test_run
    
    def _save_test_run(self, test_run: TestRun):
        """Save test run to JSON file"""
        run_dir = Config.LOGS_DIR / test_run.task.id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        run_file = run_dir / "test_run.json"
        
        # Convert to dict
        run_data = {
            "task": test_run.task.model_dump(),
            "scripts": [s.model_dump() for s in test_run.scripts],
            "executions": [e.model_dump() for e in test_run.executions],
            "diagnoses": [d.model_dump() for d in test_run.diagnoses],
            "repairs": [r.model_dump() for r in test_run.repairs],
            "final_status": test_run.final_status.value,
            "total_cost": test_run.total_cost,
            "completed_at": test_run.completed_at.isoformat() if test_run.completed_at else None
        }
        
        with open(run_file, 'w', encoding='utf-8') as f:
            json.dump(run_data, f, indent=2, default=str)
        
        print(f"\n💾 Test run saved to: {run_file}")
    
    def get_summary(self, test_run: TestRun) -> str:
        """Get formatted summary of test run"""
        
        status_emoji = "✅" if test_run.final_status == TaskStatus.SUCCESS else "❌"
        
        summary = f"""
{status_emoji} Status: {test_run.final_status.value.upper()}
Task ID: {test_run.task.id}
Description: {test_run.task.description}

Workflow Metrics:
  Scripts Generated: {len(test_run.scripts)}
  Execution Attempts: {len(test_run.executions)}
  Repairs Made: {len(test_run.repairs)}
  Total Cost: ${test_run.total_cost:.4f}

Final Result:
  Success: {test_run.final_status == TaskStatus.SUCCESS}
"""
        
        if test_run.executions:
            last_execution = test_run.executions[-1]
            summary += f"  Screenshots: {len(last_execution.screenshots)}\n"
            summary += f"  Video: {'Available' if last_execution.video_path else 'N/A'}\n"
            summary += f"  Execution Time: {last_execution.execution_time:.2f}s\n"
        
        if test_run.completed_at:
            duration = (test_run.completed_at - test_run.task.created_at).total_seconds()
            summary += f"\nTotal Duration: {duration:.1f}s"
        
        summary += "\n\n" + self.cost_tracker.format_cost_report()
        
        return summary
    
    @staticmethod
    def load_test_run(task_id: str) -> Optional[TestRun]:
        """Load a saved test run"""
        run_file = Config.LOGS_DIR / task_id / "test_run.json"
        
        if not run_file.exists():
            return None
        
        with open(run_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct TestRun (simplified - you'd need to reconstruct all nested objects)
        # This is a basic implementation
        return data


# Convenience function
async def automate(
    description: str,
    url: Optional[str] = None,
    **kwargs
) -> TestRun:
    """Quick function to run automation"""
    orchestrator = AutomationOrchestrator()
    return await orchestrator.run_automation(description, url, **kwargs)


# Example usage
if __name__ == "__main__":
    async def main():
        # Example 1: Simple navigation
        result = await automate(
            "Navigate to example.com and take a screenshot",
            url="https://example.com"
        )
        
        print(f"\nFinal status: {result.final_status}")
    
    asyncio.run(main())
