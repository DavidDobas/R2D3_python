"""Episode management for LeRobot v3 datasets."""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Frame:
    """Represents a single frame of data in an episode."""
    timestamp: float
    index: int
    
    # Observation data
    observation: Dict[str, Any] = field(default_factory=dict)
    
    # Action data (what the robot did)
    action: Dict[str, Any] = field(default_factory=dict)
    
    # State data (robot state)
    state: Dict[str, Any] = field(default_factory=dict)
    
    # Optional image data (stored separately in videos)
    image_keys: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to dictionary format."""
        return {
            "timestamp": self.timestamp,
            "index": self.index,
            "observation": self.observation,
            "action": self.action,
            "state": self.state,
            "image_keys": self.image_keys
        }


@dataclass
class Episode:
    """
    Represents an episode in LeRobot v3 format.
    
    An episode is a sequence of frames from start to end of a task.
    """
    episode_index: int
    task: str
    task_index: int = 0
    
    # Metadata
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: float = 0.0
    
    # Frames
    frames: List[Frame] = field(default_factory=list)
    
    # Episode-specific info
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize episode with start time."""
        if self.start_time is None:
            self.start_time = datetime.now().isoformat()
    
    def add_frame(self, observation: Dict[str, Any], action: Dict[str, Any], 
                  state: Dict[str, Any], image_keys: Optional[List[str]] = None):
        """
        Add a frame to the episode.
        
        Args:
            observation: Observation data (joint states, end effector pose, etc.)
            action: Action data (commanded positions, velocities, etc.)
            state: Robot state (current position, velocity, etc.)
            image_keys: List of image/camera names for this frame
        """
        frame = Frame(
            timestamp=time.time(),
            index=len(self.frames),
            observation=observation,
            action=action,
            state=state,
            image_keys=image_keys or []
        )
        self.frames.append(frame)
    
    def finalize(self):
        """Finalize the episode by setting end time and duration."""
        self.end_time = datetime.now().isoformat()
        if self.frames:
            start_timestamp = self.frames[0].timestamp
            end_timestamp = self.frames[-1].timestamp
            self.duration = end_timestamp - start_timestamp
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the episode."""
        return {
            "episode_index": self.episode_index,
            "task": self.task,
            "num_frames": len(self.frames),
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "fps": len(self.frames) / self.duration if self.duration > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary format."""
        return {
            "episode_index": self.episode_index,
            "task": self.task,
            "task_index": self.task_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "num_frames": len(self.frames),
            "metadata": self.metadata,
            "frames": [frame.to_dict() for frame in self.frames]
        }

