import urllib.request
import urllib.parse
import json
import uuid
import os

def upload_to_tiiny():
    file_path = 'public.zip'
    if not os.path.exists(file_path):
        print("Помилка: public.zip не знайдено.")
        return

    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    subdomain = f"svitlovodsk-{uuid.uuid4().hex[:6]}"

    with open(file_path, 'rb') as f:
        content = f.read()

    body = bytearray()
    
    # 1. Поле file
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="public.zip"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: application/zip\r\n\r\n'.encode('utf-8'))
    body.extend(content)
    body.extend(f'\r\n'.encode('utf-8'))

    # 2. Поле subdomain
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="subdomain"\r\n\r\n'.encode('utf-8'))
    body.extend(f'{subdomain}\r\n'.encode('utf-8'))

    # Завершення
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

    req = urllib.request.Request(
        'https://tiiny.host/api/upload',
        data=bytes(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8')
            print("Успішно! Відповідь:", data)
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode('utf-8'))
    except Exception as ex:
        print("Error:", ex)

if __name__ == '__main__':
    upload_to_tiiny()
