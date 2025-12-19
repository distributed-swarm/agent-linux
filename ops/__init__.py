"""
Basic op registry for Base Agent v2.

This file defines a simple registry that other modules can use to
register operation handlers. For now we also eagerly register the
built-in ops like map_classify and map_summarize.
"""

from typing import Any, Callable, Dict, Optional

# op name -> handler(task: dict) -> dict
OPS_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}


def register_op(
    name: str,
    handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
):
    """
    Register an op handler.

    Supports two usage styles:

      1) Direct registration (what older code used):
         register_op("map_classify", handler_fn)

      2) Decorator style (what newer plugins can use):
         @register_op("map_summarize")
         def handle(task: dict) -> dict:
             ...

    In both cases, OPS_REGISTRY[name] will point to the handler.
    """

    # Direct call: register_op("name", handler_fn)
    if handler is not None:
        OPS_REGISTRY[name] = handler
        return handler

    # Decorator usage: @register_op("name")
    def decorator(fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        OPS_REGISTRY[name] = fn
        return fn

    return decorator


def get_op(name: str):
    """Get a handler by op name, or None if not registered."""
    return OPS_REGISTRY.get(name)


def list_ops():
    """Return a list of registered op names."""
    return list(OPS_REGISTRY.keys())


# ------------------------------------------------------------------
# Built-in ops
# ------------------------------------------------------------------


def _safe_register_builtins():
    """
    Try to register built-ins in a backward-compatible way.

    We support:
      - New style: module has OP_NAME + handle(task: dict)
      - Old style: module has <op>(task)
    """

    def _try_register(module_name: str, default_op_name: str):
        """
        Attempt to import a module and register its handler.
        - New style: OP_NAME + handle
        - Old style: function named like default_op_name
        """
        try:
            mod = __import__(f"{__name__}.{module_name}", fromlist=[module_name])
            if hasattr(mod, "OP_NAME") and hasattr(mod, "handle"):
                register_op(getattr(mod, "OP_NAME"), getattr(mod, "handle"))
                return
            # old-style function name matches the op name
            if hasattr(mod, default_op_name):
                register_op(default_op_name, getattr(mod, default_op_name))
                return
        except Exception:
            # Don't kill the agent just because one op is broken.
            pass

    # Existing lite ops
    _try_register("map_classify", "map_classify")
    _try_register("map_summarize", "map_summarize")

    # Added lite-safe ops
    _try_register("csv_shard", "csv_shard")
    _try_register("fibonacci", "fibonacci")
    _try_register("prime_factor", "prime_factor")


_safe_register_builtins()
