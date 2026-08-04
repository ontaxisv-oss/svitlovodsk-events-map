import urllib.request
import urllib.parse
import json
import time
import os

API_KEY = "rnd_npkqYwDmsnKdtOKK5gGJhH7XbOyK"
OWNER_ID = "tea-d9oc2mh42hec7394uvk0"

def create_service(repo_url):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "type": "web_service",
        "name": "svitlovodsk-events-map",
        "ownerId": OWNER_ID,
        "repo": repo_url,
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "region": "frankfurt",
            "plan": "starter",
            "envVars": [
                {"key": "BOT_TOKEN", "value": "8469860489:AAH2ZC7y7FUeF6wZleI0Z_amSFdVxk4mY8w"},
                {"key": "SOURCE_CHANNEL", "value": "ukraina_olivki"},
                {"key": "TARGET_CHANNEL", "value": "@kr_probki"},
                {"key": "PORT", "value": "8080"}
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
            service_info = data.get("service", {})
            service_id = service_info.get("id")
            service_url = service_info.get("serviceDetails", {}).get("url")
            print("==================================================")
            print("🚀 СЕРВЕР СТВОРЕНО НА RENDER!")
            print("Service ID:", service_id)
            print("URL:", service_url)
            print("==================================================")
            return service_url
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode("utf-8"))
        return None

if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else ""
    if repo:
        create_service(repo)
    else:
        print("Введіть посилання на репозиторій.")
