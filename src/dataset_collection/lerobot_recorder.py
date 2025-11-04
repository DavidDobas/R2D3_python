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
from typing import Dict, Any, List, Optional, Union
import numpy as np
import cv2

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
                 arm2_port: int = 8080,
                 cameras: Optional[List[Union[str, int]]] = None):
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
            cameras: List of camera sources (e.g., ["/dev/video0", "/dev/video2"] or [0, 1])
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
        
        # Robot interface - use separate instances for parallel reads
        self.robot = None  # Kept for compatibility
        self.robot_left = None  # Separate robot instance for left arm
        self.robot_right = None  # Separate robot instance for right arm
        self.arm1 = None
        self.arm2 = None
        
        # Camera support
        self.cameras = cameras or []
        self.cv2_caps = {}  # Camera captures: {camera_name: cv2.VideoCapture}
        self.camera_names = {}  # Map camera index/source to readable name
        
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
        print("Initializing robot interfaces...")
        
        # Create separate robot instances for true parallelism
        if self.arm1_ip:
            print(f"Connecting to Left Arm at {self.arm1_ip}:{self.arm1_port}...")
            self.robot_left = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
            self.arm1 = self.robot_left.rm_create_robot_arm(self.arm1_ip, self.arm1_port)
            if self.arm1 and self.arm1.id != -1:
                print(f"✓ Connected to Left Arm (ID: {self.arm1.id})")
            else:
                print("✗ Failed to connect to Left Arm")
                return False
        
        if self.arm2_ip:
            print(f"Connecting to Right Arm at {self.arm2_ip}:{self.arm2_port}...")
            self.robot_right = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
            self.arm2 = self.robot_right.rm_create_robot_arm(self.arm2_ip, self.arm2_port)
            if self.arm2 and self.arm2.id != -1:
                print(f"✓ Connected to Right Arm (ID: {self.arm2.id})")
            else:
                print("✗ Failed to connect to Right Arm")
                return False
        
        # Keep self.robot for backward compatibility (use robot_left if available)
        self.robot = self.robot_left if self.robot_left else self.robot_right
        
        # Connect cameras
        if self.cameras:
            if not self.connect_cameras():
                print("⚠ Warning: Some cameras failed to connect, continuing without them")
        
        return True
    
    def connect_cameras(self) -> bool:
        """Connect to all configured cameras."""
        if not self.cameras:
            return True
        
        print(f"\nConnecting to {len(self.cameras)} camera(s)...")
        all_connected = True
        
        for idx, camera_source in enumerate(self.cameras):
            # Generate camera name
            if isinstance(camera_source, str):
                camera_name = f"camera_{Path(camera_source).name}"  # e.g., "camera_video0"
                camera_display = camera_source
            else:
                camera_name = f"camera_{camera_source}"  # e.g., "camera_0"
                camera_display = str(camera_source)
            
            self.camera_names[camera_source] = camera_name
            
            # Try to open camera
            try:
                cap = cv2.VideoCapture(camera_source)
                if not cap.isOpened():
                    print(f"  ✗ Failed to open camera: {camera_display}")
                    all_connected = False
                    continue
                
                # Set resolution and FPS if possible
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                # Read one frame to verify
                ret, frame = cap.read()
                if not ret:
                    print(f"  ✗ Camera {camera_display} opened but cannot read frames")
                    cap.release()
                    all_connected = False
                    continue
                
                self.cv2_caps[camera_name] = cap
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps_actual = cap.get(cv2.CAP_PROP_FPS)
                print(f"  ✓ Connected to {camera_name}: {width}x{height} @ {fps_actual:.1f} FPS")
            
            except Exception as e:
                print(f"  ✗ Error connecting to camera {camera_display}: {e}")
                all_connected = False
        
        return all_connected
    
    def read_camera_frames(self) -> Dict[str, np.ndarray]:
        """
        Read frames from all connected cameras.
        
        Returns:
            Dictionary mapping camera names to frame arrays (BGR format)
        """
        frames = {}
        
        for camera_name, cap in self.cv2_caps.items():
            try:
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames[camera_name] = frame
                else:
                    # Frame read failed, store None to indicate error
                    frames[camera_name] = None
            except Exception as e:
                print(f"Warning: Error reading from {camera_name}: {e}")
                frames[camera_name] = None
        
        return frames
    
    def read_arm_observation(self, arm_name: str) -> Dict[str, Any]:
        """
        Read observation data from an arm.
        Uses dedicated robot instance for each arm for parallel execution.
        
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
            # Select the correct robot instance for this arm
            if arm_name == "left" and self.robot_left:
                robot = self.robot_left
            elif arm_name == "right" and self.robot_right:
                robot = self.robot_right
            else:
                robot = self.robot
            
            # Get current arm state
            result = robot.rm_get_current_arm_state()
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
            gripper_result = robot.rm_get_gripper_state()
            if gripper_result[0] == 0:
                gripper_data = gripper_result[1]
                observation["gripper_position"] = gripper_data.get("position", 0.0)
            else:
                observation["gripper_position"] = 0.0
                
        except Exception as e:
            observation["error"] = str(e)
        
        return observation
    
    def read_arm_observations_parallel(self) -> Dict[str, Dict[str, Any]]:
        """
        Read observations from both arms in parallel using threading.
        
        Returns:
            Dictionary with "left" and "right" arm observations
        """
        observations = {}
        errors = {}
        
        def read_arm(arm_name):
            """Read arm data and store in shared dict."""
            try:
                obs = self.read_arm_observation(arm_name)
                observations[arm_name] = obs
            except Exception as e:
                errors[arm_name] = str(e)
        
        # Create threads for each arm
        threads = []
        if self.arm1:
            threads.append(threading.Thread(target=read_arm, args=("left",)))
        if self.arm2:
            threads.append(threading.Thread(target=read_arm, args=("right",)))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Report any errors
        if errors:
            print(f"Warning: Errors reading arms: {errors}")
        
        return observations
    
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
        
        # Read observations from both arms in parallel
        observation = {}
        action = {}
        state = {}
        
        # Use parallel reading when both arms are present
        if self.arm1 and self.arm2:
            arm_observations = self.read_arm_observations_parallel()
            left_obs = arm_observations.get("left", {})
            right_obs = arm_observations.get("right", {})
        else:
            # Single arm or fallback to sequential
            arm_observations = {}
            if self.arm1:
                left_obs = self.read_arm_observation("left")
            else:
                left_obs = {}
            if self.arm2:
                right_obs = self.read_arm_observation("right")
            else:
                right_obs = {}
        
        # Extract data from observations
        if "qpos" in left_obs:
            observation["observation.state.left_arm"] = left_obs.get("qpos", [])
            observation["observation.state.left_eef_pos"] = left_obs.get("position", [])
            observation["observation.state.left_eef_euler"] = left_obs.get("orientation", [])
            observation["observation.state.left_gripper"] = left_obs.get("gripper_position", 0.0)
            
            action["action.left_arm"] = left_obs.get("qpos", [])
            action["action.left_gripper"] = left_obs.get("gripper_position", 0.0)
            
            state["state.left_arm"] = left_obs.get("qpos", [])
        
        if "qpos" in right_obs:
            observation["observation.state.right_arm"] = right_obs.get("qpos", [])
            observation["observation.state.right_eef_pos"] = right_obs.get("position", [])
            observation["observation.state.right_eef_euler"] = right_obs.get("orientation", [])
            observation["observation.state.right_gripper"] = right_obs.get("gripper_position", 0.0)
            
            action["action.right_arm"] = right_obs.get("qpos", [])
            action["action.right_gripper"] = right_obs.get("gripper_position", 0.0)
            
            state["state.right_arm"] = right_obs.get("qpos", [])
        
        # Read camera frames
        camera_frames = self.read_camera_frames()
        image_keys = []
        for camera_name, frame in camera_frames.items():
            if frame is not None:
                # Add image to observation with LeRobot naming convention
                image_key = f"observation.{camera_name}"
                observation[image_key] = frame
                image_keys.append(image_key)
        
        # Add frame to episode
        self.current_episode.add_frame(
            observation=observation,
            action=action,
            state=state,
            image_keys=image_keys
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
        # Exclude image keys (images are saved separately, not in Parquet)
        all_keys = set()
        for frame in episode.frames:
            for key in frame.observation.keys():
                # Skip image keys (numpy arrays)
                if not isinstance(frame.observation[key], np.ndarray):
                    all_keys.add(key)
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
            
            # Add all data (excluding images)
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
        """Disconnect from all arms and cameras."""
        print("\nDisconnecting from robotic arms...")
        if self.robot_left:
            self.robot_left.rm_delete_robot_arm()
        if self.robot_right:
            self.robot_right.rm_delete_robot_arm()
        
        # Close all cameras
        if self.cv2_caps:
            print("Closing cameras...")
            for camera_name, cap in self.cv2_caps.items():
                try:
                    cap.release()
                    print(f"  ✓ Closed {camera_name}")
                except Exception as e:
                    print(f"  ✗ Error closing {camera_name}: {e}")
            self.cv2_caps.clear()
            self.camera_names.clear()

