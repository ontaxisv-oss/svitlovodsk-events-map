import subprocess
import time
import re
import sys
import os

def launch_persistent():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("==================================================")
    print("AUTORUN: Tunnel & Bot starting...")
    print("==================================================")

    # 1. Запускаємо cloudflared
    cloudflared_path = os.path.join(os.path.dirname(__file__), "cloudflared.exe")
    if not os.path.exists(cloudflared_path):
        print("ERROR: cloudflared.exe not found!")
        return

    tunnel_proc = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", "http://localhost:8080"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    public_url = None
    print("Waiting for Cloudflare HTTPS tunnel URL...")

    start_time = time.time()
    while time.time() - start_time < 30:
        line = tunnel_proc.stdout.readline()
        if not line:
            break
        print(f"[Tunnel] {line.strip()}")
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        print("ERROR: Failed to fetch Cloudflare URL.")
        return

    print("==================================================")
    print(f"ACTIVE HTTPS URL: {public_url}")
    print("==================================================")

    # 2. Оновлюємо config.py з новим PUBLIC_URL
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        config_text = f.read()

    new_config = re.sub(
        r'PUBLIC_URL = os\.getenv\("PUBLIC_URL", ".*?"\)',
        f'PUBLIC_URL = os.getenv("PUBLIC_URL", "{public_url}")',
        config_text
    )

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(new_config)

    print("Config updated. Updating Surge with new API_BASE...")

    # 3a. Оновлюємо app.js з новим API_BASE
    app_js_path = os.path.join(os.path.dirname(__file__), "public", "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        app_js = f.read()

    updated_js = re.sub(
        r"(const API_BASE = window\.location\.hostname === 'svitlovodsk-map\.surge\.sh'\s*\n\s*\? ')[^']+(')",
        rf"\g<1>{public_url}\g<2>",
        app_js
    )

    with open(app_js_path, "w", encoding="utf-8") as f:
        f.write(updated_js)

    # 3b. Перезаливаємо Surge
    surge_cmd = f'echo ontaxisv@gmail.com| npx -y surge public svitlovodsk-map.surge.sh'
    surge_proc = subprocess.Popen(
        surge_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    surge_out, _ = surge_proc.communicate(timeout=60)
    if surge_out and "Success" in surge_out:
        print(f"✅ Surge оновлено! https://svitlovodsk-map.surge.sh")
    else:
        print(f"⚠️ Surge: {(surge_out or '')[-200:]}")

    print("Starting python server & bot...")

    # 4. Запускаємо run.py
    try:
        subprocess.run([sys.executable, "run.py"])
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        tunnel_proc.terminate()

if __name__ == "__main__":
    launch_persistent()
