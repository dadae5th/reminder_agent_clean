#!/usr/bin/env bash
set -e
APP_DIR="/opt/reminder"
PY="/usr/bin/python3"
VENV="$APP_DIR/.venv"

sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip

sudo mkdir -p "$APP_DIR"
sudo chown -R $USER:$USER "$APP_DIR"

if [ ! -d "$VENV" ]; then $PY -m venv "$VENV"; fi
source "$VENV/bin/activate"
pip install --upgrade pip
if [ -f "$APP_DIR/requirements.txt" ]; then pip install -r "$APP_DIR/requirements.txt"; else pip install fastapi uvicorn APScheduler PyYAML; fi

python - <<'PY'
from db import init_schema
init_schema()
print("[OK] schema ensured")
PY

sudo tee /etc/systemd/system/reminder.service >/dev/null <<'EOF'
[Unit]
Description=Reminder webhook + scheduler
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/reminder
ExecStart=/opt/reminder/.venv/bin/python run_all.py --port 8510
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/dashboard.service >/dev/null <<'EOF'
[Unit]
Description=Reminder Streamlit Dashboard
After=network.target

[Service]
WorkingDirectory=/opt/reminder
ExecStart=/opt/reminder/.venv/bin/streamlit run dashboard_complete.py --server.port 8505 --server.address 0.0.0.0
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 8510/tcp || true
  sudo ufw allow 8505/tcp || true
fi

echo "Done. Enable services with:"
echo "  sudo systemctl enable --now reminder.service"
echo "  sudo systemctl enable --now dashboard.service  # if needed"
