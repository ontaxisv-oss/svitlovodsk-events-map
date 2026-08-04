import urllib.request
import json
import zipfile
import io
import os

def deploy_netlify():
    print("Packing public directory to zip...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk('public'):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, 'public')
                zip_file.write(file_path, arcname)
    
    zip_data = zip_buffer.getvalue()
    print(f"Zip created: {len(zip_data)} bytes")

    # Створюємо новий сайт на Netlify без авторизації
    req = urllib.request.Request(
        'https://api.netlify.com/api/v1/sites',
        data=zip_data,
        headers={
            'Content-Type': 'application/zip',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            site_url = data.get('ssl_url') or data.get('url')
            print("==================================================")
            print("NETLIFY_VISUAL_MAP_URL:", site_url)
            print("==================================================")
            
            with open('netlify_url.txt', 'w') as f_out:
                f_out.write(site_url)
    except Exception as ex:
        print("Netlify deploy error:", ex)

if __name__ == '__main__':
    deploy_netlify()
