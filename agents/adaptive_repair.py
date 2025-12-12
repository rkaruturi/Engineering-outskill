"""
Adaptive Repair Agent - Automatically fixes failed scripts using LLM.
Implements self-healing by regenerating scripts with error context.
"""

import asyncio
from typing import Optional
from openai import OpenAI

from config import Config
from models import (
    GeneratedScript, ErrorDiagnosis, RepairAttempt, 
    TaskStatus, AutomationTask
)
from utils import PromptTemplates, get_cost_tracker


class AdaptiveRepairAgent:
    """Repairs failed automation scripts"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/self-healing-automation",
                "X-Title": "Self-Healing Browser Automation"
            },
            timeout=60.0
        )
        self.cost_tracker = get_cost_tracker()
        self.model = Config.DEFAULT_MODEL
    
    async def repair_script(
        self,
        original_script: GeneratedScript,
        diagnosis: ErrorDiagnosis,
        attempt_number: int = 1
    ) -> RepairAttempt:
        """Attempt to repair a failed script"""
        
        print(f"🔧 Repairing script (attempt {attempt_number}/{Config.MAX_REPAIR_ATTEMPTS})")
        
        if attempt_number > Config.MAX_REPAIR_ATTEMPTS:
            raise ValueError(f"Exceeded maximum repair attempts ({Config.MAX_REPAIR_ATTEMPTS})")
        
        # Try quick fixes first
        quick_fix_result = self._try_quick_fixes(original_script, diagnosis)
        if quick_fix_result:
            print("  ✓ Applied quick fix")
            return quick_fix_result
        
        # Use LLM for complex repairs
        print("  Using LLM for repair...")
        return await self._llm_repair(original_script, diagnosis, attempt_number)
    
    def _try_quick_fixes(
        self,
        script: GeneratedScript,
        diagnosis: ErrorDiagnosis
    ) -> Optional[RepairAttempt]:
        """Apply rule-based quick fixes for common issues"""
        
        code = script.code
        modified = False
        repair_strategy = []
        
        # Fix 1: Add longer timeouts for timeout errors
        if diagnosis.error_type.value == "timeout":
            if "timeout=" not in code:
                code = code.replace(
                    "await page.goto(",
                    "await page.goto("
                ).replace(
                    "await page.goto(",
                    "await page.goto(timeout=60000, "
                )
                modified = True
                repair_strategy.append("Increased navigation timeout to 60s")
            
            if "wait_until=" not in code:
                code = code.replace(
                    "await page.goto(",
                    "await page.goto(wait_until='networkidle', "
                )
                modified = True
                repair_strategy.append("Added network idle wait")
        
        # Fix 2: Add explicit waits for selector errors
        elif diagnosis.error_type.value == "selector_not_found":
            # Look for immediate clicks without waits
            if "await page.click(" in code and "wait_for_selector" not in code:
                # This is a simplified fix - LLM will handle complex cases
                modified = True
                repair_strategy.append("Would add explicit waits (LLM recommended)")
        
        # If no quick fix applied, return None
        if not modified:
            return None
        
        # Create repaired script
        repaired_script = GeneratedScript(
            task_id=script.task_id,
            code=code,
            model_used="quick_fix",
            version=script.version + 1,
            cost=0.0  # Quick fixes are free
        )
        
        # Save repaired script
        self._save_script(repaired_script)
        
        return RepairAttempt(
            task_id=script.task_id,
            original_version=script.version,
            repaired_script=repaired_script,
            repair_strategy="; ".join(repair_strategy),
            diagnosis_used=diagnosis,
            attempt_number=1
        )
    
    async def _llm_repair(
        self,
        script: GeneratedScript,
        diagnosis: ErrorDiagnosis,
        attempt_number: int
    ) -> RepairAttempt:
        """Use LLM to repair the script"""
        
        # Build repair prompt
        prompt = PromptTemplates.error_repair_prompt(
            original_script=script.code,
            error_type=diagnosis.error_type.value,
            error_message=diagnosis.error_message,
            error_context=diagnosis.error_context
        )
        
        # Add suggested fixes to context
        if diagnosis.suggested_fixes:
            prompt += f"\n\nSuggested Fixes:\n"
            for fix in diagnosis.suggested_fixes[:3]:  # Top 3 suggestions
                prompt += f"- {fix}\n"
        
        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.get_system_message("error_repair")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Slightly higher for creative fixes
                max_tokens=2000
            )
            
            # Extract code
            repaired_code = self._extract_code(response.choices[0].message.content)
            
            # Track costs
            usage = response.usage
            cost_info = self.cost_tracker.track_request(
                model=self.model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
            
            print(f"  ✓ Script repaired (${cost_info['cost']:.4f})")
            
            # Create repaired script
            repaired_script = GeneratedScript(
                task_id=script.task_id,
                code=repaired_code,
                model_used=self.model,
                version=script.version + 1,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cost=cost_info['cost']
            )
            
            # Save repaired script
            self._save_script(repaired_script)
            
            return RepairAttempt(
                task_id=script.task_id,
                original_version=script.version,
                repaired_script=repaired_script,
                repair_strategy=f"LLM repair for {diagnosis.error_type.value}",
                diagnosis_used=diagnosis,
                attempt_number=attempt_number
            )
            
        except Exception as e:
            print(f"  ✗ Repair failed: {e}")
            raise
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response"""
        import re
        
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        
        return response.strip()
    
    def _save_script(self, script: GeneratedScript):
        """Save repaired script to file"""
        script_dir = Config.SCRIPTS_DIR / script.task_id
        script_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = script_dir / f"script_v{script.version}.py"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script.code)
        
        print(f"  💾 Repaired script saved: v{script.version}")
    
    def get_repair_summary(self, repair: RepairAttempt) -> str:
        """Format repair attempt as summary"""
        
        return f"""
🔧 REPAIR ATTEMPT #{repair.attempt_number}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Original: v{repair.original_version} → Repaired: v{repair.repaired_script.version}
Strategy: {repair.repair_strategy}

Error Type: {repair.diagnosis_used.error_type.value}
Cost: ${repair.repaired_script.cost:.4f}

Status: {'✓ Success' if repair.success else '○ Pending verification'}
"""


# Convenience function
async def repair_failed_script(
    script: GeneratedScript,
    diagnosis: ErrorDiagnosis
) -> RepairAttempt:
    """Quick function to repair a script"""
    agent = AdaptiveRepairAgent()
    return await agent.repair_script(script, diagnosis)
