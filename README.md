cat > README.md << 'EOF'
# Agent Lite

Lightweight CPU-only agent for Neuro Fabric. Runs on endpoints (laptops, desktops, terminals) without Docker.

## Purpose

Connects idle CPU resources to the distributed compute fabric. No GPU required, no containers needed.

## Features

- CPU-only operations (map_classify, map_summarize)
- Runs as native Python process
- Same controller protocol as Docker agents
- Minimal resource footprint

## Installation
```bash
pip install -r requirements.txt
python app.py
```

## Configuration

Set environment variables:
- `CONTROLLER_URL`: Controller endpoint (default: http://localhost:8080)
- `AGENT_NAME`: This agent's identifier
- `DEVICE`: Always "cpu" for agent-lite
EOF
