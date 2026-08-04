import urllib.request
import uuid
import os

def deploy_0x0():
    filename = 'index_standalone.html'
    if not os.path.exists(filename):
        print("Creating standalone html...")
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
        'https://0x0.st',
        data=bytes(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            url = resp.read().decode('utf-8').strip()
            print("==================================================")
            print("VISUAL_URL:", url)
            print("==================================================")
            with open('visual_url.txt', 'w') as f_out:
                f_out.write(url)
    except Exception as ex:
        print("0x0 Error:", ex)

if __name__ == '__main__':
    deploy_0x0()
