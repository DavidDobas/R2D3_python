# macOS Setup Guide

⚠️ **Important**: The Realman Robotic_Arm Python library does not include native macOS support. It only provides binaries for Linux and Windows.

## Problem

When you try to run the scripts directly on macOS, you'll get this error:
```
NameError: name 'libname' is not defined
```

This happens because the library doesn't check for macOS (`sys.platform == 'darwin'`) and doesn't include the required `.dylib` file.

## Solutions

### Option 1: Docker (Recommended) ✅

Use Docker to run the Linux version of the library:

#### Setup:
1. Install Docker Desktop for Mac: https://www.docker.com/products/docker-desktop

2. Build the Docker image:
```bash
docker-compose build
```

#### Usage:
Use the helper script to run commands:

```bash
# Read joint states
./run_docker.sh --read

# Set joint states
./run_docker.sh --set 0 0 0 0 0 0 0 --arm 1 --degrees

# Get arm info
./run_docker.sh --info --arm 1
```

Or run commands directly:
```bash
# Interactive shell in container
docker-compose run --rm arm-controller bash

# Then inside container:
python arm_cli.py --read
python arm_version.py --ip 192.168.1.18
```

### Option 2: Remote Linux Machine

Run the scripts on a Linux machine that can access your network:

1. Copy files to Linux machine:
```bash
scp -r . user@linux-machine:~/arm_controller/
```

2. SSH into the machine:
```bash
ssh user@linux-machine
cd ~/arm_controller
```

3. Install dependencies and run:
```bash
pip install -r requirements.txt
python arm_cli.py --read
```

### Option 3: Contact Realman for macOS Support

Reach out to Realman Robotics support to request:
- Native macOS library files (`.dylib`)
- Updated Python package with macOS support

**Contact**: https://www.realman-robotics.com/

### Option 4: Patch the Library (Not Recommended)

You could try to patch the library to use the Linux `.so` file on macOS, but this is unlikely to work due to binary incompatibility between Linux and macOS.

## Recommended Workflow

For development on macOS, use Docker:

1. **Development**: Edit Python files on macOS with your favorite IDE
2. **Testing**: Run scripts in Docker container with `./run_docker.sh`
3. **Production**: Deploy to a Linux machine or continue using Docker

## Docker Tips

### Build and run in one command:
```bash
docker-compose up --build
```

### Access container shell:
```bash
docker-compose run --rm arm-controller bash
```

### View logs:
```bash
docker-compose logs
```

### Clean up Docker resources:
```bash
docker-compose down
docker system prune -a
```

## Verifying Setup

Once you have Docker set up, test the connection:

```bash
# Test with your actual arm IPs
./run_docker.sh --arm1-ip 192.168.1.18 --arm2-ip 192.168.1.19 --read
```

If you see connection messages and joint states, you're good to go! 🎉

