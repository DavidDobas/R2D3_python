# Quick Start Guide for macOS

Since the Realman library doesn't support macOS natively, here's the fastest way to get started using Docker.

## Prerequisites

1. Install Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop
2. Start Docker Desktop
3. Make sure your robotic arms are powered on and connected to your network

## Step 1: Build the Docker Image

```bash
cd /Users/daviddobas/dev/robotics/R2D3_python
docker-compose build
```

This takes a few minutes the first time. Subsequent builds are faster.

## Step 2: Test Connection

Replace the IP addresses with your actual arm IPs:

```bash
./run_docker.sh --arm1-ip 169.254.128.18 --arm2-ip 169.254.128.19 --read
```

Expected output:
```
Connecting to Arm 1 at 169.254.128.18:8080...
✓ Connected to Arm 1 (ID: 1)
Connecting to Arm 2 at 169.254.128.19:8080...
✓ Connected to Arm 2 (ID: 2)

=== Arm 1 Joint States ===
  Joint 1: 0.0000 rad (0.00°)
  Joint 2: ...
```

## Step 3: Common Commands

### Read joint states:
```bash
./run_docker.sh --read
```

### Read from specific arm:
```bash
./run_docker.sh --read --arm 1
```

### Set joint positions (in degrees):
```bash
./run_docker.sh --set 0 30 -30 0 90 0 0 --arm 1 --degrees
```

### Get arm information:
```bash
./run_docker.sh --info
```

### Run the version check script:
```bash
docker-compose run --rm arm-controller python arm_version.py --ip 169.254.128.18
```

## Troubleshooting

### "Cannot connect to the Docker daemon"
- Make sure Docker Desktop is running
- Check the Docker icon in your menu bar

### "Connection refused" or timeout errors
- Verify the arm IP addresses are correct
- Ping the arms: `ping 169.254.128.18`
- Make sure you're on the same network as the arms
- Check if any firewall is blocking the connection

### "Error response from daemon: Conflict"
- Container name is already in use
- Run: `docker-compose down`
- Then retry your command

### Slow performance
- Docker on macOS uses a VM, so there's some overhead
- For production, consider deploying to a native Linux machine

## Interactive Development

Want to experiment interactively?

```bash
# Start a shell in the container
docker-compose run --rm arm-controller bash

# Now you're inside the container, try:
python
>>> from arm_cli import DualArmController
>>> controller = DualArmController()
>>> controller.connect()
>>> controller.read_joint_states()
```

## Next Steps

- See [README.md](README.md) for all CLI options
- See [MACOS_SETUP.md](MACOS_SETUP.md) for alternative solutions
- Check out [demo_usage.py](demo_usage.py) for programmatic examples

## Tips

- The `./run_docker.sh` script is just a wrapper around `docker-compose`
- You can edit the Python files on macOS and they'll be used in the container
- Volume mounting means changes are reflected immediately
- Use `--help` to see all available options: `./run_docker.sh --help`

