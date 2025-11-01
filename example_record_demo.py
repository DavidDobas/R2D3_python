#!/usr/bin/env python3
"""
Example: Programmatically use the data recorder.
This shows how to use the recorder as a library in your own code.
"""

from record_arm_data import ArmDataRecorder
import time


def main():
    # Initialize recorder
    recorder = ArmDataRecorder(
        arm1_ip="192.168.1.18",
        arm1_port=8080,
        arm2_ip="192.168.1.19",  # Optional: set to None if only using one arm
        arm2_port=8080,
        fps=30
    )
    
    # Connect
    print("Connecting to arms...")
    if not recorder.connect():
        print("Failed to connect!")
        return
    
    print("Connected successfully!")
    
    # Start recording
    print("\nStarting recording for 5 seconds...")
    recorder.start_recording()
    
    # Record for 5 seconds
    time.sleep(5)
    
    # Stop recording
    print("Stopping recording...")
    recorder.stop_recording()
    
    # Save data
    output_file = recorder.save_data("demo_recording.json")
    print(f"\nRecording saved to: {output_file}")
    
    # Access the data programmatically
    print(f"\nRecorded {len(recorder.data['frames'])} frames")
    print(f"Duration: {recorder.data['metadata']['duration']:.2f} seconds")
    
    # Example: Get first frame's joint states
    if recorder.data['frames']:
        first_frame = recorder.data['frames'][0]
        if 'arm1' in first_frame:
            joints = first_frame['arm1']['joint_states']['angles_deg']
            print(f"\nFirst frame joint angles (Arm 1): {joints}")
    
    # Disconnect
    recorder.disconnect()
    print("\nDone!")


if __name__ == "__main__":
    main()

