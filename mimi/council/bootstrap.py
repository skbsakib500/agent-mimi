"""Auto-register all council departments."""
from .council import council

_DEPTS = (
    ("mimi.council.departments.devops", "DevOps"),
    ("mimi.council.departments.strategy", "Strategy"),
    ("mimi.council.departments.finance", "Finance"),
    ("mimi.council.departments.admin", "Admin"),
    ("mimi.council.departments.study", "Study"),
    ("mimi.council.departments.health", "Health"),
    ("mimi.council.departments.civil", "Civil"),
    ("mimi.council.departments.research", "Research"),
    ("mimi.council.departments.relations", "Relations"),
    ("mimi.council.departments.legal", "Legal"),
)


def bootstrap():
    """Register all standard departments if not already present."""
    import importlib
    c = council()
    existing = {d.NAME for d in c.all()}
    added = []
    for mod_path, cls_name in _DEPTS:
        try:
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            inst = cls()
            if inst.NAME not in existing:
                c.register(inst)
                added.append(inst.NAME)
        except Exception:
            continue
    return added


def is_bootstrapped():
    c = council()
    return len(c.all()) >= 10
