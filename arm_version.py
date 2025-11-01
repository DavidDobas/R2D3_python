import argparse

from Robotic_Arm.rm_robot_interface import *

def get_arm_version(ip_adress:str, port:int):
    robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
    handle = robot.rm_create_robot_arm(ip_adress, port)
    print ("robotic arm ID:", handle.id)

    software_info = robot.rm_get_arm_software_info()
    if software_info[0] == 0:
        print("\n================== Arm Software Information ==================")
        print("Arm Model: ", software_info[1]['product_version'])
        print("Algorithm Library Version: ", software_info[1]['algorithm_info']['version'])
        print("Control Layer Software Version: ", software_info[1]['ctrl_info']['version'])
        print("Dynamics Version: ", software_info[1]['dynamic_info']['model_version'])
        print("Planning Layer Software Version: ", software_info[1]['plan_info']['version'])
        print("==============================================================\n")
    else:
        print("\nFailed to get arm software information, Error code: ", software_info[0], "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="169.254.128.18")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    get_arm_version(args.ip, args.port)