"""Civil Engineering department - BOQ, estimate, quantity."""
from ..department import Department
from ...guardian import audit


class Civil(Department):
    NAME = "civil"
    ROLE = "civil_engineer"
    MANDATE = "Construction quantity and cost math (needs engineer verification)"
    CAPABILITIES = ("civil", "boq", "estimate", "quantity",
                    "concrete", "brick", "construction")
    PRIORITY = 5

    def handle(self, command, args=None, actor="system"):
        args = args or {}
        table = {
            "boq":       self._boq,
            "estimate":  self._estimate,
            "quantity":  self._quantity,
            "concrete":  self._concrete,
            "brick":     self._brick,
        }
        fn = table.get(command)
        if not fn:
            raise NotImplementedError(
                f"Civil cannot handle '{command}'")
        return fn(args, actor)

    def _quantity(self, args, actor):
        shape = (args.get("shape") or "rect").lower()
        if shape == "rect":
            l = float(args.get("length") or 0)
            w = float(args.get("width") or 0)
            return {"area_sqm": round(l * w, 3),
                    "note": "verify with licensed engineer"}
        if shape == "box":
            l = float(args.get("length") or 0)
            w = float(args.get("width") or 0)
            h = float(args.get("height") or 0)
            v = l * w * h
            return {"volume_cum": round(v, 3),
                    "volume_cft": round(v * 35.3147, 2),
                    "note": "verify with licensed engineer"}
        raise ValueError(f"unknown shape '{shape}'")

    def _concrete(self, args, actor):
        vol = float(args.get("volume_cum") or 0)
        if vol <= 0:
            raise ValueError("volume_cum required")
        ratio = args.get("ratio") or "1:2:4"
        bags = {"1:1.5:3": 8.5, "1:2:4": 6.4, "1:3:6": 4.6}.get(ratio, 6.4)
        return {
            "volume_cum": vol, "ratio": ratio,
            "cement_bags": round(bags * vol, 1),
            "sand_cum": round(0.42 * vol, 2),
            "aggregate_cum": round(0.85 * vol, 2),
            "note": "verify with licensed engineer before ordering",
        }

    def _brick(self, args, actor):
        l = float(args.get("length") or 0)
        h = float(args.get("height") or 0)
        t = float(args.get("thickness") or 0.125)
        v = l * h * t
        return {
            "wall_volume_cum": round(v, 3),
            "bricks_approx": int(v * 500),
            "mortar_cum": round(v * 0.30, 3),
            "note": "verify with licensed engineer before ordering",
        }

    def _boq(self, args, actor):
        items = args.get("items") or []
        if not isinstance(items, list):
            raise ValueError("items must be list")
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
                "qty": qty, "rate": rate,
                "amount": round(amount, 2),
            })
        return {
            "lines": lines,
            "subtotal": round(total, 2),
            "note": "prices require professional verification",
        }

    def _estimate(self, args, actor):
        boq = self._boq(args, actor)
        pct = float(args.get("contingency_pct") or 10)
        sub = boq["subtotal"]
        cont = sub * pct / 100
        return {
            "boq": boq["lines"],
            "subtotal": round(sub, 2),
            "contingency_pct": pct,
            "contingency_amount": round(cont, 2),
            "total": round(sub + cont, 2),
            "note": "estimate only; needs professional sign-off",
        }
