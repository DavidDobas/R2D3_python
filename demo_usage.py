#!/usr/bin/env python3
"""
Demo script showing how to use the DualArmController programmatically.
"""

from arm_cli import DualArmController
import time


def main():
    # Initialize controller with custom IPs if needed
    controller = DualArmController(
        arm1_ip="169.254.128.18",
        arm1_port=8080,
        arm2_ip="169.254.128.19",
        arm2_port=8080
    )
    
    # Connect to both arms
    print("Connecting to robotic arms...")
    if not controller.connect():
        print("Failed to connect. Exiting.")
        return
    
    print("\n" + "="*50)
    print("Demo: Reading and Setting Joint States")
    print("="*50)
    
    # 1. Read initial joint states
    print("\n[1] Reading initial joint states...")
    controller.read_joint_states()
    
    # 2. Get arm information
    print("\n[2] Getting arm information...")
    controller.get_arm_info(1)
    controller.get_arm_info(2)
    
    # 3. Example: Move arm 1 to a predefined position
    print("\n[3] Moving Arm 1 to position (example)...")
    # Note: Uncomment to actually execute movement
    # joint_angles_arm1 = [0.0, 0.5, -0.5, 0.0, 1.57, 0.0, 0.0]
    # controller.set_joint_states(joint_angles_arm1, arm_num=1, speed=20)
    # time.sleep(2)
    
    # 4. Example: Move arm 2 to a different position
    print("\n[4] Moving Arm 2 to position (example)...")
    # Note: Uncomment to actually execute movement
    # joint_angles_arm2 = [0.0, -0.5, 0.5, 0.0, 1.57, 0.0, 0.0]
    # controller.set_joint_states(joint_angles_arm2, arm_num=2, speed=20)
    # time.sleep(2)
    
    # 5. Read final joint states
    print("\n[5] Reading final joint states...")
    controller.read_joint_states()
    
    # Disconnect
    controller.disconnect()
    print("\nDemo complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")

