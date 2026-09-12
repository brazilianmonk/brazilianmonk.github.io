import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
t = open('pages/semester VI (09_06_2025 ‒ 31_10_2025)/Vinaya.html', encoding='utf-8', errors='replace').read()
m = re.search(r'<body[^>]*>(.*)</body>', t, re.S)
body = m.group(1)

# top-level offsets
lines = body.split('\n')
items, off = [], 0
for ln in lines:
    s = ln.strip()
    if s.startswith('<li>') and (len(ln) - len(ln.lstrip())) <= 10:
        items.append((off, ' '.join(re.sub(r'<[^>]+>', '', s).split()).lower()))
    off += len(ln) + 1
print('items:', [(o, x[:40]) for o, x in items])

def flatten(x):
    x = re.sub(r'<[^>]+>', ' ', x)
    return ' '.join(x.split())

# first 500 chars of text of each section
for i, (o, txt) in enumerate(items):
    nxt = items[i + 1][0] if i + 1 < len(items) else len(body)
    sl = flatten(body[o:nxt])
    print(f'--- section {i} ({txt[:20]}) {len(sl)}ch ---')
    print('   start:', sl[:220])
    print('   teacher mentioned:', [n for n in ('maggavihāri', 'siddhatthālaṅkāra', 'obhāsa', 'devānanda', 'sumana', 'vijitānanda') if n in sl[:2000]])
