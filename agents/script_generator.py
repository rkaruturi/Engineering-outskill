"""
Script Generator Agent - Uses LLM to generate Playwright automation scripts.
Converts natural language task descriptions into executable Python code.
"""

import asyncio
from typing import Optional, Dict
import re
from openai import OpenAI

from config import Config
from models import AutomationTask, GeneratedScript, TaskStatus
from utils import PromptTemplates, get_cost_tracker


class ScriptGeneratorAgent:
    """Generates Playwright automation scripts using LLM"""
    
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
    
    async def generate_script(
        self, 
        task: AutomationTask,
        context: Optional[Dict] = None
    ) -> GeneratedScript:
        """Generate a Playwright script from task description"""
        
        print(f"🤖 Generating script for: {task.description}")
        
        # Update task status
        task.status = TaskStatus.GENERATING
        
        # Build prompt
        prompt = PromptTemplates.script_generation_prompt(
            task_description=task.description,
            url=task.url
        )
        
        # Add context if provided (e.g., from error repair)
        if context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        # Check budget before making request
        estimated_cost = 0.02  # Conservative estimate
        budget_ok, message = self.cost_tracker.check_budget(estimated_cost)
        if not budget_ok:
            raise ValueError(f"Budget check failed: {message}")
        
        try:
            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": PromptTemplates.get_system_message("script_generator")
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent code
                max_tokens=2000
            )
            
            # Extract response
            generated_code = response.choices[0].message.content
            
            # Extract code from markdown if present
            code = self._extract_code(generated_code)
            
            # Track costs
            usage = response.usage
            cost_info = self.cost_tracker.track_request(
                model=self.model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
            
            print(f"✓ Script generated (${cost_info['cost']:.4f})")
            
            # Create GeneratedScript object
            script = GeneratedScript(
                task_id=task.id,
                code=code,
                model_used=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cost=cost_info['cost']
            )
            
            # Save script to file
            self._save_script(script)
            
            return script
            
        except Exception as e:
            print(f"✗ Script generation failed: {e}")
            raise
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from markdown code blocks"""
        
        # Try to find code in markdown blocks
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            # Return the largest code block (likely the main script)
            return max(matches, key=len).strip()
        
        # If no code blocks, return the whole response
        return response.strip()
    
    def _save_script(self, script: GeneratedScript):
        """Save generated script to file"""
        script_dir = Config.SCRIPTS_DIR / script.task_id
        script_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = script_dir / f"script_v{script.version}.py"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script.code)
        
        print(f"💾 Script saved to: {script_path}")
    
    async def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Validate Python syntax of generated code"""
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
    
    def get_script_metadata(self, script: GeneratedScript) -> Dict:
        """Get metadata about the generated script"""
        lines = script.code.split('\n')
        
        return {
            "task_id": script.task_id,
            "version": script.version,
            "lines_of_code": len(lines),
            "model_used": script.model_used,
            "cost": script.cost,
            "prompt_tokens": script.prompt_tokens,
            "completion_tokens": script.completion_tokens,
            "generated_at": script.generated_at.isoformat()
        }


# Convenience function for quick script generation
async def generate_automation_script(
    description: str, 
    url: Optional[str] = None
) -> GeneratedScript:
    """Quick function to generate a script from a description"""
    
    task = AutomationTask(
        description=description,
        url=url
    )
    
    agent = ScriptGeneratorAgent()
    return await agent.generate_script(task)


# Example usage
if __name__ == "__main__":
    async def main():
        task = AutomationTask(
            description="Navigate to example.com and take a screenshot of the page",
            url="https://example.com"
        )
        
        agent = ScriptGeneratorAgent()
        script = await agent.generate_script(task)
        
        print("\n" + "="*50)
        print("GENERATED SCRIPT:")
        print("="*50)
        print(script.code)
        print("\n" + "="*50)
        print("METADATA:", agent.get_script_metadata(script))
    
    asyncio.run(main())
