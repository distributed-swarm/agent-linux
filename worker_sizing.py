import os
import math
from typing import Dict, Any

try:
    import psutil
except ImportError:
    psutil = None


def _detect_cpu() -> Dict[str, Any]:
    """
    Basic CPU sizing using psutil if available, otherwise os.cpu_count().
    """
    if psutil is not None:
        try:
            total_cores = psutil.cpu_count(logical=True) or 1
        except Exception:
            total_cores = os.cpu_count() or 1
    else:
        total_cores = os.cpu_count() or 1

    # Reserve some cores for the system overhead
    reserved_cores = min(4, max(1, total_cores // 4))
    usable_cores = max(1, total_cores - reserved_cores)

    # Rough heuristic: up to 1 worker per usable core
    max_cpu_workers = max(1, usable_cores)
    min_cpu_workers = 1

    return {
        "total_cores": int(total_cores),
        "reserved_cores": int(reserved_cores),
        "usable_cores": int(usable_cores),
        "min_cpu_workers": int(min_cpu_workers),
        "max_cpu_workers": int(max_cpu_workers),
    }


def build_worker_profile() -> Dict[str, Any]:
    """
    CPU-only worker profile for agent-lite.
    
    Always reports no GPU present since agent-lite is CPU-only.

    Shape is what the controller & UI already expect:

      {
        "cpu": {...},
        "gpu": {...},
        "workers": {
          "max_total_workers": int,
          "current_workers": 0
        }
      }
    """
    cpu_info = _detect_cpu()
    
    # Agent-lite: Always report no GPU
    gpu_info = {
        "gpu_present": False,
        "gpu_count": 0,
        "vram_gb": None,
        "devices": [],
        "max_gpu_workers": 0,
    }

    # Total worker limit: use CPU max workers as upper bound
    max_total_workers = cpu_info.get("max_cpu_workers", 1)
    if isinstance(max_total_workers, float):
        max_total_workers = int(math.floor(max_total_workers))

    if max_total_workers < 1:
        max_total_workers = 1

    return {
        "cpu": cpu_info,
        "gpu": gpu_info,
        "workers": {
            "max_total_workers": int(max_total_workers),
            "current_workers": 0,
        },
    }
