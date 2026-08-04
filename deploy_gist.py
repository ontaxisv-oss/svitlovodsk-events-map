import urllib.request
import urllib.parse
import json
import os

def bundle_and_deploy_gist():
    # Зчитуємо index.html, styles.css, app.js
    root_public = 'public'
    
    with open(os.path.join(root_public, 'index.html'), 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    with open(os.path.join(root_public, 'styles.css'), 'r', encoding='utf-8') as f:
        css_content = f.read()

    with open(os.path.join(root_public, 'app.js'), 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Вбудовуємо CSS та JS в один монолітний standalone HTML файл для миттєвого завантаження!
    html_content = html_content.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f'<style>\n{css_content}\n</style>'
    )
    
    html_content = html_content.replace(
        '</body>',
        f'<script>\n{js_content}\n</script>\n</body>'
    )

    # Завантажуємо на GitHub Gist
    payload = json.dumps({
        'description': 'Карта Подій Світловодськ (Telegram Mini App)',
        'public': True,
        'files': {
            'index.html': {
                'content': html_content
            }
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.github.com/gists',
        data=payload,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            raw_url = data['files']['index.html']['raw_url']
            
            # Перетворюємо на пряме CDN посилання з правильним Content-Type: text/html
            githack_url = raw_url.replace('https://gist.githubusercontent.com/', 'https://raw.githack.com/')
            print("==================================================")
            print("🚀 УСПІШНО РОЗГОРНУТО У ХМАРІ!")
            print("🌐 Пряме HTTPS посилання:", githack_url)
            print("==================================================")

            with open('deploy_result.json', 'w') as f_res:
                json.dump({'url': githack_url}, f_res)

    except Exception as ex:
        print("Помилка розгортання:", ex)

if __name__ == '__main__':
    bundle_and_deploy_gist()
