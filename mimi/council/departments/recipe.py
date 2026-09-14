"""Auto-generated department: recipe."""
from datetime import date
from ..department import Department
from ...database import fetch_one, fetch_all, execute
from ...guardian import audit


class Recipe(Department):
    NAME = "recipe"
    ROLE = "cook"
    MANDATE = "Store and search recipes"
    CAPABILITIES = ("recipe", "cook", "food")
    PRIORITY = 5

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "recipe_ping": self._ping,
            "recipe_echo": self._echo,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Recipe cannot handle '{command}'")
        return fn(args, actor)

    def _ping(self, args, actor):
        return {"ok": True, "dept": self.NAME, "pong": True}

    def _echo(self, args, actor):
        msg = (args.get("message") or "").strip()
        return {"ok": True, "echo": msg}
