import urllib.request
import json
import os

def create_visual_gist():
    with open('public/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    with open('public/styles.css', 'r', encoding='utf-8') as f:
        css = f.read()
    with open('public/app.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Створюємо монолітний файл
    standalone_html = html.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f'<style>\n{css}\n</style>'
    ).replace(
        '</body>',
        f'<script>\n{js}\n</script>\n</body>'
    )

    data = json.dumps({
        'description': 'Svitlovodsk Visual Map',
        'public': True,
        'files': {
            'index.html': {
                'content': standalone_html
            }
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.github.com/gists',
        data=data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            raw_url = res_data['files']['index.html']['raw_url']
            
            # htmlpreview посилання для 100% візуального рендерингу
            preview_url = f"https://htmlpreview.github.io/?{raw_url}"
            print("==================================================")
            print("VISUAL_MAP_URL:", preview_url)
            print("==================================================")

            with open('visual_url.txt', 'w') as f_out:
                f_out.write(preview_url)
    except Exception as ex:
        print("Gist error:", ex)

if __name__ == '__main__':
    create_visual_gist()
