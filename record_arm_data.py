#!/usr/bin/env python3
"""
Data Recorder for Realman Robotic Arms
Records joint states, end effector pose, and gripper state at specified FPS.
Press Enter to stop recording and save data.
"""

import argparse
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from Robotic_Arm.rm_robot_interface import *


class ArmDataRecorder:
    """Records data from one or two robotic arms."""
    
    def __init__(self, arm1_ip=None, arm1_port=8080, arm2_ip=None, arm2_port=8080, fps=30):
        """
        Initialize the data recorder.
        
        Args:
            arm1_ip: IP address of arm 1 (None to skip)
            arm1_port: Port of arm 1
            arm2_ip: IP address of arm 2 (None to skip)
            arm2_port: Port of arm 2
            fps: Frames per second for recording
        """
        self.arm1_ip = arm1_ip
        self.arm1_port = arm1_port
        self.arm2_ip = arm2_ip
        self.arm2_port = arm2_port
        self.fps = fps
        self.interval = 1.0 / fps
        
        self.robot = None
        self.arm1 = None
        self.arm2 = None
        
        self.recording = False
        self.data = {
            "metadata": {
                "fps": fps,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "num_frames": 0
            },
            "frames": []
        }
        
    def connect(self):
        """Connect to the robotic arms."""
        print("Initializing robot interface...")
        self.robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
        
        if self.arm1_ip:
            print(f"Connecting to Arm 1 at {self.arm1_ip}:{self.arm1_port}...")
            self.arm1 = self.robot.rm_create_robot_arm(self.arm1_ip, self.arm1_port)
            if self.arm1 and self.arm1.id != -1:
                print(f"✓ Connected to Arm 1 (ID: {self.arm1.id})")
            else:
                print("✗ Failed to connect to Arm 1")
                return False
        
        if self.arm2_ip:
            print(f"Connecting to Arm 2 at {self.arm2_ip}:{self.arm2_port}...")
            self.arm2 = self.robot.rm_create_robot_arm(self.arm2_ip, self.arm2_port)
            if self.arm2 and self.arm2.id != -1:
                print(f"✓ Connected to Arm 2 (ID: {self.arm2.id})")
            else:
                print("✗ Failed to connect to Arm 2")
                return False
        
        return True
    
    def read_arm_data(self, arm_name):
        """
        Read all data from a specific arm.
        
        Args:
            arm_name: "arm1" or "arm2"
            
        Returns:
            dict: Dictionary containing joint states, pose, and gripper state
        """
        data = {
            "joint_states": None,
            "end_effector_pose": None,
            "gripper_state": None,
            "timestamp": time.time(),
            "error": None
        }
        
        try:
            # Get current arm state (includes joint angles and pose)
            result = self.robot.rm_get_current_arm_state()
            if result[0] == 0:
                arm_state = result[1]
                
                # Extract joint states
                data["joint_states"] = {
                    "angles_deg": list(arm_state.get("joint", [])),
                    "angles_rad": [angle * 3.14159 / 180 for angle in arm_state.get("joint", [])]
                }
                
                # Extract end effector pose
                pose = arm_state.get("pose", {})
                position = pose.get("position", {})
                euler = pose.get("euler", {})
                quaternion = pose.get("quaternion", {})
                
                data["end_effector_pose"] = {
                    "position": {
                        "x": position.get("x", 0.0),
                        "y": position.get("y", 0.0),
                        "z": position.get("z", 0.0)
                    },
                    "orientation_euler": {
                        "rx": euler.get("rx", 0.0),
                        "ry": euler.get("ry", 0.0),
                        "rz": euler.get("rz", 0.0)
                    },
                    "orientation_quaternion": {
                        "w": quaternion.get("w", 0.0),
                        "x": quaternion.get("x", 0.0),
                        "y": quaternion.get("y", 0.0),
                        "z": quaternion.get("z", 0.0)
                    }
                }
            else:
                data["error"] = f"Failed to get arm state, error code: {result[0]}"
            
            # Get gripper state
            gripper_result = self.robot.rm_get_gripper_state()
            if gripper_result[0] == 0:
                data["gripper_state"] = gripper_result[1]
            else:
                # Gripper might not be present, that's okay
                data["gripper_state"] = {"error": f"Error code: {gripper_result[0]}"}
                
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def record_frame(self):
        """Record a single frame of data from all connected arms."""
        frame = {
            "frame_number": len(self.data["frames"]),
            "timestamp": time.time()
        }
        
        if self.arm1:
            frame["arm1"] = self.read_arm_data("arm1")
        
        if self.arm2:
            frame["arm2"] = self.read_arm_data("arm2")
        
        self.data["frames"].append(frame)
        return frame
    
    def recording_loop(self):
        """Main recording loop that runs at specified FPS."""
        print(f"\n{'='*60}")
        print(f"Recording started at {self.fps} FPS")
        print(f"Press ENTER to stop recording")
        print(f"{'='*60}\n")
        
        self.data["metadata"]["start_time"] = datetime.now().isoformat()
        start_timestamp = time.time()
        frame_count = 0
        
        while self.recording:
            loop_start = time.time()
            
            # Record frame
            frame = self.record_frame()
            frame_count += 1
            
            # Print status every second
            elapsed = time.time() - start_timestamp
            if frame_count % self.fps == 0:
                print(f"Recording... {elapsed:.1f}s elapsed, {frame_count} frames recorded")
            
            # Sleep to maintain FPS
            elapsed_frame = time.time() - loop_start
            sleep_time = max(0, self.interval - elapsed_frame)
            time.sleep(sleep_time)
        
        # Update metadata
        self.data["metadata"]["end_time"] = datetime.now().isoformat()
        self.data["metadata"]["duration"] = time.time() - start_timestamp
        self.data["metadata"]["num_frames"] = frame_count
        
        print(f"\n{'='*60}")
        print(f"Recording stopped")
        print(f"Total frames: {frame_count}")
        print(f"Duration: {self.data['metadata']['duration']:.2f}s")
        print(f"Average FPS: {frame_count / self.data['metadata']['duration']:.2f}")
        print(f"{'='*60}\n")
    
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
    
    def save_data(self, output_file=None):
        """
        Save recorded data to a JSON file.
        
        Args:
            output_file: Path to output file. If None, auto-generates filename.
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"arm_recording_{timestamp}.json"
        
        output_path = Path(output_file)
        
        print(f"Saving data to {output_path}...")
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Data saved successfully ({file_size_mb:.2f} MB)")
        print(f"  Location: {output_path.absolute()}")
        
        return output_path
    
    def disconnect(self):
        """Disconnect from all arms."""
        print("\nDisconnecting from robotic arms...")
        if self.robot:
            self.robot.rm_delete_robot_arm()


def main():
    parser = argparse.ArgumentParser(
        description="Record robotic arm data at specified FPS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record from arm 1 at 30 FPS
  python record_arm_data.py --arm1-ip 192.168.1.18 --fps 30
  
  # Record from both arms at 60 FPS
  python record_arm_data.py --arm1-ip 192.168.1.18 --arm2-ip 192.168.1.19 --fps 60
  
  # Record with custom output file
  python record_arm_data.py --arm1-ip 192.168.1.18 --output my_recording.json
  
  # Record from arm 2 only
  python record_arm_data.py --arm2-ip 192.168.1.19 --fps 10

The script records:
  - Joint states (angles in degrees and radians)
  - End effector pose (position and orientation)
  - Gripper state
  
Press Enter to stop recording and save the data.
        """
    )
    
    # Connection arguments
    parser.add_argument("--arm1-ip", type=str,
                        help="IP address of arm 1")
    parser.add_argument("--arm1-port", type=int, default=8080,
                        help="Port of arm 1 (default: 8080)")
    parser.add_argument("--arm2-ip", type=str,
                        help="IP address of arm 2")
    parser.add_argument("--arm2-port", type=int, default=8080,
                        help="Port of arm 2 (default: 8080)")
    
    # Recording arguments
    parser.add_argument("--fps", type=int, default=30,
                        help="Frames per second for recording (default: 30)")
    parser.add_argument("--output", type=str,
                        help="Output file path (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Validate that at least one arm is specified
    if not args.arm1_ip and not args.arm2_ip:
        parser.error("At least one arm IP must be specified (--arm1-ip or --arm2-ip)")
    
    # Initialize recorder
    recorder = ArmDataRecorder(
        arm1_ip=args.arm1_ip,
        arm1_port=args.arm1_port,
        arm2_ip=args.arm2_ip,
        arm2_port=args.arm2_port,
        fps=args.fps
    )
    
    try:
        # Connect to arms
        if not recorder.connect():
            print("\n✗ Failed to connect to robotic arms")
            return 1
        
        print()  # Empty line for readability
        
        # Start recording
        recorder.start_recording()
        
        # Wait for Enter key
        input()
        
        # Stop recording
        recorder.stop_recording()
        
        # Save data
        recorder.save_data(args.output)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        recorder.stop_recording()
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        recorder.disconnect()
    
    print("\n✓ Done")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

