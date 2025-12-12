"""
Screenshot and video management utilities.
Handles saving, organizing, and retrieving automation artifacts.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import shutil

from config import Config


class ScreenshotManager:
    """Manage screenshots and videos from automation runs"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.task_dir = Config.SCREENSHOTS_DIR / task_id
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
        self.video_dir = Config.VIDEOS_DIR / task_id
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        self.screenshot_paths: List[Path] = []
        self.video_path: Optional[Path] = None
    
    def get_screenshot_path(self, step_name: str) -> Path:
        """Generate a path for a screenshot"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{step_name}.png"
        path = self.task_dir / filename
        self.screenshot_paths.append(path)
        return path
    
    def get_video_path(self) -> Path:
        """Generate a path for a video recording"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.webm"
        path = self.video_dir / filename
        self.video_path = path
        return path
    
    def save_screenshot(self, screenshot_bytes: bytes, step_name: str) -> Path:
        """Save a screenshot from bytes"""
        path = self.get_screenshot_path(step_name)
        with open(path, 'wb') as f:
            f.write(screenshot_bytes)
        return path
    
    def get_all_screenshots(self) -> List[Path]:
        """Get all screenshots for this task"""
        return sorted(self.task_dir.glob("*.png"))
    
    def get_video(self) -> Optional[Path]:
        """Get the video file if it exists"""
        videos = list(self.video_dir.glob("*.webm"))
        return videos[0] if videos else None
    
    def cleanup_old_artifacts(self, days: int = 7):
        """Remove artifacts older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for artifact_dir in [Config.SCREENSHOTS_DIR, Config.VIDEOS_DIR]:
            for task_folder in artifact_dir.iterdir():
                if not task_folder.is_dir():
                    continue
                
                # Check folder modification time
                if task_folder.stat().st_mtime < cutoff:
                    try:
                        shutil.rmtree(task_folder)
                        print(f"Cleaned up old artifacts: {task_folder.name}")
                    except Exception as e:
                        print(f"Could not remove {task_folder}: {e}")
    
    def get_task_directory(self) -> Path:
        """Get the task directory path"""
        return self.task_dir
    
    @staticmethod
    def list_all_tasks() -> List[str]:
        """List all task IDs with artifacts"""
        tasks = set()
        
        for artifact_dir in [Config.SCREENSHOTS_DIR, Config.VIDEOS_DIR]:
            if artifact_dir.exists():
                for task_folder in artifact_dir.iterdir():
                    if task_folder.is_dir():
                        tasks.add(task_folder.name)
        
        return sorted(list(tasks), reverse=True)
    
    @staticmethod
    def get_task_artifacts(task_id: str) -> dict:
        """Get all artifacts for a specific task"""
        screenshots = []
        videos = []
        
        screenshot_dir = Config.SCREENSHOTS_DIR / task_id
        if screenshot_dir.exists():
            screenshots = sorted(screenshot_dir.glob("*.png"))
        
        video_dir = Config.VIDEOS_DIR / task_id
        if video_dir.exists():
            videos = sorted(video_dir.glob("*.webm"))
        
        return {
            "task_id": task_id,
            "screenshots": [str(s) for s in screenshots],
            "videos": [str(v) for v in videos],
            "total_screenshots": len(screenshots),
            "total_videos": len(videos)
        }
