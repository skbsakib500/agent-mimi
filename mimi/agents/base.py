"""V10 Specialists - base class.

Every specialist:
  - declares role + capabilities
  - auto-registers with core.registry at __init__
  - implements handle(command, args, actor) -> dict
  - is audited automatically by the orchestrator
"""
from ..core.registry import registry
from ..guardian import audit


class Specialist:
    NAME = "base"
    ROLE = "generic"
    CAPABILITIES = ()
    DESCRIPTION = ""

    def __init__(self):
        registry().register(
            self.NAME, self,
            role=self.ROLE,
            capabilities=self.CAPABILITIES,
            description=self.DESCRIPTION or self.__doc__ or "",
        )

    # Subclasses override
    def handle(self, command, args=None, actor="system"):
        raise NotImplementedError(
            f"{self.NAME} cannot handle '{command}'"
        )

    # Optional: return health dict
    def health(self):
        return {"name": self.NAME, "ok": True}
