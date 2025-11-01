# Realman Dual Arm Controller

Control and record data from two Realman robotic arms with easy-to-use CLI tools.

## ⚠️ macOS Users

The Realman library **does not support macOS natively**. 

- **Quick Start**: See [QUICKSTART_MACOS.md](QUICKSTART_MACOS.md) to get running in 5 minutes with Docker
- **Detailed Setup**: See [MACOS_SETUP.md](MACOS_SETUP.md) for all options and troubleshooting

## Features Overview

### 1. Arm Control (`arm_cli.py`)
- Connect to dual arms
- Read current joint states
- Set new joint positions
- Get arm information

### 2. Data Recording (`record_arm_data.py`)
- Record joint states at specified FPS (10-100 Hz)
- Capture end effector pose (position + orientation)
- Log gripper state
- Press Enter to stop and save
- See [RECORDING_GUIDE.md](RECORDING_GUIDE.md) for details

### 3. Data Analysis (`visualize_recording.py`)
- View recording summaries
- Inspect specific frames
- Export to CSV for further analysis

## Installation

1. Install the Realman Python SDK:
```bash
pip install Robotic_Arm
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Commands

**Read joint states from both arms:**
```bash
python arm_cli.py --read
```

**Read joint states from a specific arm:**
```bash
python arm_cli.py --read --arm 1
python arm_cli.py --read --arm 2
```

**Set joint states for arm 1 (angles in radians):**
```bash
python arm_cli.py --set 0.0 0.5 -0.5 0.0 1.57 0.0 0.0 --arm 1
```

**Set joint states for arm 2 (angles in degrees):**
```bash
python arm_cli.py --set 0 30 -30 0 90 0 0 --arm 2 --degrees
```

**Set joint states with custom speed:**
```bash
python arm_cli.py --set 0.0 0.5 -0.5 0.0 1.57 0.0 0.0 --arm 1 --speed 30
```

**Get arm information:**
```bash
python arm_cli.py --info --arm 1
```

### Connection Configuration

**Connect with custom IP addresses:**
```bash
python arm_cli.py --arm1-ip 169.254.128.20 --arm2-ip 169.254.128.21 --read
```

**Connect with custom ports:**
```bash
python arm_cli.py --arm1-port 8080 --arm2-port 8081 --read
```

### Command Line Options

```
Connection Options:
  --arm1-ip IP          IP address of arm 1 (default: 169.254.128.18)
  --arm1-port PORT      Port of arm 1 (default: 8080)
  --arm2-ip IP          IP address of arm 2 (default: 169.254.128.19)
  --arm2-port PORT      Port of arm 2 (default: 8080)

Commands:
  --read                Read joint states from arm(s)
  --set J1 J2 J3 J4 J5 J6 J7
                        Set joint states (7 values required)
  --info                Get arm software information
  
Control Options:
  --arm {1,2}           Specify which arm (required for --set)
  --degrees             Interpret --set angles as degrees (default: radians)
  --speed SPEED         Movement speed for --set (default: 20)
```

## Examples

### Example 1: Check both arms are connected and read their states
```bash
python arm_cli.py --read
```

Output:
```
Connecting to Arm 1 at 169.254.128.18:8080...
✓ Connected to Arm 1 (ID: 1)
Connecting to Arm 2 at 169.254.128.19:8080...
✓ Connected to Arm 2 (ID: 2)

=== Arm 1 Joint States ===
  Joint 1: 0.0000 rad (0.00°)
  Joint 2: 0.5236 rad (30.00°)
  Joint 3: -0.5236 rad (-30.00°)
  Joint 4: 0.0000 rad (0.00°)
  Joint 5: 1.5708 rad (90.00°)
  Joint 6: 0.0000 rad (0.00°)
  Joint 7: 0.0000 rad (0.00°)

=== Arm 2 Joint States ===
  Joint 1: 0.0000 rad (0.00°)
  ...
```

### Example 2: Move arm 1 to home position
```bash
python arm_cli.py --set 0 0 0 0 0 0 0 --arm 1 --degrees
```

### Example 3: Move arm 2 to a specific position
```bash
python arm_cli.py --set 0.0 0.785 -0.785 0.0 1.57 0.0 0.0 --arm 2 --speed 15
```

### Example 4: Get detailed information about both arms
```bash
python arm_cli.py --info
```

### Example 5: Record arm data at 30 FPS
```bash
# Using Docker on macOS
./run_docker.sh python record_arm_data.py --arm1-ip 169.254.128.18 --fps 30

# Press Enter to stop recording
# Output: arm_recording_YYYYMMDD_HHMMSS.json
```

### Example 6: Analyze recorded data
```bash
# View summary
python visualize_recording.py arm_recording_20251101_123045.json

# View specific frames
python visualize_recording.py recording.json --frame 0 --frame -1

# Export to CSV
python visualize_recording.py recording.json --export data.csv
```

## API Reference

The CLI wraps the Realman Python SDK. For more details, see:
- [Realman Python API Documentation](https://develop.realman-robotics.com/en/robot4th/apipython/getStarted/)

## Notes

- Joint angles can be specified in either radians (default) or degrees (with `--degrees` flag)
- The `--arm` parameter is required when using `--set` to specify which arm to control
- When using `--read` without `--arm`, both arms' states will be displayed
- Default IP addresses are 169.254.128.18 (arm 1) and 169.254.128.19 (arm 2)
- Make sure both arms are powered on and connected to the network before running commands

