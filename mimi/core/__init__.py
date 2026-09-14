"""V10 Core package."""
# Re-export everything from the legacy core module
from ._legacy import (APP_NAME, VERSION, CODENAME, SYSTEM,
                      USER_NAME, SCHEMA_VERSION, greeting)

# V10 submodules
from . import bus
from . import registry
from . import orchestrator

__all__ = ["APP_NAME", "VERSION", "CODENAME", "SYSTEM",
           "USER_NAME", "SCHEMA_VERSION", "greeting",
           "bus", "registry", "orchestrator"]
