#!/usr/bin/env python3
"""
CLI for recording LeRobot v3 format datasets.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dataset_collection.lerobot_recorder import LeRobotRecorder


def main():
    parser = argparse.ArgumentParser(
        description="Record LeRobot v3.0 format datasets with Realman dual arms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record a dataset with 5 episodes
  python -m src.dataset_collection.record_dataset \\
    --dataset-name my_dataset \\
    --task "Pick and place" \\
    --num-episodes 5
  
  # Record with cameras
  python -m src.dataset_collection.record_dataset \\
    --dataset-name my_dataset \\
    --task "Pick and place" \\
    --num-episodes 5 \\
    --camera /dev/video0 --camera /dev/video2
  
  # Record with multiple cameras (mix of device paths and indices)
  python -m src.dataset_collection.record_dataset \\
    --dataset-name my_dataset \\
    --task "Pick and place" \\
    --num-episodes 5 \\
    --camera /dev/video0 --camera 1
  
  # Record with custom IPs and FPS
  python -m src.dataset_collection.record_dataset \\
    --dataset-name high_speed_demo \\
    --task "Fast movements" \\
    --fps 60 \\
    --arm1-ip 169.254.128.18 \\
    --arm2-ip 169.254.128.19

Usage:
  1. Start the script
  2. When prompted, perform the task
  3. Press Enter to stop recording the episode
  4. Repeat for remaining episodes
        """
    )
    
    # Dataset configuration
    parser.add_argument("--dataset-name", type=str, required=True,
                        help="Name of the dataset")
    parser.add_argument("--dataset-path", type=str, default="./lerobot_data",
                        help="Path to save dataset (default: ./lerobot_data)")
    parser.add_argument("--task", type=str, required=True,
                        help="Description of the task being performed")
    parser.add_argument("--num-episodes", type=int, default=1,
                        help="Number of episodes to record (default: 1)")
    
    # Robot configuration
    parser.add_argument("--robot-type", type=str, default="realman_dual_arm",
                        help="Robot type identifier (default: realman_dual_arm)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Recording FPS (default: 30)")
    parser.add_argument("--arm1-ip", type=str, default="169.254.128.18",
                        help="Left arm IP address (default: 169.254.128.18)")
    parser.add_argument("--arm1-port", type=int, default=8080,
                        help="Left arm port (default: 8080)")
    parser.add_argument("--arm2-ip", type=str, default="169.254.128.19",
                        help="Right arm IP address (default: 169.254.128.19)")
    parser.add_argument("--arm2-port", type=int, default=8080,
                        help="Right arm port (default: 8080)")
    
    # Camera configuration
    parser.add_argument("--camera", type=str, action="append",
                        help="Camera source (can be used multiple times). "
                             "Examples: /dev/video0, /dev/video2, or numeric index 0, 1, etc.")
    
    args = parser.parse_args()
    
    # Parse camera sources (convert numeric strings to int, keep paths as str)
    cameras = []
    if args.camera:
        for cam_source in args.camera:
            # Try to convert to int if it's numeric, otherwise keep as string
            try:
                cameras.append(int(cam_source))
            except ValueError:
                cameras.append(cam_source)
    
    # Initialize recorder
    print(f"\n{'='*70}")
    print(f"LeRobot v3.0 Dataset Recorder")
    print(f"{'='*70}")
    print(f"Dataset: {args.dataset_name}")
    print(f"Task: {args.task}")
    print(f"Episodes: {args.num_episodes}")
    print(f"FPS: {args.fps}")
    if cameras:
        print(f"Cameras: {cameras}")
    print(f"{'='*70}\n")
    
    recorder = LeRobotRecorder(
        dataset_name=args.dataset_name,
        dataset_path=args.dataset_path,
        robot_type=args.robot_type,
        fps=args.fps,
        arm1_ip=args.arm1_ip,
        arm1_port=args.arm1_port,
        arm2_ip=args.arm2_ip,
        arm2_port=args.arm2_port,
        cameras=cameras
    )
    
    try:
        # Connect to arms
        if not recorder.connect():
            print("\n✗ Failed to connect to robotic arms")
            return 1
        
        print()
        
        # Record episodes
        for episode_num in range(args.num_episodes):
            print(f"\n{'='*70}")
            print(f"Episode {episode_num + 1} / {args.num_episodes}")
            print(f"{'='*70}")
            
            # Start episode
            recorder.start_episode(task=args.task, task_index=0)
            
            # Start recording
            recorder.start_recording()
            
            # Wait for user to press Enter
            input("\nPerform the task. Press ENTER when done...\n")
            
            # Stop recording
            recorder.stop_recording()
            
            # End episode
            recorder.end_episode()
        
        # Save dataset metadata
        recorder.save_dataset_info()
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Dataset Recording Complete!")
        print(f"{'='*70}")
        print(f"Dataset: {args.dataset_name}")
        print(f"Location: {recorder.dataset_path}")
        print(f"Episodes: {len(recorder.episodes)}")
        total_frames = sum(len(ep.frames) for ep in recorder.episodes)
        print(f"Total frames: {total_frames}")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user")
        if recorder.current_episode:
            recorder.stop_recording()
            recorder.end_episode()
        recorder.save_dataset_info()
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        recorder.disconnect()
    
    print("✓ Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

