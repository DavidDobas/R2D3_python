#!/usr/bin/env python3
"""
LeRobot v3 Dataset Recorder for Realman Dual Arms
Records data in LeRobot v3.0 format with Parquet files and video support.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from Robotic_Arm.rm_robot_interface import *
from .episode import Episode, Frame


class LeRobotRecorder:
    """
    Records robot data in LeRobot v3.0 format.
    
    LeRobot v3.0 format structure:
    dataset/
    ├── meta/
    │   ├── info.json                # Dataset-level metadata
    │   └── episodes.jsonl           # Episode metadata (one JSON per line)
    ├── data/
    │   └── chunk-000/
    │       └── episode_000000.parquet  # Episode data
    └── videos/
        └── chunk-000/
            ├── episode_000000_observation.image.mp4
            └── episode_000000_observation.wrist_image.mp4
    """
    
    def __init__(self, 
                 dataset_name: str,
                 dataset_path: str = "./lerobot_data",
                 robot_type: str = "realman_dual_arm",
                 fps: int = 30,
                 arm1_ip: str = "169.254.128.18",
                 arm1_port: int = 8080,
                 arm2_ip: str = "169.254.128.19",
                 arm2_port: int = 8080):
        """
        Initialize the LeRobot recorder.
        
        Args:
            dataset_name: Name of the dataset
            dataset_path: Path where dataset will be saved
            robot_type: Type of robot being recorded
            fps: Recording frames per second
            arm1_ip: IP address of left arm
            arm1_port: Port of left arm
            arm2_ip: IP address of right arm
            arm2_port: Port of right arm
        """
        self.dataset_name = dataset_name
        self.dataset_path = Path(dataset_path) / dataset_name
        self.robot_type = robot_type
        self.fps = fps
        self.interval = 1.0 / fps
        
        # Arm connection info
        self.arm1_ip = arm1_ip
        self.arm1_port = arm1_port
        self.arm2_ip = arm2_ip
        self.arm2_port = arm2_port
        
        # Robot interface
        self.robot = None
        self.arm1 = None
        self.arm2 = None
        
        # Recording state
        self.recording = False
        self.current_episode: Optional[Episode] = None
        self.episodes: List[Episode] = []
        
        # Dataset metadata
        self.dataset_metadata = {
            "name": dataset_name,
            "robot_type": robot_type,
            "fps": fps,
            "created_at": datetime.now().isoformat(),
            "version": "3.0",
            "codebase_version": "0.1.0"
        }
        
        # Create directory structure
        self._setup_directories()
    
    def _setup_directories(self):
        """Create the LeRobot v3 directory structure."""
        self.dataset_path.mkdir(parents=True, exist_ok=True)
        (self.dataset_path / "meta").mkdir(exist_ok=True)
        (self.dataset_path / "data" / "chunk-000").mkdir(parents=True, exist_ok=True)
        (self.dataset_path / "videos" / "chunk-000").mkdir(parents=True, exist_ok=True)
    
    def connect(self) -> bool:
        """Connect to the robotic arms."""
        print("Initializing robot interface...")
        self.robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
        
        if self.arm1_ip:
            print(f"Connecting to Left Arm at {self.arm1_ip}:{self.arm1_port}...")
            self.arm1 = self.robot.rm_create_robot_arm(self.arm1_ip, self.arm1_port)
            if self.arm1 and self.arm1.id != -1:
                print(f"✓ Connected to Left Arm (ID: {self.arm1.id})")
            else:
                print("✗ Failed to connect to Left Arm")
                return False
        
        if self.arm2_ip:
            print(f"Connecting to Right Arm at {self.arm2_ip}:{self.arm2_port}...")
            self.arm2 = self.robot.rm_create_robot_arm(self.arm2_ip, self.arm2_port)
            if self.arm2 and self.arm2.id != -1:
                print(f"✓ Connected to Right Arm (ID: {self.arm2.id})")
            else:
                print("✗ Failed to connect to Right Arm")
                return False
        
        return True
    
    def read_arm_observation(self, arm_name: str) -> Dict[str, Any]:
        """
        Read observation data from an arm.
        
        Args:
            arm_name: "left" or "right"
            
        Returns:
            Dictionary containing observation data
        """
        observation = {
            "timestamp": time.time(),
            "arm": arm_name
        }
        
        try:
            # Get current arm state
            result = self.robot.rm_get_current_arm_state()
            if result[0] == 0:
                arm_state = result[1]
                
                # Joint positions (state.qpos)
                joint_angles_rad = [angle * np.pi / 180 for angle in arm_state.get("joint", [])]
                observation["qpos"] = joint_angles_rad
                
                # End effector pose
                # Note: pose is a flat list [x, y, z, rx, ry, rz] from rm_current_arm_state_t.to_dictionary()
                pose_list = arm_state.get("pose", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                
                # Ensure we have 6 elements
                if len(pose_list) >= 6:
                    observation["position"] = pose_list[0:3]  # [x, y, z] in meters
                    observation["orientation"] = pose_list[3:6]  # [rx, ry, rz] in radians
                else:
                    # Fallback if pose format is unexpected
                    observation["position"] = [0.0, 0.0, 0.0]
                    observation["orientation"] = [0.0, 0.0, 0.0]
            
            # Get gripper state
            gripper_result = self.robot.rm_get_gripper_state()
            if gripper_result[0] == 0:
                gripper_data = gripper_result[1]
                observation["gripper_position"] = gripper_data.get("position", 0.0)
            else:
                observation["gripper_position"] = 0.0
                
        except Exception as e:
            observation["error"] = str(e)
        
        return observation
    
    def start_episode(self, task: str, task_index: int = 0) -> Episode:
        """
        Start a new episode.
        
        Args:
            task: Description of the task
            task_index: Index of the task type
            
        Returns:
            The created Episode object
        """
        episode_index = len(self.episodes)
        self.current_episode = Episode(
            episode_index=episode_index,
            task=task,
            task_index=task_index
        )
        
        print(f"\n{'='*60}")
        print(f"Started Episode {episode_index}: {task}")
        print(f"{'='*60}\n")
        
        return self.current_episode
    
    def record_frame(self):
        """Record a single frame to the current episode."""
        if not self.current_episode:
            raise RuntimeError("No active episode. Call start_episode() first.")
        
        # Read observations from both arms
        observation = {}
        action = {}
        state = {}
        
        if self.arm1:
            left_obs = self.read_arm_observation("left")
            observation["observation.state.left_arm"] = left_obs.get("qpos", [])
            observation["observation.state.left_eef_pos"] = left_obs.get("position", [])
            observation["observation.state.left_eef_euler"] = left_obs.get("orientation", [])
            observation["observation.state.left_gripper"] = left_obs.get("gripper_position", 0.0)
            
            # For now, action = current state (will be replaced with actual commands in teleoperation)
            action["action.left_arm"] = left_obs.get("qpos", [])
            action["action.left_gripper"] = left_obs.get("gripper_position", 0.0)
            
            state["state.left_arm"] = left_obs.get("qpos", [])
        
        if self.arm2:
            right_obs = self.read_arm_observation("right")
            observation["observation.state.right_arm"] = right_obs.get("qpos", [])
            observation["observation.state.right_eef_pos"] = right_obs.get("position", [])
            observation["observation.state.right_eef_euler"] = right_obs.get("orientation", [])
            observation["observation.state.right_gripper"] = right_obs.get("gripper_position", 0.0)
            
            action["action.right_arm"] = right_obs.get("qpos", [])
            action["action.right_gripper"] = right_obs.get("gripper_position", 0.0)
            
            state["state.right_arm"] = right_obs.get("qpos", [])
        
        # Add frame to episode
        self.current_episode.add_frame(
            observation=observation,
            action=action,
            state=state
        )
    
    def recording_loop(self):
        """Main recording loop running at specified FPS."""
        frame_count = 0
        start_time = time.time()
        
        while self.recording:
            loop_start = time.time()
            
            try:
                self.record_frame()
                frame_count += 1
                
                # Print status every second
                if frame_count % self.fps == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed if elapsed > 0 else 0
                    print(f"Recording... {elapsed:.1f}s | {frame_count} frames | {actual_fps:.1f} FPS")
            
            except Exception as e:
                print(f"Error recording frame: {e}")
            
            # Sleep to maintain FPS
            elapsed_frame = time.time() - loop_start
            sleep_time = max(0, self.interval - elapsed_frame)
            time.sleep(sleep_time)
    
    def start_recording(self):
        """Start recording in a separate thread."""
        self.recording = True
        self.recording_thread = threading.Thread(target=self.recording_loop, daemon=True)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording."""
        self.recording = False
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=2.0)
    
    def end_episode(self):
        """End the current episode and save it."""
        if not self.current_episode:
            print("No active episode to end.")
            return
        
        self.current_episode.finalize()
        self.episodes.append(self.current_episode)
        
        # Print episode stats
        stats = self.current_episode.get_stats()
        print(f"\n{'='*60}")
        print(f"Episode {stats['episode_index']} Complete")
        print(f"  Task: {stats['task']}")
        print(f"  Frames: {stats['num_frames']}")
        print(f"  Duration: {stats['duration']:.2f}s")
        print(f"  Average FPS: {stats['fps']:.2f}")
        print(f"{'='*60}\n")
        
        # Save episode data
        self._save_episode(self.current_episode)
        
        self.current_episode = None
    
    def _save_episode(self, episode: Episode):
        """Save episode data in LeRobot v3 format."""
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            print("Warning: pandas and pyarrow required for Parquet export.")
            print("Install with: pip install pandas pyarrow")
            # Fallback to JSON
            self._save_episode_json(episode)
            return
        
        # Prepare data for Parquet
        data_dict = {
            "episode_index": [],
            "frame_index": [],
            "timestamp": []
        }
        
        # Collect all unique keys from observations, actions, states
        all_keys = set()
        for frame in episode.frames:
            all_keys.update(frame.observation.keys())
            all_keys.update(frame.action.keys())
            all_keys.update(frame.state.keys())
        
        # Initialize columns
        for key in all_keys:
            data_dict[key] = []
        
        # Fill data
        for frame in episode.frames:
            data_dict["episode_index"].append(episode.episode_index)
            data_dict["frame_index"].append(frame.index)
            data_dict["timestamp"].append(frame.timestamp)
            
            # Add all data
            for key in all_keys:
                value = None
                if key in frame.observation:
                    value = frame.observation[key]
                elif key in frame.action:
                    value = frame.action[key]
                elif key in frame.state:
                    value = frame.state[key]
                
                # Convert lists to tuples for Parquet
                if isinstance(value, list):
                    value = tuple(value)
                
                data_dict[key].append(value)
        
        # Create DataFrame
        df = pd.DataFrame(data_dict)
        
        # Save as Parquet
        output_file = self.dataset_path / "data" / "chunk-000" / f"episode_{episode.episode_index:06d}.parquet"
        df.to_parquet(output_file, engine='pyarrow', compression='snappy')
        print(f"✓ Saved episode data: {output_file}")
        
        # Save episode metadata to episodes.jsonl
        metadata_file = self.dataset_path / "meta" / "episodes.jsonl"
        with open(metadata_file, 'a') as f:
            episode_meta = {
                "episode_index": episode.episode_index,
                "task": episode.task,
                "task_index": episode.task_index,
                "length": len(episode.frames),
                "start_time": episode.start_time,
                "end_time": episode.end_time,
                "duration": episode.duration
            }
            f.write(json.dumps(episode_meta) + "\n")
    
    def _save_episode_json(self, episode: Episode):
        """Fallback: Save episode as JSON."""
        output_file = self.dataset_path / "data" / "chunk-000" / f"episode_{episode.episode_index:06d}.json"
        with open(output_file, 'w') as f:
            json.dump(episode.to_dict(), f, indent=2)
        print(f"✓ Saved episode data (JSON): {output_file}")
    
    def save_dataset_info(self):
        """Save dataset-level metadata."""
        self.dataset_metadata["num_episodes"] = len(self.episodes)
        self.dataset_metadata["total_frames"] = sum(len(ep.frames) for ep in self.episodes)
        
        info_file = self.dataset_path / "meta" / "info.json"
        with open(info_file, 'w') as f:
            json.dump(self.dataset_metadata, f, indent=2)
        
        print(f"✓ Saved dataset info: {info_file}")
    
    def disconnect(self):
        """Disconnect from all arms."""
        print("\nDisconnecting from robotic arms...")
        if self.robot:
            self.robot.rm_delete_robot_arm()

