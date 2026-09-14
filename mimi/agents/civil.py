"""Civil Engineer - BOQ, estimate, quantity calculations.

DISCLAIMER: This is decision-support math only. Real construction
requires a licensed engineer's verification. Mimi never signs off
on structural safety — only computes quantities and costs.
"""
from .base import Specialist
from ..database import execute, fetch_all
from ..guardian import audit


# Unit conversion helpers (all lengths in meters)
def sqm(l, w):
    return float(l) * float(w)

def cum(l, w, h):
    return float(l) * float(w) * float(h)

def cft(l, w, h):
    return float(l) * float(w) * float(h) * 35.3147


class Civil(Specialist):
    NAME = "civil"
    ROLE = "civil_engineer"
    CAPABILITIES = ("civil", "boq", "estimate", "quantity")
    DESCRIPTION = "Quantity and cost math (needs engineer verification)"

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "boq": self._boq,
            "estimate": self._estimate,
            "quantity": self._quantity,
            "concrete": self._concrete,
            "brick": self._brick,
        }
        fn = table.get(command)
        if not fn:
            raise ValueError(f"Civil does not handle '{command}'")
        return fn(args, actor)

    def _quantity(self, args, actor):
        """Generic area/volume."""
        shape = (args.get("shape") or "rect").lower()
        if shape == "rect":
            l = float(args.get("length") or 0)
            w = float(args.get("width") or 0)
            return {"area_sqm": sqm(l, w), "shape": "rectangle",
                    "note": "licensed engineer verification required"}
        if shape == "box":
            l = float(args.get("length") or 0)
            w = float(args.get("width") or 0)
            h = float(args.get("height") or 0)
            return {"volume_cum": cum(l, w, h),
                    "volume_cft": cft(l, w, h),
                    "shape": "box",
                    "note": "licensed engineer verification required"}
        raise ValueError(f"unknown shape '{shape}'")

    def _concrete(self, args, actor):
        """Concrete mix estimate for given volume."""
        vol = float(args.get("volume_cum") or 0)
        if vol <= 0:
            raise ValueError("volume_cum required")
        ratio = args.get("ratio") or "1:2:4"
        # Nominal cement bags per cum for common mixes
        bags_per_cum = {"1:1.5:3": 8.5, "1:2:4": 6.4, "1:3:6": 4.6}
        bags = bags_per_cum.get(ratio, 6.4) * vol
        sand = 0.42 * vol  # cum
        agg = 0.85 * vol  # cum
        return {
            "volume_cum": vol, "ratio": ratio,
            "cement_bags": round(bags, 1),
            "sand_cum": round(sand, 2),
            "aggregate_cum": round(agg, 2),
            "note": "verify with licensed engineer before ordering",
        }

    def _brick(self, args, actor):
        """Brickwork estimate."""
        l = float(args.get("length") or 0)
        h = float(args.get("height") or 0)
        t = float(args.get("thickness") or 0.125)  # 5 inch
        wall_vol = l * h * t
        bricks_per_cum = 500
        return {
            "wall_volume_cum": round(wall_vol, 3),
            "bricks_approx": int(wall_vol * bricks_per_cum),
            "mortar_cum": round(wall_vol * 0.30, 3),
            "note": "verify with licensed engineer before ordering",
        }

    def _boq(self, args, actor):
        """Bill of Quantities - list of items with qty × rate = amount."""
        items = args.get("items") or []
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        lines = []
        total = 0.0
        for it in items:
            try:
                qty = float(it.get("qty") or 0)
                rate = float(it.get("rate") or 0)
            except (TypeError, ValueError):
                continue
            amount = qty * rate
            total += amount
            lines.append({
                "desc": str(it.get("desc") or "item")[:60],
                "unit": str(it.get("unit") or "unit"),
                "qty": qty, "rate": rate, "amount": amount,
            })
        return {
            "lines": lines,
            "subtotal": round(total, 2),
            "note": "prices and quantities require professional verification",
        }

    def _estimate(self, args, actor):
        """Full estimate: BOQ + contingency."""
        boq = self._boq(args, actor)
        contingency_pct = float(args.get("contingency_pct") or 10)
        sub = boq["subtotal"]
        cont = sub * contingency_pct / 100
        return {
            "boq": boq["lines"],
            "subtotal": round(sub, 2),
            "contingency_pct": contingency_pct,
            "contingency_amount": round(cont, 2),
            "total": round(sub + cont, 2),
            "note": "estimate only; final costs need professional sign-off",
        }


civil = Civil()
