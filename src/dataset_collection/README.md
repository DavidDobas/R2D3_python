# Dataset Collection Module

LeRobot v3 format dataset collection for Realman dual robotic arms with optional camera support.

## Overview

This module provides tools to record robot demonstrations in the industry-standard LeRobot v3.0 format, compatible with HuggingFace datasets and modern robot learning frameworks.

## Quick Start

```bash
# Record a dataset with 5 episodes
python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick red cube and place in blue box" \
  --num-episodes 5

# With cameras
python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place" \
  --num-episodes 5 \
  --camera /dev/video0 \
  --camera /dev/video2

# With Docker (macOS)
./run_docker.sh python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place" \
  --num-episodes 5
```

## Installation

```bash
pip install -r requirements.txt
```

Required packages:
- `Robotic_Arm` - Realman SDK
- `pandas` - Data manipulation
- `pyarrow` - Parquet file format
- `numpy` - Numerical operations
- `opencv-python` - Camera support

## Dataset Format

LeRobot v3.0 structure:

```
lerobot_data/my_dataset/
├── meta/
│   ├── info.json              # Dataset metadata
│   └── episodes.jsonl         # Episode list (one JSON per line)
├── data/
│   └── chunk-000/
│       ├── episode_000000.parquet  # Episode 0 data
│       ├── episode_000001.parquet  # Episode 1 data
│       └── ...
└── videos/                    # Reserved for video files
    └── chunk-000/
```

## Data Captured

### Robot State (Every Frame)

**Joint Positions:**
- `observation.state.left_arm` - Left arm joint angles (7 values, radians)
- `observation.state.right_arm` - Right arm joint angles (7 values, radians)

**End Effector Pose:**
- `observation.state.left_eef_pos` - Left end effector position [x, y, z] (meters)
- `observation.state.left_eef_euler` - Left end effector orientation [rx, ry, rz] (radians)
- `observation.state.right_eef_pos` - Right end effector position [x, y, z] (meters)
- `observation.state.right_eef_euler` - Right end effector orientation [rx, ry, rz] (radians)

**Gripper State:**
- `observation.state.left_gripper` - Left gripper position
- `observation.state.right_gripper` - Right gripper position

### Action Data (Every Frame)

Currently set to current state (for demonstration collection). In teleoperation, these would be commanded actions:
- `action.left_arm`, `action.right_arm`
- `action.left_gripper`, `action.right_gripper`

### Camera Images (Every Frame, if cameras enabled)

Images captured from all cameras:
- `observation.camera_video0` - BGR image array (H, W, 3)
- `observation.camera_video2` - BGR image array (H, W, 3)
- etc.

## Recording Workflow

### 1. Basic Recording

```bash
python -m src.dataset_collection.record_dataset \
  --dataset-name pick_place_demo \
  --task "Pick red cube and place in blue box" \
  --num-episodes 10
```

**Process:**
1. Script connects to both arms (and cameras if specified)
2. For each episode:
   - Episode starts automatically
   - Recording begins at specified FPS
   - **Perform the task** (teleoperate, demonstrate, etc.)
   - **Press Enter** when done
   - Episode data saved to Parquet
3. Dataset metadata saved to `meta/info.json`

### 2. With Cameras

```bash
# Single camera
python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place" \
  --num-episodes 5 \
  --camera /dev/video0

# Multiple cameras
python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place" \
  --num-episodes 5 \
  --camera /dev/video0 \
  --camera /dev/video2 \
  --camera 1
```

**Camera sources:**
- Device paths: `/dev/video0`, `/dev/video2`, etc.
- Numeric indices: `0`, `1`, `2`, etc.
- Mixed formats supported

### 3. Custom Configuration

```bash
python -m src.dataset_collection.record_dataset \
  --dataset-name custom_demo \
  --task "Fast manipulation" \
  --num-episodes 20 \
  --fps 60 \
  --arm1-ip 192.168.1.20 \
  --arm2-ip 192.168.1.21 \
  --camera /dev/video0
```

## Loading and Analyzing Datasets

### Load Episode Data

```python
import pandas as pd

# Load a single episode
df = pd.read_parquet("lerobot_data/my_dataset/data/chunk-000/episode_000000.parquet")

# View structure
print(df.columns.tolist())
print(df.head())
print(f"Frames: {len(df)}")
print(f"Duration: {df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]:.2f}s")
```

### Access Robot State

```python
# Get joint positions for all frames
left_arm = df['observation.state.left_arm'].values
right_arm = df['observation.state.right_arm'].values

# Get end effector positions
left_eef_pos = df['observation.state.left_eef_pos'].values
right_eef_pos = df['observation.state.right_eef_pos'].values

# Individual frame
frame_10 = df.iloc[10]
joint_angles = frame_10['observation.state.left_arm']  # tuple of 7 values
```

### Visualize Trajectories

```python
import matplotlib.pyplot as plt

# Plot joint 1 angle over time
times = df['timestamp'].values - df['timestamp'].values[0]
joint1 = [x[0] for x in df['observation.state.left_arm']]
plt.plot(times, joint1)
plt.xlabel('Time (s)')
plt.ylabel('Joint 1 Angle (rad)')
plt.title('Left Arm Joint 1 Trajectory')
plt.show()

# Plot 3D end effector path
from mpl_toolkits.mplot3d import Axes3D
pos = df['observation.state.left_eef_pos'].values
x = [p[0] for p in pos]
y = [p[1] for p in pos]
z = [p[2] for p in pos]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(x, y, z)
ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')
plt.title('End Effector Path')
plt.show()
```

### Access Camera Images

Camera images are stored in the episode frames as numpy arrays. To load them:

```python
from src.dataset_collection.lerobot_recorder import LeRobotRecorder
import pickle

# Load episode (images stored in Frame objects)
episode = pickle.load(open("episode_pickle.pkl", "rb"))  # If you save full episodes
# Or load from frame data...

# Access frame 10's camera image
frame_10 = episode.frames[10]
if 'observation.camera_video0' in frame_10.observation:
    image = frame_10.observation['observation.camera_video0']  # numpy array (H, W, 3)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.show()
```

## Programmatic Usage

```python
from src.dataset_collection.lerobot_recorder import LeRobotRecorder

# Initialize
recorder = LeRobotRecorder(
    dataset_name="my_dataset",
    cameras=["/dev/video0", "/dev/video2"],
    fps=30
)

# Connect
recorder.connect()

# Record episodes
for i in range(5):
    recorder.start_episode(task="Pick and place", task_index=0)
    recorder.start_recording()
    
    # Wait for user or execute automated task
    input(f"Episode {i+1}: Perform task, press Enter...")
    
    recorder.stop_recording()
    recorder.end_episode()

# Save metadata
recorder.save_dataset_info()
recorder.disconnect()
```

## Camera Configuration

### Supported Camera Types

- **USB cameras** (via `/dev/video*`)
- **Built-in cameras** (via index `0`, `1`, etc.)
- **IP cameras** (via RTSP/HTTP URL)

### Resolution and FPS

Default settings:
- Resolution: 640x480
- FPS: Matches recording FPS

Cameras automatically attempt to match the recording FPS. Actual FPS depends on camera hardware.

### Troubleshooting Cameras

**"Failed to open camera"**
- Check camera is connected: `ls /dev/video*`
- Try different index: `--camera 0` vs `--camera /dev/video0`
- Check permissions: may need to run with `sudo` or add user to `video` group

**"Cannot read frames"**
- Camera may be in use by another application
- Try lower resolution/FPS
- Check USB connection

**Low FPS**
- Lower camera resolution
- Reduce number of cameras
- Use USB 3.0 ports
- Lower recording FPS

## Performance Considerations

### Recording FPS

**Stable FPS estimates:**
- Single arm: 30-50 FPS
- Dual arms: 15-25 FPS
- With cameras: 10-20 FPS

**Bottlenecks:**
1. Network latency for robot API calls (~10-20ms each)
2. Camera frame capture (~5-10ms per camera)
3. Data processing overhead

### Optimization Tips

1. **Lower FPS** for longer recordings (10-20 FPS is often sufficient)
2. **Reduce camera count** or resolution if FPS drops
3. **Use wired ethernet** for stable network connections
4. **Monitor actual FPS** using printed statistics
5. **Close unnecessary applications** to free CPU/bandwidth

### File Sizes

Approximate sizes for 1 minute at 30 FPS:
- Robot state only (2 arms): ~5 MB
- With 1 camera: ~15-20 MB
- With 2 cameras: ~25-30 MB

Parquet compression provides ~60% size reduction vs uncompressed.

## Episode Management

### Episode Metadata

Each episode's metadata is stored in `meta/episodes.jsonl`:

```json
{
  "episode_index": 0,
  "task": "Pick and place",
  "task_index": 0,
  "length": 300,
  "start_time": "2025-11-01T12:00:00",
  "end_time": "2025-11-01T12:00:10",
  "duration": 10.0
}
```

### Dataset Metadata

`meta/info.json` contains dataset-level information:

```json
{
  "name": "my_dataset",
  "robot_type": "realman_dual_arm",
  "fps": 30,
  "created_at": "2025-11-01T12:00:00",
  "version": "3.0",
  "num_episodes": 50,
  "total_frames": 15000
}
```

## Advanced Usage

### Custom Episode Processing

```python
from src.dataset_collection.episode import Episode

# Create custom episode
episode = Episode(
    episode_index=0,
    task="Custom task",
    task_index=0
)

# Add frames manually
episode.add_frame(
    observation={"state": [...]},
    action={"action": [...]},
    state={"state": [...]},
    image_keys=["observation.camera_video0"]
)

episode.finalize()
print(episode.get_stats())
```

### Batch Processing

```python
import pandas as pd
from pathlib import Path

# Load all episodes from a dataset
data_dir = Path("lerobot_data/my_dataset/data/chunk-000")
episodes = []

for parquet_file in sorted(data_dir.glob("episode_*.parquet")):
    df = pd.read_parquet(parquet_file)
    episodes.append(df)
    print(f"Loaded {parquet_file.name}: {len(df)} frames")

# Combine all episodes
all_data = pd.concat(episodes, ignore_index=True)
print(f"Total frames: {len(all_data)}")
```

## Best Practices

### Recording

1. **Consistent demonstrations**: Try to perform tasks similarly each episode
2. **Clear task boundaries**: Each episode should be a complete task attempt
3. **Smooth movements**: Avoid jerky or erratic motions
4. **Sufficient episodes**: 50+ episodes recommended for learning
5. **Appropriate length**: 5-30 seconds per episode works well

### Data Quality

1. **Test cameras first**: Use `python test_realsense.py --list` to verify
2. **Check recording stats**: Monitor actual FPS during recording
3. **Review sample data**: Load and visualize a few episodes
4. **Validate consistency**: Check that all cameras produce valid frames
5. **Clean environment**: Ensure good lighting and minimal clutter

### File Management

1. **Organize by task**: Use descriptive dataset names
2. **Version datasets**: Include version numbers (e.g., `pick_place_v1`)
3. **Archive old data**: Move completed datasets to storage
4. **Keep metadata**: Don't delete `meta/` folder
5. **Regular backups**: Parquet files are efficient to backup

## Troubleshooting

### Common Issues

**"Failed to connect to arms"**
```bash
# Check IPs
ping 169.254.128.18
ping 169.254.128.19

# Verify arms are powered on
# Check network connection
```

**"Failed to open camera"**
```bash
# List available cameras
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened()); cap.release()"
```

**"Low actual FPS"**
- Reduce target FPS
- Check network latency
- Lower camera resolution
- Reduce number of cameras

**"ImportError: pandas/pyarrow not found"**
```bash
pip install pandas pyarrow
```

**"RuntimeError: No active episode"**
- Make sure to call `start_episode()` before `start_recording()`
- Check that episode wasn't finalized already

## Integration with Robot Learning

### PyTorch

```python
import pandas as pd
import torch
from torch.utils.data import Dataset

class RobotDataset(Dataset):
    def __init__(self, episode_path):
        self.data = pd.read_parquet(episode_path)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        state = torch.tensor([
            *row['observation.state.left_arm'],
            *row['observation.state.right_arm']
        ], dtype=torch.float32)
        action = torch.tensor([
            *row['action.left_arm'],
            *row['action.right_arm']
        ], dtype=torch.float32)
        return state, action

# Create dataloader
dataset = RobotDataset("lerobot_data/my_dataset/data/chunk-000/episode_000000.parquet")
dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
```

### HuggingFace Datasets

```python
from datasets import Dataset

# Load Parquet
df = pd.read_parquet("lerobot_data/my_dataset/data/chunk-000/episode_000000.parquet")

# Convert to HuggingFace Dataset
hf_dataset = Dataset.from_pandas(df)

# Use with Transformers, etc.
```

## API Reference

### LeRobotRecorder

Main recorder class for dataset collection.

```python
recorder = LeRobotRecorder(
    dataset_name: str,
    dataset_path: str = "./lerobot_data",
    robot_type: str = "realman_dual_arm",
    fps: int = 30,
    arm1_ip: str = "169.254.128.18",
    arm2_ip: str = "169.254.128.19",
    cameras: Optional[List[Union[str, int]]] = None
)
```

**Methods:**
- `connect()` - Connect to arms and cameras
- `start_episode(task, task_index)` - Begin new episode
- `start_recording()` - Begin recording loop
- `stop_recording()` - Stop recording loop
- `end_episode()` - Finalize and save episode
- `save_dataset_info()` - Save dataset metadata
- `disconnect()` - Clean disconnect

### Episode

Episode management and frame storage.

```python
episode = Episode(
    episode_index: int,
    task: str,
    task_index: int = 0
)
```

**Methods:**
- `add_frame(observation, action, state, image_keys)` - Add frame
- `finalize()` - Complete episode
- `get_stats()` - Get statistics dict

## Next Steps

1. **Record datasets**: Start collecting demonstrations
2. **Analyze data**: Visualize and inspect recordings
3. **Train models**: Use with your robot learning framework
4. **Share data**: Push to HuggingFace Hub
5. **Iterate**: Improve based on model performance

## Resources

- [LeRobot Documentation](https://huggingface.co/docs/lerobot)
- [LeRobot Dataset v3.0 Spec](https://huggingface.co/docs/lerobot/en/lerobot-dataset-v3)
- [Realman API Docs](https://develop.realman-robotics.com)
- [Main Project README](../README.md)

