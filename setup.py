"""
Quick setup script to initialize the self-healing browser automation system.
Run this script after cloning the repository.
"""

import subprocess
import sys
from pathlib import Path
import shutil


def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {message}")
    print('='*60)


def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n→ {description}")
    print(f"  Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("  ✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e}")
        print(f"  Error output: {e.stderr}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║   Self-Healing Browser Automation - Setup Script        ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    base_dir = Path(__file__).parent
    
    # Step 1: Check Python version
    print_step(1, "Checking Python Version")
    python_version = sys.version_info
    print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 9):
        print("✗ Error: Python 3.9+ is required")
        return False
    print("✓ Python version OK")
    
    # Step 2: Create .env file if it doesn't exist
    print_step(2, "Setting up Environment Configuration")
    
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"✓ Created .env file from .env.example")
        print("\n⚠️  IMPORTANT: Edit .env and add your OpenRouter API key!")
        print("   Get your key at: https://openrouter.ai/keys")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("✗ Warning: .env.example not found")
    
    # Step 3: Install Python dependencies
    print_step(3, "Installing Python Dependencies")
    
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing packages from requirements.txt"
    ):
        print("\n✗ Failed to install dependencies")
        return False
    
    # Step 4: Install Playwright browsers
    print_step(4, "Installing Playwright Browsers")
    
    if not run_command(
        "playwright install chromium",
        "Installing Chromium browser for Playwright"
    ):
        print("\n⚠️  Browser installation failed, but you can try manually:")
        print("   playwright install chromium")
    
    # Step 5: Create necessary directories
    print_step(5, "Creating Directory Structure")
    
    directories = [
        base_dir / "artifacts",
        base_dir / "artifacts" / "screenshots",
        base_dir / "artifacts" / "videos",
        base_dir / "artifacts" / "logs",
        base_dir / "artifacts" / "scripts"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory.relative_to(base_dir)}")
    
    # Step 6: Verify installation
    print_step(6, "Verifying Installation")
    
    try:
        import playwright
        import openai
        import streamlit
        print("✓ All core packages imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Final message
    print(f"\n{'='*60}")
    print("✅ SETUP COMPLETE!")
    print('='*60)
    print("""
Next steps:
1. Edit .env and add your OpenRouter API key:
   OPENROUTER_API_KEY=your_key_here

2. Run the dashboard:
   streamlit run dashboard.py

3. Or use the Python API:
   python
   >>> from orchestrator import automate
   >>> import asyncio
   >>> asyncio.run(automate("Navigate to example.com"))

For more information, see README.md
    """)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
