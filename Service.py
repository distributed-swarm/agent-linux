"""
Agent-Lite Windows Service wrapper (headless, admin-managed)

- Runs app.main() as a Windows service
- No UI, no user interaction
- Loads config from %ProgramData%\\AgentLite\\agent.env (preferred)
- Logs to %ProgramData%\\AgentLite\\service.log
"""

import os
import sys
import time
import threading
import logging
from pathlib import Path

import win32serviceutil
import win32service
import win32event
import servicemanager


# =========================
#   PATHS / CONFIG
# =========================

SERVICE_NAME = "AgentLite"

PROGRAM_DATA_DIR = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "AgentLite"
PROGRAM_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = PROGRAM_DATA_DIR / "service.log"
ENV_FILE_PRIMARY = PROGRAM_DATA_DIR / "agent.env"

# Optional dev fallback (not required for prod)
ENV_FILE_FALLBACK = Path.home() / "AppData" / "Local" / "AgentLite" / "agent.env"


# =========================
#   LOGGING
# =========================

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("AgentLiteService")


def _load_env_file(path: Path) -> bool:
    """
    Load simple KEY=VALUE pairs into os.environ, without overriding existing keys.
    Returns True if loaded.
    """
    try:
        if not path.exists():
            return False

        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

        logger.info("Loaded env from: %s", str(path))
        return True
    except Exception:
        logger.exception("Failed to load env file: %s", str(path))
        return False


def load_configuration():
    """
    Load config from ProgramData env file first, then optional fallback.
    """
    loaded = _load_env_file(ENV_FILE_PRIMARY)
    if not loaded:
        _load_env_file(ENV_FILE_FALLBACK)


# =========================
#   SERVICE CLASS
# =========================

class AgentLiteService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = "Agent-Lite Task Processor"
    _svc_description_ = "Headless lightweight task agent for Neuro-Fabric (admin-managed)"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = False
        self.agent_thread = None

    def SvcStop(self):
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        self.is_running = False
        win32event.SetEvent(self.stop_event)

        if self.agent_thread and self.agent_thread.is_alive():
            logger.info("Waiting for agent thread to terminate...")
            self.agent_thread.join(timeout=15)

        logger.info("Service stopped")

    def SvcDoRun(self):
        logger.info("=" * 60)
        logger.info("Agent-Lite Service Starting")
        logger.info("=" * 60)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        self.is_running = True
        self.main()

    def main(self):
        """
        Runs app.main() inside a managed loop. If the agent crashes, restart it with backoff.
        """
        script_dir = Path(__file__).parent.resolve()

        try:
            # Ensure predictable runtime behavior
            load_configuration()

            # Ensure imports and relative file access work
            os.chdir(script_dir)
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))

            logger.info("Working directory set to: %s", str(script_dir))
            logger.info("Python executable: %s", sys.executable)

            # Import agent module after env is loaded
            import app  # noqa

            # Optional sanity log (won’t crash if not present)
            controller_url = getattr(app, "CONTROLLER_URL", os.environ.get("CONTROLLER_URL", ""))
            agent_name = getattr(app, "AGENT_NAME", os.environ.get("AGENT_NAME", ""))
            logger.info("Controller URL: %s", controller_url)
            logger.info("Agent Name: %s", agent_name)

            # Managed run loop
            crash_count = 0
            backoff_s = 2

            def run_agent_once():
                # app.main() is expected to block until stopped
                app.main()

            while self.is_running:
                # Start agent thread
                exc_holder = {"exc": None}

                def thread_target():
                    try:
                        logger.info("Starting agent worker...")
                        run_agent_once()
                        logger.info("Agent worker exited normally")
                    except Exception as e:
                        exc_holder["exc"] = e
                        logger.exception("Agent crashed")

                self.agent_thread = threading.Thread(target=thread_target, daemon=False)
                self.agent_thread.start()

                # Monitor stop event / agent health
                while self.is_running:
                    rc = win32event.WaitForSingleObject(self.stop_event, 3000)
                    if rc == win32event.WAIT_OBJECT_0:
                        logger.info("Stop event received")
                        break
                    if self.agent_thread and not self.agent_thread.is_alive():
                        break

                # Request stop inside app if service is stopping
                if not self.is_running:
                    try:
                        if hasattr(app, "_running"):
                            app._running = False
                    except Exception:
                        logger.exception("Failed to signal agent stop")
                    break

                # If thread ended unexpectedly, restart with backoff
                if self.agent_thread and not self.agent_thread.is_alive():
                    crash_count += 1
                    e = exc_holder["exc"]
                    logger.error("Agent stopped unexpectedly (crash_count=%d, err=%s)", crash_count, repr(e))

                    # backoff up to 60s
                    time.sleep(backoff_s)
                    backoff_s = min(backoff_s * 2, 60)
                    continue

            # Final cleanup
            logger.info("Service main loop exiting")

        except ImportError:
            logger.exception("Failed to import app.py. Ensure app.py is in the same folder as Service.py.")
        except Exception:
            logger.exception("Fatal error in service")


# =========================
#   CLI ENTRYPOINT
# =========================

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Started by Windows Service Manager
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AgentLiteService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Normal CLI management (admin)
        win32serviceutil.HandleCommandLine(AgentLiteService)
