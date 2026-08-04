import urllib.request
import json
import uuid
import os

def deploy_fileio():
    filename = 'index_standalone.html'
    if not os.path.exists(filename):
        with open('public/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        with open('public/styles.css', 'r', encoding='utf-8') as f:
            css = f.read()
        with open('public/app.js', 'r', encoding='utf-8') as f:
            js = f.read()

        standalone = html.replace(
            '<link rel="stylesheet" href="styles.css" />',
            f'<style>\n{css}\n</style>'
        ).replace(
            '</body>',
            f'<script>\n{js}\n</script>\n</body>'
        )
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(standalone)

    with open(filename, 'rb') as f:
        content = f.read()

    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    body = bytearray()

    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="index.html"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: text/html; charset=utf-8\r\n\r\n'.encode('utf-8'))
    body.extend(content)
    body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

    req = urllib.request.Request(
        'https://file.io',
        data=bytes(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            link = data.get('link', '')
            print("==================================================")
            print("FILE_IO_URL:", link)
            print("==================================================")
    except Exception as ex:
        print("file.io Error:", ex)

if __name__ == '__main__':
    deploy_fileio()
