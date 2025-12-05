import threading
import time
import requests
import psutil
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

CONTROLLER_URL = "http://localhost:8080"
AGENT_NAME = "agent-lite-win-1"   # match what app.py registers as


class AgentTray:
    def __init__(self):
        self.icon = Icon("agent-lite", self._create_icon(), "Agent Lite")
        self.running = True
        self.status_text = "Starting..."
        self._start_background_updater()

        self.icon.menu = Menu(
            MenuItem("Pause agent", self.pause_agent),
            MenuItem("Resume agent", self.resume_agent),
            MenuItem("Exit tray", self.exit_tray)
        )

    def _create_icon(self, size=64, color_fg=(0, 255, 0), color_bg=(0, 0, 0)):
        image = Image.new("RGB", (size, size), color_bg)
        d = ImageDraw.Draw(image)
        margin = 10
        d.ellipse((margin, margin, size - margin, size - margin), fill=color_fg)
        return image

    def _start_background_updater(self):
        t = threading.Thread(target=self._update_loop, daemon=True)
        t.start()

    def _update_loop(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=0.5)

                # pull agent stats from controller
                resp = requests.get(f"{CONTROLLER_URL}/agents", timeout=2)
                data = resp.json()
                agent_info = data.get(AGENT_NAME, {})

                state = agent_info.get("state", "unknown")
                metrics = agent_info.get("metrics", {})
                tasks_completed = metrics.get("tasks_completed", 0)

                self.status_text = (
                    f"{AGENT_NAME} [{state}]  "
                    f"CPU: {cpu:.0f}%  "
                    f"Completed: {tasks_completed}"
                )

                # update tooltip
                self.icon.title = self.status_text

            except Exception:
                self.status_text = "Agent / controller unreachable"
                self.icon.title = self.status_text

            time.sleep(3)

    def pause_agent(self, icon, item):
        try:
            r = requests.post(
                f"{CONTROLLER_URL}/agents/{AGENT_NAME}/quarantine",
                json={"reason": "paused_from_tray"},
                timeout=3,
            )
            # if you have a different pause endpoint, adjust this
        except Exception:
            pass

    def resume_agent(self, icon, item):
        try:
            r = requests.post(
                f"{CONTROLLER_URL}/agents/{AGENT_NAME}/restore",
                json={},
                timeout=3,
            )
        except Exception:
            pass

    def exit_tray(self, icon, item):
        self.running = False
        self.icon.stop()

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    tray = AgentTray()
    tray.run()
