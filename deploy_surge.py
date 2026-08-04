import subprocess
import sys
import time

def deploy_surge():
    print("Creating Surge account & deploying visual map...")
    # Стандартні облікові дані Surge
    email = "antigravity.svitlovodsk.map@gmail.com"
    password = "SvitlovodskMapPass2026!"
    domain = "svitlovodsk-events-map.surge.sh"

    # Створюємо процес Surge
    cmd = f"npx -y surge public {domain} --email {email} --password {password}"
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(timeout=30)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)

    if "Success" in stdout or "Success" in stderr or "svitlovodsk" in stdout:
        print("==================================================")
        print("SURGE_VISUAL_MAP_URL:", f"https://{domain}")
        print("==================================================")

if __name__ == '__main__':
    deploy_surge()
