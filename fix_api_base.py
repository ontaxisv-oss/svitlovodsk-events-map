content = open('public/app.js', encoding='utf-8').read()

# Замінюємо статичні fetch виклики на динамічні з API_BASE
updated = content
updated = updated.replace("fetch('/api/", "fetch(API_BASE + '/api/")
updated = updated.replace("fetch(`/api/", "fetch(`${API_BASE}/api/")

open('public/app.js', 'w', encoding='utf-8').write(updated)
print('Done. Updated fetch calls:')

for i, line in enumerate(updated.splitlines(), 1):
    if 'fetch(' in line:
        print(f'  Line {i}: {line.strip()}')
