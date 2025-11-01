# Data Recording Guide

This guide explains how to record and analyze data from your Realman robotic arms.

## Quick Start

### Record from one arm at 30 FPS:
```bash
# On macOS (using Docker)
./run_docker.sh python record_arm_data.py --arm1-ip 192.168.1.18 --fps 30

# On Linux (native)
python record_arm_data.py --arm1-ip 192.168.1.18 --fps 30
```

**Press Enter to stop recording and save the data.**

## What Gets Recorded

For each frame, the script captures:

### 1. Joint States
- All 7 joint angles in both degrees and radians
- Example: `[0.0, 30.0, -45.0, 0.0, 90.0, 0.0, 0.0]`

### 2. End Effector Pose
- **Position** (x, y, z) in meters
- **Orientation** as Euler angles (rx, ry, rz) in radians
- **Orientation** as Quaternion (w, x, y, z)

### 3. Gripper State
- Current gripper status and position
- If no gripper is attached, this field will contain an error note

### 4. Metadata
- Recording FPS
- Start/end timestamps
- Total duration
- Number of frames

## Recording Options

### Basic Usage

```bash
# Record from arm 1
python record_arm_data.py --arm1-ip 192.168.1.18

# Record from arm 2
python record_arm_data.py --arm2-ip 192.168.1.19

# Record from both arms simultaneously
python record_arm_data.py --arm1-ip 192.168.1.18 --arm2-ip 192.168.1.19
```

### FPS Settings

```bash
# Low FPS (10 Hz) - for slow movements
python record_arm_data.py --arm1-ip 192.168.1.18 --fps 10

# Standard FPS (30 Hz) - default
python record_arm_data.py --arm1-ip 192.168.1.18 --fps 30

# High FPS (60 Hz) - for fast movements
python record_arm_data.py --arm1-ip 192.168.1.18 --fps 60

# Very high FPS (100 Hz) - maximum detail
python record_arm_data.py --arm1-ip 192.168.1.18 --fps 100
```

**Note**: Higher FPS creates larger files and may affect timing accuracy. The actual FPS achieved depends on network latency and system performance.

### Custom Output File

```bash
# Specify output filename
python record_arm_data.py --arm1-ip 192.168.1.18 --output my_recording.json

# Default: auto-generated filename with timestamp
# Example: arm_recording_20251101_123045.json
```

## Output Format

The data is saved as JSON with this structure:

```json
{
  "metadata": {
    "fps": 30,
    "start_time": "2025-11-01T12:30:45.123456",
    "end_time": "2025-11-01T12:31:15.987654",
    "duration": 30.864198,
    "num_frames": 925
  },
  "frames": [
    {
      "frame_number": 0,
      "timestamp": 1730469045.123456,
      "arm1": {
        "timestamp": 1730469045.123789,
        "joint_states": {
          "angles_deg": [0.0, 30.0, -30.0, 0.0, 90.0, 0.0, 0.0],
          "angles_rad": [0.0, 0.5236, -0.5236, 0.0, 1.5708, 0.0, 0.0]
        },
        "end_effector_pose": {
          "position": {"x": 0.3, "y": 0.0, "z": 0.4},
          "orientation_euler": {"rx": 3.141, "ry": 0.0, "rz": 0.0},
          "orientation_quaternion": {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
        },
        "gripper_state": {
          "position": 0.0,
          "status": "idle"
        },
        "error": null
      }
    }
  ]
}
```

## Analyzing Recorded Data

### View Summary

```bash
python visualize_recording.py arm_recording_20251101_123045.json
```

Output:
```
============================================================
RECORDING SUMMARY
============================================================
Start Time:    2025-11-01T12:30:45.123456
End Time:      2025-11-01T12:31:15.987654
Duration:      30.86 seconds
Total Frames:  925
Target FPS:    30
Actual FPS:    29.98
Arms Recorded: Arm 1
============================================================
```

### View Specific Frames

```bash
# View first frame (frame 0)
python visualize_recording.py recording.json --frame 0

# View last frame
python visualize_recording.py recording.json --frame -1

# View multiple frames
python visualize_recording.py recording.json --frame 0 --frame 100 --frame -1
```

### Export to CSV

```bash
python visualize_recording.py recording.json --export data.csv
```

The CSV format is easier to import into Excel, MATLAB, or Python (pandas) for analysis:

```csv
frame_number,timestamp,arm1_j1,arm1_j2,arm1_j3,arm1_j4,arm1_j5,arm1_j6,arm1_j7,arm1_x,arm1_y,arm1_z,arm1_rx,arm1_ry,arm1_rz
0,1730469045.123,0.0,30.0,-30.0,0.0,90.0,0.0,0.0,0.3,0.0,0.4,3.141,0.0,0.0
1,1730469045.156,0.0,30.1,-30.1,0.0,90.1,0.0,0.0,0.301,0.0,0.401,3.141,0.0,0.0
...
```

## Using with Docker (macOS)

Since the library doesn't support macOS natively, use Docker:

### Record data:
```bash
./run_docker.sh python record_arm_data.py --arm1-ip 192.168.1.18 --fps 30
```

The recorded file will be saved in the current directory and accessible from macOS.

### Visualize data (can run natively on macOS):
```bash
python3 visualize_recording.py arm_recording_20251101_123045.json
```

**Note**: The visualization script doesn't need the Realman library, so it works natively on macOS!

## Tips and Best Practices

### 1. Choose the Right FPS
- **10 Hz**: Manual teleoperation, slow movements
- **30 Hz**: Standard recording, most use cases
- **60 Hz**: Fast movements, precise timing needed
- **100 Hz**: Research applications, very fast movements

### 2. File Sizes
Approximate file sizes for 1 minute of recording:
- 10 FPS, 1 arm: ~1.5 MB
- 30 FPS, 1 arm: ~4.5 MB
- 60 FPS, 1 arm: ~9 MB
- 30 FPS, 2 arms: ~9 MB

### 3. Network Considerations
- Use wired ethernet for best reliability
- WiFi may introduce latency and jitter
- Higher FPS is more sensitive to network issues

### 4. Stopping Recording
- Press Enter cleanly to ensure data is saved
- Don't force-quit (Ctrl+C) if possible
- The script handles interruptions gracefully but Enter is preferred

### 5. Storage
- Recordings are append-only in memory until saved
- Long recordings use more RAM
- For very long recordings (>10 minutes), consider lower FPS

## Data Analysis Examples

### Using Python (pandas)

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv('data.csv')

# Plot joint 1 position over time
plt.plot(df['timestamp'] - df['timestamp'][0], df['arm1_j1'])
plt.xlabel('Time (s)')
plt.ylabel('Joint 1 Angle (deg)')
plt.title('Joint 1 Trajectory')
plt.show()

# Plot end effector path in 3D
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(df['arm1_x'], df['arm1_y'], df['arm1_z'])
ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')
plt.show()
```

### Using JSON directly

```python
import json

with open('arm_recording_20251101_123045.json', 'r') as f:
    data = json.load(f)

# Get all joint 1 angles from arm 1
joint1_angles = [
    frame['arm1']['joint_states']['angles_deg'][0]
    for frame in data['frames']
    if 'arm1' in frame
]

# Get all end effector positions
positions = [
    (
        frame['arm1']['end_effector_pose']['position']['x'],
        frame['arm1']['end_effector_pose']['position']['y'],
        frame['arm1']['end_effector_pose']['position']['z']
    )
    for frame in data['frames']
    if 'arm1' in frame
]
```

## Troubleshooting

### "Failed to get arm state"
- Check network connection
- Verify arm IP address
- Ensure arm is powered on and initialized

### Actual FPS much lower than target
- Network latency too high
- Try wired connection
- Lower target FPS
- Check CPU usage

### Large file sizes
- Reduce FPS
- Record for shorter duration
- Consider compression (gzip) for storage

### Script hangs or freezes
- Check arm is responsive (try ping)
- Restart arm controller
- Check for firewall issues

## Next Steps

After recording data, you can:
1. Replay movements using the joint states
2. Analyze trajectories for smoothness
3. Train machine learning models
4. Compare left vs right arm coordination
5. Extract features for task analysis

For more information, see the main README.md

