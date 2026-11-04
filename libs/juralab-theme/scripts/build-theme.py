"""JuraLab DS: tokens.json → CSS темы (уровни 1–2) и цвета в hlm-tailwind-preset.css.

Запуск из корня репозитория:  python3 libs/juralab-theme/scripts/build-theme.py
Затем:                        python3 libs/juralab-theme/scripts/build-style.py && pnpm nx format:write
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LIB = os.path.join(ROOT, 'libs', 'juralab-theme')
SRC = os.path.join(LIB, 'src')
PRESET_FILE = os.path.join(ROOT, 'libs', 'brain', 'hlm-tailwind-preset.css')
T = json.load(open(os.path.join(LIB, 'tokens.json'), encoding='utf-8'))
TOKS = T['colors']

PRESETS = ['juralab', 'neutral', 'amber']
PRESET_TITLE = {'juralab': 'JuraLab (Indigo + Slate)', 'neutral': 'Neutral (Gray)', 'amber': 'Amber (Amber + Sand)'}
DEFAULT = 'juralab'
I_SEM = [x['name'] for x in TOKS].index('background')
PRIM, SEM = TOKS[:I_SEM], TOKS[I_SEM:]

HEAD = ('/* JuraLab DS · {what}\n'
        '   Сгенерировано scripts/build-theme.py из tokens.json. Не правьте вручную. */\n\n')


def css_val(v):
    return re.sub(r'\{([a-z0-9-]+)\}', r'var(--\1)', v)


def val(tok, preset, scheme):
    v = tok['value']
    return v[f'{preset}-{scheme}'] if isinstance(v, dict) else v


def block(sel, decls, comment=None):
    if not decls:
        return ''
    c = f'/* {comment} */\n' if comment else ''
    body = '\n'.join(f'\t--{n}: {css_val(v)};' for n, v in decls)
    return f'{c}{sel} {{\n{body}\n}}\n\n'


def sel_light(p):
    if p == DEFAULT:
        return f':where(:root, [data-preset="{p}"])'
    return f':where([data-preset="{p}"], [data-preset="{p}"] .dark)'


def sel_dark(p):
    if p == DEFAULT:
        return f':where(.dark, .dark [data-preset="{p}"])'
    return f':where(.dark[data-preset="{p}"], .dark [data-preset="{p}"], [data-preset="{p}"] .dark)'


def write(rel, text):
    path = os.path.join(SRC, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text.rstrip() + '\n')


# 1. Шкалы: по файлу на пресет
for p in PRESETS:
    s = HEAD.format(what=f'пресет {PRESET_TITLE[p]}: уровень 1, шкалы Radix Colors')
    s += ('/* Пресет выбирается атрибутом data-preset на <html> или на любом контейнере;\n'
          f'   без атрибута действует {DEFAULT}. Тёмная схема — класс .dark, как в spartan. */\n\n')
    for sch, sel in (('light', sel_light(p)), ('dark', sel_dark(p))):
        s += block(sel, [(t['name'], val(t, p, sch)) for t in PRIM], 'светлая схема' if sch == 'light' else 'тёмная схема')
    write(f'presets/{p}.css', s)

# 2. Семантика: база → тёмная → отличия пресетов. :where() — нулевая специфичность.
SCOPE = ':where(:root, .dark, [data-preset])'
s = HEAD.format(what='уровень 2, семантика')
s += ('/* Селекторы в :where() — нулевая специфичность, любое ваше переопределение ниже по коду побеждает.\n'
      '   .dark и [data-preset] в селекторах нужны, чтобы var() пересчитывались во вложенном контейнере. */\n\n')
s += block(SCOPE, [(t['name'], val(t, DEFAULT, 'light')) for t in SEM], f'база: {DEFAULT}, светлая схема')
dark = [(t['name'], val(t, DEFAULT, 'dark')) for t in SEM if val(t, DEFAULT, 'dark') != val(t, DEFAULT, 'light')]
s += block(':where(.dark, .dark [data-preset])', dark, 'тёмная схема (все пресеты)')
dark_d = dict(dark)
for p in PRESETS:
    if p == DEFAULT:
        continue
    lo = [(t['name'], val(t, p, 'light')) for t in SEM if val(t, p, 'light') != val(t, DEFAULT, 'light')]
    s += block(sel_light(p), lo, f'пресет {p}: отличия от базы')
    lo_d = dict(lo)
    do = [(t['name'], val(t, p, 'dark')) for t in SEM
          if val(t, p, 'dark') != lo_d.get(t['name'], dark_d.get(t['name'], val(t, DEFAULT, 'light')))]
    s += block(sel_dark(p), do, f'пресет {p}, тёмная схема')
s += ':where(:root) {\n\tcolor-scheme: light;\n}\n\n:where(.dark) {\n\tcolor-scheme: dark;\n}\n'
write('semantic.css', s)

# 3. База: радиус и шрифты
fam = T['fonts']
write('base.css', HEAD.format(what='база: радиус и шрифты') +
      ':where(:root) {\n\t/* единственный радиус, который стоит менять: шкала radius-* — множители от него */\n'
      f'\t--radius: 0.625rem;\n\t--font-sans: {fam["sans"]};\n\t--font-mono: {fam["mono"]};\n}}\n')

# 4. Точка входа
write('juralab-theme.css', HEAD.format(what='точка входа темы') +
      '/* Подключайте в styles.css после Tailwind и hlm-tailwind-preset.css.\n'
      '   Ненужный пресет можно убрать из списка. */\n' +
      "@import './base.css';\n" + ''.join(f"@import './presets/{p}.css';\n" for p in PRESETS) +
      "@import './semantic.css';\n@import './components.css';\n")

# 5. Цвета в hlm-tailwind-preset.css: недостающие --color-* добавляются блоком между маркерами
#    в конец первого @theme inline (перед --radius-sm); исходные строки spartan не трогаются.
BEGIN, END = '\t/* juralab:colors:begin */', '\t/* juralab:colors:end */'
preset = open(PRESET_FILE, encoding='utf-8').read()
preset = re.sub(r'\n' + re.escape(BEGIN) + r'.*?' + re.escape(END), '', preset, flags=re.S)
have = set(re.findall(r'--color-([a-z0-9-]+):', preset))
sem_new = [t['name'] for t in SEM if t['name'] not in have]
lines = [BEGIN, '\t/* JuraLab DS · производная семантика: hover:bg-primary-hover, ring-ring-halo, text-link… */']
lines += [f'\t--color-{n}: var(--{n});' for n in sem_new]
lines += ['\t/* JuraLab DS · шкалы пресета: bg-brand-3, text-neutral-11, border-danger-a8… */']
lines += [f'\t--color-{t["name"]}: var(--{t["name"]});' for t in PRIM]
lines += [END]
i = preset.index('\t--radius-sm:')
preset = preset[:i] + '\n'.join(lines) + '\n' + preset[i:]
open(PRESET_FILE, 'w', encoding='utf-8').write(preset)

print(f'шкалы: {len(PRIM)}, семантика: {len(SEM)}, пресеты: {len(PRESETS)}')
