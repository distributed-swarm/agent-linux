## Linux / Raspberry Pi (No Docker)

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/Skullbaby/agent-linux.git
cd agent-linux
chmod +x install.sh
./install.sh

cp agent.env.template agent.env
nano agent.env

source .venv/bin/activate
python app.py

## systemd (optional)
This repo includes a template systemd unit at `systemd/agent-linux.service`.

Before using it on any Linux machine, you must edit:
- `User=...`
- `WorkingDirectory=...`
- `ExecStart=...`

These values depend on where you cloned the repo and which Linux user runs the agent.
