# config_check.py
import argparse, random, string, yaml, os

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

def ensure_keys(cfg: dict):
    changed = []
    cfg.setdefault("base_url", "http://localhost:8510")
    cfg.setdefault("dashboard_url", "http://localhost:8505")
    smtp = cfg.setdefault("smtp", {})
    if "host" not in smtp: smtp["host"]="smtp.gmail.com"; changed.append("smtp.host")
    if "port" not in smtp: smtp["port"]=465; changed.append("smtp.port")
    smtp.setdefault("user",""); smtp.setdefault("pass","")
    smtp.setdefault("sender_name","해야할일 알림")
    if not smtp.get("sender_email"): smtp["sender_email"]=smtp.get("user","")
    if not cfg.get("secret"):
        cfg["secret"]="".join(random.choices(string.ascii_letters+string.digits,k=48)); changed.append("secret")
    return cfg, changed

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="config.yaml")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        raise SystemExit(f"[!] config not found: {args.path}")
    cfg = load_yaml(args.path)
    cfg2, changed = ensure_keys(cfg)
    if not args.no_write and cfg2!=cfg:
        save_yaml(args.path, cfg2)
        print("[OK] config updated:", ", ".join(changed) if changed else "(no changes)")
    print("SMTP:", cfg2.get("smtp"))
    print("base_url:", cfg2.get("base_url"), "dashboard_url:", cfg2.get("dashboard_url"))
