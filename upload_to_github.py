import os
import sys
import base64
import urllib.request
import json

def upload_project(token, repo_name="svitlovodsk-events-map"):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Antigravity-Agent"
    }

    # 1. Створюємо репозиторій на GitHub
    create_repo_url = "https://api.github.com/user/repos"
    payload = json.dumps({"name": repo_name, "private": False, "auto_init": False}).encode("utf-8")
    
    req = urllib.request.Request(create_repo_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            repo_info = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Створено репозиторій на GitHub: {repo_info['html_url']}")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print(f"ℹ️ Репозиторій {repo_name} вже існує. Оновлюємо файли...")
        else:
            print(f"❌ Помилка створення репозиторію: {e.read().decode('utf-8')}")
            return

    # 2. Отримуємо список усіх файлів проекту
    root_dir = os.path.dirname(__file__)
    ignored_dirs = {'.git', '__pycache__', 'data'}
    ignored_files = {'svitlovodsk-events-map.zip', 'cloudflared.exe'}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            if f in ignored_files or f.endswith('.pyc') or f.endswith('.exe') or f.endswith('.zip'):
                continue

            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, root_dir).replace('\\', '/')

            with open(filepath, 'rb') as file_obj:
                content = file_obj.read()
            
            b64_content = base64.b64encode(content).decode('utf-8')
            
            # Перевіряємо чи файл існує на GitHub для отримання sha
            file_url = f"https://api.github.com/repos/{get_username(token)}/{repo_name}/contents/{relpath}"
            sha = None
            try:
                get_req = urllib.request.Request(file_url, headers=headers)
                with urllib.request.urlopen(get_req) as get_resp:
                    sha = json.loads(get_resp.read().decode("utf-8")).get("sha")
            except Exception:
                pass

            put_data = {
                "message": f"Upload {relpath}",
                "content": b64_content
            }
            if sha:
                put_data["sha"] = sha

            put_req = urllib.request.Request(
                file_url,
                data=json.dumps(put_data).encode("utf-8"),
                headers=headers,
                method="PUT"
            )
            try:
                with urllib.request.urlopen(put_req):
                    print(f"  🟢 Завантажено: {relpath}")
            except Exception as ex:
                print(f"  ⚠️ Помилка завантаження {relpath}: {ex}")

    print(f"\n🎉 Проект успішно завантажено на GitHub: https://github.com/{get_username(token)}/{repo_name}")

def get_username(token):
    req = urllib.request.Request("https://api.github.com/user", headers={"Authorization": f"token {token}", "User-Agent": "Antigravity-Agent"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["login"]

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not token:
        print("Введіть GITHUB_TOKEN для автоматичного завантаження на GitHub.")
    else:
        upload_project(token)
