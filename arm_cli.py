#!/usr/bin/env python3
"""
CLI for controlling two Realman robotic arms.
Supports reading and setting joint states for both arms.
"""

import argparse
import sys
from Robotic_Arm.rm_robot_interface import *


class DualArmController:
    def __init__(self, arm1_ip="192.168.1.18", arm1_port=8080, 
                 arm2_ip="192.168.1.19", arm2_port=8080):
        """Initialize connection to two robotic arms."""
        self.robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
        self.arm1_ip = arm1_ip
        self.arm1_port = arm1_port
        self.arm2_ip = arm2_ip
        self.arm2_port = arm2_port
        self.arm1 = None
        self.arm2 = None
        
    def connect(self):
        """Connect to both robotic arms."""
        print(f"Connecting to Arm 1 at {self.arm1_ip}:{self.arm1_port}...")
        self.arm1 = self.robot.rm_create_robot_arm(self.arm1_ip, self.arm1_port)
        if self.arm1:
            print(f"✓ Connected to Arm 1 (ID: {self.arm1.id})")
        else:
            print("✗ Failed to connect to Arm 1")
            return False
            
        print(f"Connecting to Arm 2 at {self.arm2_ip}:{self.arm2_port}...")
        self.arm2 = self.robot.rm_create_robot_arm(self.arm2_ip, self.arm2_port)
        if self.arm2:
            print(f"✓ Connected to Arm 2 (ID: {self.arm2.id})")
        else:
            print("✗ Failed to connect to Arm 2")
            return False
            
        return True
    
    def read_joint_states(self, arm_num=None):
        """
        Read joint states from one or both arms.
        
        Args:
            arm_num: 1 for arm1, 2 for arm2, None for both
        """
        if arm_num is None or arm_num == 1:
            result = self.robot.rm_get_current_arm_state()
            if result[0] == 0:
                joint_data = result[1]['joint']
                print("\n=== Arm 1 Joint States ===")
                for i, angle in enumerate(joint_data, 1):
                    print(f"  Joint {i}: {angle:.4f} rad ({angle * 180 / 3.14159:.2f}°)")
            else:
                print(f"\n✗ Failed to read Arm 1 joint states, Error code: {result[0]}")
        
        if arm_num is None or arm_num == 2:
            # Switch to arm 2 if needed
            if arm_num == 2 or arm_num is None:
                result = self.robot.rm_get_current_arm_state()
                if result[0] == 0:
                    joint_data = result[1]['joint']
                    print("\n=== Arm 2 Joint States ===")
                    for i, angle in enumerate(joint_data, 1):
                        print(f"  Joint {i}: {angle:.4f} rad ({angle * 180 / 3.14159:.2f}°)")
                else:
                    print(f"\n✗ Failed to read Arm 2 joint states, Error code: {result[0]}")
    
    def set_joint_states(self, joint_angles, arm_num, speed=20, block=True):
        """
        Set joint states for a specific arm.
        
        Args:
            joint_angles: List of joint angles in radians
            arm_num: 1 for arm1, 2 for arm2
            speed: Movement speed (default 20)
            block: Whether to block until movement is complete
        """
        if len(joint_angles) != 7:
            print(f"✗ Error: Expected 7 joint angles, got {len(joint_angles)}")
            return False
        
        arm_name = f"Arm {arm_num}"
        print(f"\nSetting joint states for {arm_name}...")
        print(f"Target angles (rad): {[f'{a:.4f}' for a in joint_angles]}")
        print(f"Target angles (deg): {[f'{a * 180 / 3.14159:.2f}' for a in joint_angles]}")
        
        # Use rm_movej to move to joint positions
        result = self.robot.rm_movej(joint_angles, speed, 0, block)
        
        if result == 0:
            print(f"✓ Successfully set joint states for {arm_name}")
            return True
        else:
            print(f"✗ Failed to set joint states for {arm_name}, Error code: {result}")
            return False
    
    def get_arm_info(self, arm_num):
        """Get software information for a specific arm."""
        print(f"\n=== Arm {arm_num} Information ===")
        software_info = self.robot.rm_get_arm_software_info()
        if software_info[0] == 0:
            print(f"  Model: {software_info[1]['product_version']}")
            print(f"  Algorithm Version: {software_info[1]['algorithm_info']['version']}")
            print(f"  Control Version: {software_info[1]['ctrl_info']['version']}")
            print(f"  Planning Version: {software_info[1]['plan_info']['version']}")
        else:
            print(f"  ✗ Failed to get arm information, Error code: {software_info[0]}")
    
    def disconnect(self):
        """Disconnect from both arms."""
        print("\nDisconnecting from robotic arms...")
        # The API handles disconnection automatically


def main():
    parser = argparse.ArgumentParser(
        description="CLI for controlling two Realman robotic arms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read joint states from both arms
  python arm_cli.py --read
  
  # Read joint states from arm 1 only
  python arm_cli.py --read --arm 1
  
  # Set joint states for arm 1 (7 angles in radians)
  python arm_cli.py --set 0.0 0.5 -0.5 0.0 1.57 0.0 0.0 --arm 1
  
  # Set joint states for arm 1 (7 angles in degrees)
  python arm_cli.py --set 0 30 -30 0 90 0 0 --arm 1 --degrees
  
  # Get arm information
  python arm_cli.py --info --arm 1
  
  # Connect with custom IP addresses
  python arm_cli.py --arm1-ip 192.168.1.20 --arm2-ip 192.168.1.21 --read
        """
    )
    
    # Connection arguments
    parser.add_argument("--arm1-ip", type=str, default="192.168.1.18",
                        help="IP address of arm 1 (default: 192.168.1.18)")
    parser.add_argument("--arm1-port", type=int, default=8080,
                        help="Port of arm 1 (default: 8080)")
    parser.add_argument("--arm2-ip", type=str, default="192.168.1.19",
                        help="IP address of arm 2 (default: 192.168.1.19)")
    parser.add_argument("--arm2-port", type=int, default=8080,
                        help="Port of arm 2 (default: 8080)")
    
    # Command arguments
    parser.add_argument("--read", action="store_true",
                        help="Read joint states")
    parser.add_argument("--set", nargs=7, type=float, metavar=('J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7'),
                        help="Set joint states (provide 7 values)")
    parser.add_argument("--info", action="store_true",
                        help="Get arm information")
    parser.add_argument("--arm", type=int, choices=[1, 2],
                        help="Specify which arm to control (1 or 2). If not specified, applies to both for --read")
    parser.add_argument("--degrees", action="store_true",
                        help="Interpret angles as degrees instead of radians (for --set command)")
    parser.add_argument("--speed", type=int, default=20,
                        help="Movement speed for --set command (default: 20)")
    
    args = parser.parse_args()
    
    # Check if at least one command is provided
    if not (args.read or args.set or args.info):
        parser.print_help()
        return 1
    
    # Check if --set requires --arm
    if args.set and not args.arm:
        print("✗ Error: --set command requires --arm to specify which arm to control")
        return 1
    
    # Initialize controller
    controller = DualArmController(
        arm1_ip=args.arm1_ip,
        arm1_port=args.arm1_port,
        arm2_ip=args.arm2_ip,
        arm2_port=args.arm2_port
    )
    
    # Connect to arms
    if not controller.connect():
        print("\n✗ Failed to connect to robotic arms")
        return 1
    
    print()  # Empty line for readability
    
    try:
        # Execute commands
        if args.info:
            controller.get_arm_info(args.arm if args.arm else 1)
            if not args.arm:
                controller.get_arm_info(2)
        
        if args.read:
            controller.read_joint_states(args.arm)
        
        if args.set:
            joint_angles = args.set
            # Convert from degrees to radians if needed
            if args.degrees:
                joint_angles = [angle * 3.14159 / 180 for angle in joint_angles]
            
            controller.set_joint_states(joint_angles, args.arm, speed=args.speed)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    finally:
        controller.disconnect()
    
    print("\n✓ Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

