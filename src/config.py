import os
import yaml
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    gmail_user: str = ""
    gmail_app_password: str = ""
    email_to: str = ""
    timezone: str = "Asia/Shanghai"

def load_env_file(filepath: str = "local.env"):
    p = Path(filepath)
    if not p.exists():
        return
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def get_settings() -> Settings:
    load_env_file()
    return Settings(
        gmail_user=os.environ.get("GMAIL_USER", ""),
        gmail_app_password=os.environ.get("GMAIL_APP_PASSWORD", ""),
        email_to=os.environ.get("EMAIL_TO", ""),
        timezone=os.environ.get("TIMEZONE", "Asia/Shanghai")
    )

def load_assets_config(filepath: str = "config/assets.yaml") -> list[dict]:
    p = Path(filepath)
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("assets", [])
