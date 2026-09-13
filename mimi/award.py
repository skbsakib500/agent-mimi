"""One-shot XP award + level-up celebration."""
from . import xp
from . import badges
from .levelup import maybe_celebrate


def award(action, amount=None, celebrate=True):
    """Award XP for an action, check badges, celebrate level-up."""
    try:
        gained, leveled_up = xp.award(action, amount)
    except Exception:
        return 0

    if gained and celebrate:
        try:
            maybe_celebrate(gained, leveled_up, xp.level_info)
        except Exception:
            if gained:
                print(f"  +{gained} XP")

    try:
        new = badges.check_all()
        for code in new:
            info = badges.info(code)
            if info:
                print(f"  🏅 NEW BADGE: {info['icon']} {info['label']}")
    except Exception:
        pass

    return gained
