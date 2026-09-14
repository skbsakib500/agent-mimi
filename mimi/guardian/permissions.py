"""V10 Guardian - permission gate.

Every sensitive operation passes through check(). The gate consults
the constitution, logs every decision, and refuses by default.
"""
from . import audit
from ..trust.loader import ensure_trusted

# Operations and their policy.
# "auto"    -> allowed, logged
# "owner"   -> requires approval token from owner
# "refuse"  -> never allowed, even with approval
POLICY = {
    # read-only
    "read":            "auto",
    "list":            "auto",
    "query":           "auto",
    "compute":         "auto",
    "plan":            "auto",
    "predict":         "auto",
    "report":          "auto",

    # network
    "network_read":    "auto",
    "network_write":   "owner",

    # modifications
    "write_db":        "auto",
    "delete_record":   "owner",
    "delete_table":    "refuse",
    "drop_database":   "refuse",

    # code / files
    "read_code":       "auto",
    "write_code":      "owner",
    "delete_file":     "owner",
    "delete_dir":      "refuse",

    # trust root
    "read_constitution":  "auto",
    "sign":               "owner",
    "resign_constitution":"owner",
    "delete_key":         "refuse",
    "chmod_key_open":     "refuse",

    # upgrades
    "upgrade_propose":    "auto",
    "upgrade_apply":      "owner",
    "upgrade_rollback":   "owner",

    # external
    "send_external":      "owner",
    "install_package":    "owner",
}


def _normalize(op):
    return str(op).strip().lower().replace("-", "_")


def check(op, actor="system", approved_by=None, context=None):
    """Return (allowed: bool, reason: str).

    Records decision in the audit log. Never raises.
    """
    op_n = _normalize(op)
    ctx = context or {}

    # Trust root gate first
    try:
        if not ensure_trusted(fail_closed=False):
            audit.log("permission_denied", actor=actor,
                      payload={"op": op_n, "why": "trust_failed"})
            return False, "trust root not verified"
    except Exception:
        return False, "trust loader error"

    verdict = POLICY.get(op_n)
    if verdict is None:
        audit.log("permission_denied", actor=actor,
                  payload={"op": op_n, "why": "unknown_op"})
        return False, f"unknown operation: {op_n}"

    if verdict == "refuse":
        audit.log("permission_denied", actor=actor,
                  payload={"op": op_n, "why": "policy_refuse"})
        return False, f"operation '{op_n}' is refused by policy"

    if verdict == "owner":
        if approved_by != "SKB Sakib":
            audit.log("permission_denied", actor=actor,
                      payload={"op": op_n, "why": "no_owner_approval",
                               "approved_by": approved_by})
            return False, "requires owner approval (SKB Sakib)"
        audit.log("permission_granted", actor=actor,
                  payload={"op": op_n, "mode": "owner"})
        return True, "owner approved"

    # auto
    audit.log("permission_granted", actor=actor,
              payload={"op": op_n, "mode": "auto", "ctx": ctx})
    return True, "auto-allowed"


def policy_for(op):
    return POLICY.get(_normalize(op), "(unknown)")


def main():
    import sys
    if len(sys.argv) > 1:
        op = sys.argv[1]
        approved = sys.argv[2] if len(sys.argv) > 2 else None
        ok, reason = check(op, actor="cli", approved_by=approved)
        mark = "OK" if ok else "X"
        print(f"  {mark} {op}: {reason}")
        return 0 if ok else 1
    print("Policy table:")
    for k in sorted(POLICY):
        print(f"  {k:<22} {POLICY[k]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
