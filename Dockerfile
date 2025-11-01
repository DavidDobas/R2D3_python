FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY arm_cli.py .
COPY arm_version.py .
COPY demo_usage.py .
COPY record_arm_data.py .
COPY visualize_recording.py .

# Set environment
ENV PYTHONUNBUFFERED=1

# Default command shows help
CMD ["python", "arm_cli.py", "--help"]

