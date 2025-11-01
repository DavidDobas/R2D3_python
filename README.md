# R2D3 Python - Realman Dual Arm Control & Dataset Collection

Control two Realman robotic arms and record datasets in LeRobot v3 format for robot learning.

## ⚠️ macOS Users

The Realman library **does not support macOS natively**. Use Docker:

```bash
# Install Docker Desktop first, then:
docker-compose build
./run_docker.sh python -m src.dataset_collection.record_dataset --dataset-name test --task "Test" --num-episodes 1
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Record LeRobot v3 Dataset

```bash
# Record a dataset with 5 episodes
python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place red cube" \
  --num-episodes 5

# On macOS (with Docker)
./run_docker.sh python -m src.dataset_collection.record_dataset \
  --dataset-name my_dataset \
  --task "Pick and place" \
  --num-episodes 5
```

**Usage:**
1. Run the command above
2. Wait for arms to connect
3. For each episode: perform the task, then press Enter
4. Dataset saved to `lerobot_data/my_dataset/`

### Test RealSense Camera

```bash
# List available cameras
python test_realsense.py --list

# Test camera (30 frames)
python test_realsense.py

# Save sample images
python test_realsense.py --save-images
```

## Dataset Format

Datasets are saved in LeRobot v3 format:

```
lerobot_data/my_dataset/
├── meta/
│   ├── info.json          # Dataset metadata
│   └── episodes.jsonl     # Episode metadata
├── data/
│   └── chunk-000/
│       └── episode_*.parquet  # Episode data (Parquet format)
└── videos/                # Reserved for camera support
```

**Data captured per frame:**
- Joint positions (7 DOF × 2 arms)
- End effector pose (position + orientation, both arms)
- Gripper states (both arms)
- Timestamps

## Configuration

Default robot IPs (configurable):
- **Left Arm**: 169.254.128.18:8080
- **Right Arm**: 169.254.128.19:8080

## Examples

### Record Dataset

```bash
# Basic recording
python -m src.dataset_collection.record_dataset \
  --dataset-name pick_place_v1 \
  --task "Pick cube and place in box" \
  --num-episodes 50

# High-speed (60 FPS)
python -m src.dataset_collection.record_dataset \
  --dataset-name fast_demo \
  --task "Fast movements" \
  --fps 60 \
  --num-episodes 20
```

### Load Dataset

```python
import pandas as pd

# Load episode
df = pd.read_parquet("lerobot_data/my_dataset/data/chunk-000/episode_000000.parquet")

# View data
print(df.columns)
print(df[['observation.state.left_arm', 'observation.state.right_arm']].head())
```

### Use Programmatically

```python
from src.dataset_collection.lerobot_recorder import LeRobotRecorder

recorder = LeRobotRecorder(dataset_name="my_data", fps=30)
recorder.connect()
recorder.start_episode(task="Pick and place")
recorder.start_recording()
# ... perform task ...
recorder.stop_recording()
recorder.end_episode()
recorder.save_dataset_info()
recorder.disconnect()
```

## Project Structure

```
src/
├── arm_control/
│   └── controller.py          # DualArmController class
└── dataset_collection/
    ├── episode.py             # Episode & Frame classes
    ├── lerobot_recorder.py    # Main recorder
    └── record_dataset.py      # CLI interface
```

## Troubleshooting

**"Failed to connect to arms"**
- Check IP addresses (default: 169.254.128.18/19)
- Verify arms are powered on
- Test network: `ping 169.254.128.18`

**"No RealSense devices found"**
- Check USB connection
- Try different USB port (USB 3.0 recommended)
- Install: `pip install pyrealsense2`

**macOS issues**
- Make sure Docker Desktop is running
- Rebuild: `docker-compose build`

## Requirements

- Python 3.9+
- Realman Robotic_Arm SDK
- pandas, pyarrow, numpy (for LeRobot format)
- opencv-python, pyrealsense2 (for camera support)

## Documentation

- [Realman Python API](https://develop.realman-robotics.com/en/robot4th/apipython/getStarted/)
- [LeRobot Documentation](https://huggingface.co/docs/lerobot)
