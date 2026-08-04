import urllib.request
import urllib.parse
import json
import uuid
import os

def deploy_to_catbox():
    root_public = 'public'
    
    with open(os.path.join(root_public, 'index.html'), 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    with open(os.path.join(root_public, 'styles.css'), 'r', encoding='utf-8') as f:
        css_content = f.read()

    with open(os.path.join(root_public, 'app.js'), 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Створюємо монолітний index.html
    html_content = html_content.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f'<style>\n{css_content}\n</style>'
    )
    html_content = html_content.replace(
        '</body>',
        f'<script>\n{js_content}\n</script>\n</body>'
    )

    with open('index_standalone.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 1. Створюємо multipart/form-data для catbox
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    body = bytearray()

    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'.encode('utf-8'))
    body.extend(f'fileupload\r\n'.encode('utf-8'))

    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="fileToUpload"; filename="index.html"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: text/html; charset=utf-8\r\n\r\n'.encode('utf-8'))
    body.extend(html_content.encode('utf-8'))
    body.extend(f'\r\n'.encode('utf-8'))

    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

    req = urllib.request.Request(
        'https://catbox.moe/user/api.php',
        data=bytes(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8').strip()
            print("=== DEPLOY SUCCESS ===")
            print("URL:", data)
            print("======================")
            
            with open('deploy_result.json', 'w') as f_res:
                json.dump({'url': data}, f_res)
    except Exception as ex:
        print("Помилка catbox:", ex)

if __name__ == '__main__':
    deploy_to_catbox()
