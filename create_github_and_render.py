import urllib.request
import urllib.parse
import json
import os
import sys

RENDER_API_KEY = "rnd_npkqYwDmsnKdtOKK5gGJhH7XbOyK"
RENDER_OWNER_ID = "tea-d9oc2mh42hec7394uvk0"

def deploy(github_token):
    # 1. Створюємо репозиторій на GitHub через API
    headers_gh = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Agent"
    }

    repo_name = "svitlovodsk-events-map"
    payload_gh = json.dumps({"name": repo_name, "private": False, "auto_init": True}).encode("utf-8")
    
    req_gh = urllib.request.Request("https://api.github.com/user/repos", data=payload_gh, headers=headers_gh, method="POST")
    repo_url = None
    try:
        with urllib.request.urlopen(req_gh) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            repo_url = data.get("html_url")
            print("✅ GitHub Репозиторій створено:", repo_url)
    except urllib.error.HTTPError as e:
        if e.code == 422:
            # Отримуємо username
            u_req = urllib.request.Request("https://api.github.com/user", headers=headers_gh)
            with urllib.request.urlopen(u_req) as u_resp:
                username = json.loads(u_resp.read().decode("utf-8"))["login"]
                repo_url = f"https://github.com/{username}/{repo_name}"
                print("ℹ️ Репозиторій вже існує:", repo_url)
        else:
            print("❌ Помилка GitHub:", e.code, e.read().decode("utf-8"))
            return

    # 2. Створюємо сервіс на Render через API
    headers_render = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload_render = {
        "type": "web_service",
        "name": "svitlovodsk-events-map",
        "ownerId": RENDER_OWNER_ID,
        "repo": repo_url,
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "region": "frankfurt",
            "envVars": [
                {"key": "BOT_TOKEN", "value": "8469860489:AAH2ZC7y7FUeF6wZleI0Z_amSFdVxk4mY8w"},
                {"key": "SOURCE_CHANNEL", "value": "ukraina_olivki"},
                {"key": "TARGET_CHANNEL", "value": "@kr_probki"},
                {"key": "PORT", "value": "8080"}
            ]
        }
    }

    req_render = urllib.request.Request(
        "https://api.render.com/v1/services",
        data=json.dumps(payload_render).encode("utf-8"),
        headers=headers_render,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_render) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            service_info = data.get("service", {})
            service_url = service_info.get("serviceDetails", {}).get("url")
            print("==================================================")
            print("🚀 СЕРВЕР СТВОРЕНО НА RENDER!")
            print("🌐 Хмарна адреса:", service_url)
            print("==================================================")
    except urllib.error.HTTPError as e:
        print("❌ Помилка Render API:", e.code, e.read().decode("utf-8"))

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else ""
    if token:
        deploy(token)
    else:
        print("Введіть GITHUB_TOKEN")
