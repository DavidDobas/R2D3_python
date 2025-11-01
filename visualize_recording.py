#!/usr/bin/env python3
"""
Visualize and analyze recorded arm data.
"""

import argparse
import json
from pathlib import Path
import sys


def print_summary(data):
    """Print a summary of the recording."""
    metadata = data.get("metadata", {})
    frames = data.get("frames", [])
    
    print("\n" + "="*60)
    print("RECORDING SUMMARY")
    print("="*60)
    print(f"Start Time:    {metadata.get('start_time', 'N/A')}")
    print(f"End Time:      {metadata.get('end_time', 'N/A')}")
    print(f"Duration:      {metadata.get('duration', 0):.2f} seconds")
    print(f"Total Frames:  {metadata.get('num_frames', 0)}")
    print(f"Target FPS:    {metadata.get('fps', 'N/A')}")
    
    if metadata.get('duration', 0) > 0:
        actual_fps = metadata.get('num_frames', 0) / metadata.get('duration', 1)
        print(f"Actual FPS:    {actual_fps:.2f}")
    
    # Check which arms were recorded
    if frames:
        first_frame = frames[0]
        arms_present = []
        if 'arm1' in first_frame:
            arms_present.append("Arm 1")
        if 'arm2' in first_frame:
            arms_present.append("Arm 2")
        print(f"Arms Recorded: {', '.join(arms_present)}")
    
    print("="*60 + "\n")


def print_frame_details(data, frame_num=0):
    """Print details of a specific frame."""
    frames = data.get("frames", [])
    
    if frame_num < 0 or frame_num >= len(frames):
        print(f"✗ Frame {frame_num} not found (total frames: {len(frames)})")
        return
    
    frame = frames[frame_num]
    
    print("\n" + "="*60)
    print(f"FRAME {frame_num} DETAILS")
    print("="*60)
    print(f"Timestamp: {frame.get('timestamp', 'N/A')}")
    
    # Print Arm 1 data
    if 'arm1' in frame:
        print("\n--- ARM 1 ---")
        print_arm_data(frame['arm1'])
    
    # Print Arm 2 data
    if 'arm2' in frame:
        print("\n--- ARM 2 ---")
        print_arm_data(frame['arm2'])
    
    print("="*60 + "\n")


def print_arm_data(arm_data):
    """Print data for a single arm."""
    if arm_data.get('error'):
        print(f"  ✗ Error: {arm_data['error']}")
        return
    
    # Joint states
    joint_states = arm_data.get('joint_states', {})
    if joint_states:
        print("  Joint States (degrees):")
        angles = joint_states.get('angles_deg', [])
        for i, angle in enumerate(angles, 1):
            print(f"    Joint {i}: {angle:8.3f}°")
    
    # End effector pose
    pose = arm_data.get('end_effector_pose', {})
    if pose:
        position = pose.get('position', {})
        euler = pose.get('orientation_euler', {})
        
        print("\n  End Effector Position (meters):")
        print(f"    X: {position.get('x', 0):8.4f}")
        print(f"    Y: {position.get('y', 0):8.4f}")
        print(f"    Z: {position.get('z', 0):8.4f}")
        
        print("\n  End Effector Orientation (radians):")
        print(f"    RX: {euler.get('rx', 0):8.4f}")
        print(f"    RY: {euler.get('ry', 0):8.4f}")
        print(f"    RZ: {euler.get('rz', 0):8.4f}")
    
    # Gripper state
    gripper = arm_data.get('gripper_state', {})
    if gripper and not gripper.get('error'):
        print("\n  Gripper State:")
        for key, value in gripper.items():
            if key != 'error':
                print(f"    {key}: {value}")
    elif gripper.get('error'):
        print(f"\n  Gripper: Not available")


def export_to_csv(data, output_file):
    """Export recording data to CSV format."""
    import csv
    
    frames = data.get("frames", [])
    if not frames:
        print("✗ No frames to export")
        return
    
    output_path = Path(output_file)
    
    with open(output_path, 'w', newline='') as csvfile:
        # Determine headers based on first frame
        headers = ['frame_number', 'timestamp']
        first_frame = frames[0]
        
        if 'arm1' in first_frame:
            headers.extend([
                'arm1_j1', 'arm1_j2', 'arm1_j3', 'arm1_j4', 'arm1_j5', 'arm1_j6', 'arm1_j7',
                'arm1_x', 'arm1_y', 'arm1_z', 'arm1_rx', 'arm1_ry', 'arm1_rz'
            ])
        
        if 'arm2' in first_frame:
            headers.extend([
                'arm2_j1', 'arm2_j2', 'arm2_j3', 'arm2_j4', 'arm2_j5', 'arm2_j6', 'arm2_j7',
                'arm2_x', 'arm2_y', 'arm2_z', 'arm2_rx', 'arm2_ry', 'arm2_rz'
            ])
        
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for frame in frames:
            row = {
                'frame_number': frame['frame_number'],
                'timestamp': frame['timestamp']
            }
            
            # Add arm1 data
            if 'arm1' in frame:
                arm1 = frame['arm1']
                joints = arm1.get('joint_states', {}).get('angles_deg', [])
                for i, angle in enumerate(joints, 1):
                    row[f'arm1_j{i}'] = angle
                
                pose = arm1.get('end_effector_pose', {})
                pos = pose.get('position', {})
                euler = pose.get('orientation_euler', {})
                row.update({
                    'arm1_x': pos.get('x', 0),
                    'arm1_y': pos.get('y', 0),
                    'arm1_z': pos.get('z', 0),
                    'arm1_rx': euler.get('rx', 0),
                    'arm1_ry': euler.get('ry', 0),
                    'arm1_rz': euler.get('rz', 0)
                })
            
            # Add arm2 data
            if 'arm2' in frame:
                arm2 = frame['arm2']
                joints = arm2.get('joint_states', {}).get('angles_deg', [])
                for i, angle in enumerate(joints, 1):
                    row[f'arm2_j{i}'] = angle
                
                pose = arm2.get('end_effector_pose', {})
                pos = pose.get('position', {})
                euler = pose.get('orientation_euler', {})
                row.update({
                    'arm2_x': pos.get('x', 0),
                    'arm2_y': pos.get('y', 0),
                    'arm2_z': pos.get('z', 0),
                    'arm2_rx': euler.get('rx', 0),
                    'arm2_ry': euler.get('ry', 0),
                    'arm2_rz': euler.get('rz', 0)
                })
            
            writer.writerow(row)
    
    print(f"✓ Data exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize and analyze recorded arm data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show summary of recording
  python visualize_recording.py recording.json
  
  # Show details of frame 0
  python visualize_recording.py recording.json --frame 0
  
  # Show details of first and last frames
  python visualize_recording.py recording.json --frame 0 --frame -1
  
  # Export to CSV
  python visualize_recording.py recording.json --export data.csv
        """
    )
    
    parser.add_argument("input_file", type=str,
                        help="Path to recorded JSON file")
    parser.add_argument("--frame", type=int, action='append',
                        help="Show details of specific frame (can be used multiple times)")
    parser.add_argument("--export", type=str,
                        help="Export data to CSV file")
    
    args = parser.parse_args()
    
    # Load data
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"✗ Error: File not found: {input_path}")
        return 1
    
    print(f"Loading data from {input_path}...")
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Print summary
    print_summary(data)
    
    # Print frame details if requested
    if args.frame:
        frames = data.get("frames", [])
        for frame_num in args.frame:
            # Handle negative indices
            if frame_num < 0:
                frame_num = len(frames) + frame_num
            print_frame_details(data, frame_num)
    
    # Export to CSV if requested
    if args.export:
        export_to_csv(data, args.export)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

