"""Load canonical prompt specs from Life OS spec directory.

Source of truth: ~/SKB-Dev/spec/lifos/ai/prompts/<id>.md
Fallback:        ~/Life-OS/ai/prompts/<id>.md  (symlinked)

Rule: runtime is ADAPTER; spec is CANONICAL.
Never edit prompts in runtime code — edit the spec.
"""
import os


SPEC_DIRS = [
    os.path.expanduser("~/SKB-Dev/spec/lifos/ai/prompts"),
    os.path.expanduser("~/Life-OS/ai/prompts"),
]


def _parse_frontmatter(text):
    """Parse simple YAML frontmatter. Returns (meta_dict, body_str)."""
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return {}, text
    rest = text.split("\n", 1)[1] if "\n" in text else ""
    end = rest.find("\n---")
    if end < 0:
        return {}, text
    fm = rest[:end]
    body = rest[end + 4:].lstrip("\n").lstrip("\r\n")
    meta = {}
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            v = [x.strip() for x in inner.split(",")] if inner else []
        elif v.isdigit():
            v = int(v)
        else:
            try:
                v = float(v)
            except ValueError:
                pass
        meta[k] = v
    return meta, body


def load_prompt(prompt_id):
    """Load a prompt spec by id.

    Returns dict: { meta, body, source }  or None if not found.
    """
    for base in SPEC_DIRS:
        if not os.path.isdir(base):
            continue
        path = os.path.join(base, prompt_id + ".md")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            meta, body = _parse_frontmatter(content)
            return {"meta": meta, "body": body, "source": path}
        except Exception:
            continue
    return None


def validate_prompt(prompt, available_inputs):
    """Return list of declared input keys not present in available_inputs.

    Empty list = all good.
    """
    if not prompt:
        return ["(no prompt loaded)"]
    declared = prompt.get("meta", {}).get("inputs", [])
    if not isinstance(declared, list):
        return []
    return [k for k in declared if k not in available_inputs]


if __name__ == "__main__":
    import sys, json
    pid = sys.argv[1] if len(sys.argv) > 1 else "daily_plan"
    p = load_prompt(pid)
    if not p:
        print(f"prompt not found: {pid}", file=sys.stderr)
        sys.exit(1)
    print(f"source: {p['source']}")
    print(f"meta:   {json.dumps(p['meta'], indent=2)}")
    print("---")
    print(p["body"])
