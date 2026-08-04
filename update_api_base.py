import re
new_url = 'https://knock-engage-undefined-elderly.trycloudflare.com'
content = open('public/app.js', encoding='utf-8').read()
updated = re.sub(
    r"(const API_BASE = window\.location\.hostname === 'svitlovodsk-map\.surge\.sh'\s*\n\s*\? ')[^']+(')",
    lambda m: m.group(1) + new_url + m.group(2),
    content
)
open('public/app.js', 'w', encoding='utf-8').write(updated)
print('OK:', new_url)
