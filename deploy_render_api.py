import urllib.request
import urllib.parse
import json
import os
import sys

def deploy_to_render_api(api_key, github_repo_url):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Створюємо веб-сервіс на Render через API
    payload = {
        "type": "web_service",
        "name": "svitlovodsk-events-map",
        "ownerId": get_owner_id(api_key),
        "repo": github_repo_url,
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "region": "frankfurt",
            "envVars": [
                {"key": "BOT_TOKEN", "value": "8469860489:AAH2ZC7y7FUeF6wZleI0Z_amSFdVxk4mY8w"},
                {"key": "SOURCE_CHANNEL", "value": "ukraina_olivki"},
                {"key": "TARGET_CHANNEL", "value": "@kr_probki"}
            ]
        }
    }

    req = urllib.request.Request(
        "https://api.render.com/v1/services",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            service_url = data.get("service", {}).get("serviceDetails", {}).get("url")
            print("==================================================")
            print("🚀 УСПІШНО СТВОРЕНО СЕРВЕР НА RENDER!")
            print("🌐 Хмарна адреса:", service_url)
            print("==================================================")
    except urllib.error.HTTPError as e:
        print("Помилка Render API:", e.code, e.read().decode("utf-8"))
    except Exception as ex:
        print("Помилка:", ex)

def get_owner_id(api_key):
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    )
    req_render = urllib.request.Request(
        "https://api.render.com/v1/owners",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req_render) as resp:
        owners = json.loads(resp.read().decode("utf-8"))
        if owners:
            return owners[0]["owner"]["id"]
    return ""

if __name__ == "__main__":
    api_key = os.getenv("RENDER_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 else "")
    repo_url = os.getenv("GITHUB_REPO") or (sys.argv[2] if len(sys.argv) > 2 else "")
    if api_key and repo_url:
        deploy_to_render_api(api_key, repo_url)
    else:
        print("Потрібно вказати RENDER_API_KEY та GITHUB_REPO")
