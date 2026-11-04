"""JuraLab DS: style-nova.css → style-juralab.css + src/components.css (уровень 3, компонентные токены).

Запуск из корня репозитория после build-theme.py:  python3 libs/juralab-theme/scripts/build-style.py
Потом обязательно pnpm nx format:write — prettier-plugin-tailwindcss отсортирует классы в @apply.
"""
import collections
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
STYLES = os.path.join(ROOT, 'libs', 'registry', 'src', 'styles')
SRC = open(os.path.join(STYLES, 'style-nova.css'), encoding='utf-8').read()
THEME = os.path.join(ROOT, 'libs', 'juralab-theme', 'src')
SEMCSS = open(os.path.join(THEME, 'semantic.css'), encoding='utf-8').read()
SEM = sorted(set(re.findall(r'^\s+--([a-z0-9-]+):', SEMCSS, re.M)), key=len, reverse=True)
LITERAL = ['transparent', 'current', 'white', 'black', 'inherit']

# ---------- лексер ----------
def split_top(s, sep):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '[(':
            depth += 1
        elif ch in '])':
            depth -= 1
        if depth == 0 and (ch == sep if sep != ' ' else ch.isspace()):
            if cur or sep != ' ':
                out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur or sep != ' ':
        out.append(cur)
    return [x for x in out if x != ''] if sep == ' ' else out

# ---------- нормализация произвольных значений ----------
PRE = [
    ('bg-[color-mix(in_oklch,var(--muted),var(--foreground)_5%)]', 'bg-muted-hover'),
    ('bg-[oklch(from_var(--primary)_0.93_calc(c*0.4)_h)]', 'bg-bubble-tinted'),
    ('bg-[oklch(from_var(--primary)_0.3_calc(c*0.4)_h)]', 'bg-bubble-tinted'),
    ('bg-[oklch(from_var(--primary)_0.88_calc(c*0.5)_h)]', 'bg-bubble-tinted-hover'),
    ('bg-[oklch(from_var(--primary)_0.35_calc(c*0.5)_h)]', 'bg-bubble-tinted-hover'),
    (' bg-black/10 ', ' bg-overlay '),
    (' bg-white ', ' bg-thumb '),
]

# ---------- компоненты ----------
COMPS = ['alert-dialog', 'button-group', 'code-block', 'date-picker', 'dropdown-menu', 'hover-card', 'input-group', 'input-otp',
         'message-scroller', 'native-select', 'navigation-menu', 'radio-group', 'scroll-area', 'toggle-group', 'accordion', 'alert',
         'autocomplete', 'avatar', 'badge', 'breadcrumb', 'button', 'calendar', 'card', 'carousel', 'chart', 'checkbox', 'combobox',
         'command', 'dialog', 'drawer', 'empty', 'marker', 'message', 'bubble', 'attachment', 'field', 'input', 'item', 'kbd', 'label',
         'menubar', 'pagination', 'popover', 'progress', 'questionnaire', 'resizable', 'select', 'separator', 'sheet', 'sidebar',
         'skeleton', 'slider', 'toast', 'switch', 'table', 'tabs', 'textarea', 'toggle', 'tooltip', 'trace', 'rtl-flip']
COMPS.sort(key=len, reverse=True)
# общая анатомия → общий набор токенов (как в документации DS)
SHARED = {
    ('dropdown-menu', ''): 'menu',
    ('autocomplete', ''): 'listbox', ('combobox', ''): 'listbox', ('select', ''): 'listbox',
    ('alert-dialog', 'overlay'): 'dialog', ('alert-dialog', 'content'): 'dialog',
}
LISTBOX_PARTS = {'content', 'label', 'item', 'item-indicator', 'empty', 'list', 'separator', 'status', 'group', 'scroll-up-button', 'scroll-down-button'}
TITLES = {}


def comp_part(cls):
    for c in COMPS:
        if cls == c or cls.startswith(c + '-'):
            part = cls[len(c) + 1:]
            break
    else:
        raise ValueError(cls)
    part = re.sub(r'(^|-)variant-', r'\1', part)
    part = re.sub(r'(^|-)size-', r'\1', part)
    part = re.sub(r'(^|-)orientation-', r'\1', part)
    part = re.sub(r'(^|-)default$', '', part).strip('-')
    if part == 'default':
        part = ''
    return c, part


def shared_comp(c, part):
    if c in ('autocomplete', 'combobox', 'select') and part in LISTBOX_PARTS:
        return 'listbox'
    if c == 'dropdown-menu':
        return 'menu'
    if c == 'alert-dialog' and part in ('overlay', 'content'):
        return 'dialog'
    return c

# ---------- варианты → сегменты имени ----------
STATE = [
    (r'^(group-|peer-)?hover(/.*)?$', 'hover'),
    (r'^(group-|peer-)?focus(-visible|-within)?(/.*)?$', 'focus'),
    (r'^active$', 'pressed'),
    (r'^(aria-expanded|aria-\[expanded=true\])$', 'expanded'),
    (r'^(data-open|data-popup-open|data-\[state=open\])$', 'open'),
    (r'^(data-checked|aria-checked|data-\[state=checked\])$', 'checked'),
    (r'^data-unchecked$', 'unchecked'),
    (r'^(group-)?(data-active|data-\[active=true\]|data-\[state=active\])(/.*)?$', 'active'),
    (r'^(data-selected|aria-selected|data-\[selected=true\]|aria-\[selected=true\])$', 'selected'),
    (r'^(group-|peer-)?(disabled|data-disabled|aria-disabled|data-\[disabled=true\]|has-disabled|has-data-\[disabled\])(/.*)?$', 'disabled'),
    (r'^(group-|peer-)?(data-\[matches-spartan-invalid=true\]|aria-invalid|data-invalid|has-aria-invalid|has-data-\[matches-spartan-invalid=true\])(/.*)?$', 'invalid'),
    (r'^(placeholder|data-placeholder|data-\[placeholder\])$', 'placeholder'),
    (r'^data-highlighted$', 'highlighted'),
    (r'^(data-pressed|aria-pressed|data-\[state=on\])$', 'on'),
    (r'^aria-\[current=page\]$', 'current'),
    (r'^(before|after|selection|file|marker)$', None),
]
ICON = re.compile(r'(svg|ng-icon)')


INNER = [(r':hover', 'hover'), (r':focus(-visible|-within)?', 'focus'), (r':disabled|data-disabled', 'disabled'),
         (r'invalid', 'invalid'), (r'data-active|data-\[active|\[data-active', 'active'), (r'checked', 'checked'),
         (r'selected', 'selected'), (r'data-highlighted', 'highlighted')]


def strip_slot(s):
    for c in sorted(COMPS, key=len, reverse=True):
        if s.startswith(c + '-'):
            return s[len(c) + 1:]
    return s


def seg(v, comp):
    """вариант Tailwind → список сегментов имени токена"""
    core = re.sub(r'^(group-|peer-)', '', v)
    core = re.sub(r'/[a-z0-9-]+$', '', core)
    for pat, name in STATE:
        if re.match(pat, core):
            return [name if name else core]
    m = re.match(r'^in-data-\[slot=([a-z0-9-]+)\]$', v)
    if m:
        return ['in-' + strip_slot(m.group(1)).replace('-content', '')]
    out = []
    m = re.search(r'data-\[slot=([a-z0-9-]+)\]', v) or re.search(r'\[data-slot=([a-z0-9-]+)\]', v)
    if m and not v.startswith(('group-data', 'group-has', 'has-', 'in-')):
        out.append(strip_slot(m.group(1)))
    m = re.search(r'data-\[(variant|state)=([a-z-]+)\]', v)
    if m:
        out.append(m.group(2))
    if not out and ICON.search(v):
        out.append('icon')
    if v.startswith(('[', 'has-', 'group-has', '*', 'group-data', 'peer-data')):
        for pat, name in INNER:
            if re.search(pat, v):
                out.append(name)
                break
    return out  # структурные: first, last, odd, rtl, sm, supports-… → []


PROP = {'bg': 'background', 'text': 'color', 'border': 'border-color', 'ring': 'ring', 'ring-offset': 'ring-offset',
        'outline': 'outline', 'fill': 'fill', 'stroke': 'stroke', 'divide': 'divide', 'shadow': 'shadow-color',
        'caret': 'caret', 'accent': 'accent', 'decoration': 'decoration', 'inset-ring': 'inset-ring',
        'from': 'gradient-from', 'via': 'gradient-via', 'to': 'gradient-to'}
for side in 'tbsexylr':
    PROP[f'border-{side}'] = f'border-{side}-color'
PREF_RE = '|'.join(sorted(PROP, key=len, reverse=True))
COLOR_RE = re.compile(rf'^(!?)(-?)({PREF_RE})-({"|".join(SEM + LITERAL)})(?:/(\d+))?(!?)$')

# ---------- значения ----------
# (семантика, прозрачность, свойство|None) → производная семантика, как в превью DS
OPA = {
    ('ring', '50'): 'ring-halo', ('muted', '50'): 'muted-subtle', ('foreground', '10'): 'surface-border',
    ('destructive', '10'): 'destructive-subtle', ('destructive', '20'): 'destructive-subtle-hover',
    ('destructive', '30'): 'destructive-subtle-hover', ('destructive', '40'): 'destructive-border',
    ('destructive', '50'): 'destructive-border', ('destructive', '90'): 'destructive',
    ('primary', '80'): 'primary-hover', ('secondary', '80'): 'secondary-hover',
    ('primary', '5'): 'primary-subtle', ('primary', '10'): 'primary-subtle', ('primary', '20'): 'primary-subtle',
    ('primary', '30'): 'primary-subtle-border', ('primary', '40'): 'primary-subtle-border',
    ('input', '20'): 'control-subtle', ('input', '30'): 'control', ('input', '50'): 'control-disabled', ('input', '80'): 'control-disabled',
    ('background', '20'): 'kbd-tooltip', ('background', '10'): 'kbd-tooltip', ('sidebar-foreground', '70'): 'sidebar-foreground-muted',
}
OPA_RING = {('destructive', '20'): 'destructive-ring', ('destructive', '40'): 'destructive-ring', ('destructive', '30'): 'destructive-ring'}
# пары «светлая + dark:» → одна темизированная семантика
PAIRS = {
    (('background', None), ('input', '30')): 'outline',
    (('border', None), ('input', None)): 'outline-border',
    (('muted', None), ('input', '50')): 'outline-hover',
    (('muted', None), ('muted', '50')): 'ghost-hover',
    (('transparent', None), ('input', '30')): 'control',
    (None, ('input', '30')): 'control',
    (('transparent', None), ('input', '50')): 'control-hover',
    (None, ('input', '50')): 'control-hover',
    (('input', '50'), ('input', '80')): 'control-disabled',
    (('destructive', '10'), ('destructive', '20')): 'destructive-subtle',
    (('destructive', '20'), ('destructive', '30')): 'destructive-subtle-hover',
    (('destructive', '20'), ('destructive', '40')): 'destructive-ring',
    (('destructive', None), ('destructive', '50')): None,  # обрабатывается как пара с тёмным значением
    (('bubble-tinted', None), ('bubble-tinted', None)): 'bubble-tinted',
    (('bubble-tinted-hover', None), ('bubble-tinted-hover', None)): 'bubble-tinted-hover',
}


def mapc(sem, op, pref):
    if op is None:
        return f'var(--{sem})'
    if pref.startswith('border') and sem == 'destructive' and op in ('20', '30', '40', '50'):
        return 'var(--destructive-border)'
    if pref in ('ring', 'outline') and (sem, op) in OPA_RING:
        return f'var(--{OPA_RING[(sem, op)]})'
    if (sem, op) in OPA:
        return f'var(--{OPA[(sem, op)]})'
    return f'color-mix(in oklab, var(--{sem}) {op}%, transparent)'

# ---------- реестр токенов ----------
REG = collections.OrderedDict()   # name -> {'light':, 'dark':, 'comp':, 'usage': set()}
SIZE = collections.OrderedDict()


def register(base_names, light, dark, comp, usage, reg=REG):
    for i, name in enumerate(base_names + [f'{base_names[-1]}-{n}' for n in range(2, 20)]):
        if name not in reg:
            reg[name] = {'light': light, 'dark': dark, 'comp': comp, 'usage': {usage}}
            return name
        if reg[name]['light'] == light and reg[name]['dark'] == dark:
            reg[name]['usage'].add(usage)
            return name
    raise RuntimeError(name)


def tok_name(comp, part, segs, prop):
    bits = [comp] + ([part] if part else []) + [s for s in segs if s] + [prop]
    out = []
    for b in '-'.join(bits).split('-'):
        if not out or out[-1] != b:
            out.append(b)
    name = '-'.join(out)
    head, rest = name[:len(comp)], name[len(comp):]
    return head + rest.replace(f'-{comp}-', '-')


def hint(pref, token):
    return f'{pref}-(color:--{token})'

# ---------- размеры ----------
RADIUS = {'none': '0', 'xs': 'calc(var(--radius) * 0.4)', 'sm': 'calc(var(--radius) * 0.6)', 'md': 'calc(var(--radius) * 0.8)',
          'lg': 'var(--radius)', 'xl': 'calc(var(--radius) * 1.4)', '2xl': 'calc(var(--radius) * 1.8)',
          '3xl': 'calc(var(--radius) * 2.2)', '4xl': 'calc(var(--radius) * 2.6)', 'full': 'calc(infinity * 1px)'}
SIZE_U = {'h': 'height', 'min-h': 'min-height', 'size': 'size', 'gap': 'gap', 'p': 'padding', 'px': 'padding-x', 'py': 'padding-y'}
SIZE_RE = re.compile(r'^(min-h|size|gap|px|py|h|p)-(\d+(?:\.\d+)?|px)$')


def spacing(n):
    return '1px' if n == 'px' else f'calc(var(--spacing) * {n})'

# ---------- переписывание правила ----------
STATS = collections.Counter()


def rewrite(cls, apply):
    for a, b in PRE:
        apply = (' ' + apply + ' ').replace(a, b).strip()
    comp0, part = comp_part(cls)
    comp = shared_comp(comp0, part)
    toks = split_top(apply, ' ')
    parsed = []
    groups = collections.OrderedDict()
    for i, t in enumerate(toks):
        parts = split_top(t, ':')
        base, vars_ = parts[-1], parts[:-1]
        m = COLOR_RE.match(base)
        if m and not m.group(2):
            dark = 'dark' in vars_
            v = [x for x in vars_ if x != 'dark']
            key = (tuple(v), m.group(3))
            groups.setdefault(key, {'light': [], 'dark': []})['dark' if dark else 'light'].append(i)
            parsed.append(('color', v, dark, m.group(1), m.group(3), m.group(4), m.group(5), m.group(6)))
        else:
            parsed.append(('other', vars_, base))
    out = list(toks)
    for key, g in groups.items():
        v, pref = key
        L = parsed[g['light'][0]] if len(g['light']) == 1 else None
        D = parsed[g['dark'][0]] if len(g['dark']) == 1 else None
        if len(g['light']) > 1 or len(g['dark']) > 1:
            STATS['multi'] += 1
            continue
        lraw = (L[5], L[6]) if L else None
        draw = (D[5], D[6]) if D else None
        segs = [s for x in v for s in seg(x, comp)]
        name = tok_name(comp, part, segs, PROP[pref])
        alt = tok_name(comp0, part, segs, PROP[pref])
        usage = f'.spartan-{cls}'
        lit = lambda r: r and r[0] in LITERAL
        if D and (lraw, draw) in PAIRS and PAIRS[(lraw, draw)]:
            val, dval = f'var(--{PAIRS[(lraw, draw)]})', None
            STATS['pair'] += 1
        elif D and not L and (None, draw) in PAIRS:
            val, dval = f'var(--{PAIRS[(None, draw)]})', None
            STATS['pair'] += 1
        elif D and L and not lit(lraw) and not lit(draw):
            val, dval = mapc(*lraw, pref), mapc(*draw, pref)
            if val == dval:
                dval = None
            STATS['dark-override'] += 1
        else:
            # одна сторона (или литерал вроде transparent): каждую переписываем отдельно
            for side, P in (('light', L), ('dark', D)):
                if not P or P[5] in LITERAL:
                    continue
                val = mapc(P[5], P[6], pref)
                nm = register([name, alt] if name != alt else [name], val, None, comp, usage)
                vv = list(P[1]) + (['dark'] if side == 'dark' else [])
                out[g[side][0]] = ':'.join(vv + [P[3] + hint(pref, nm) + P[7]])
                STATS['single-dark' if side == 'dark' else 'single'] += 1
            continue
        nm = register([name, alt] if name != alt else [name], val, dval, comp, usage)
        P = L or D
        out[(g['light'] or g['dark'])[0]] = ':'.join(list(v) + [P[3] + hint(pref, nm) + P[7]])
        if L and D:
            out[g['dark'][0]] = None
    # размеры: только без вариантов
    for i, p in enumerate(parsed):
        if p[0] != 'other' or p[1] or out[i] is None:
            continue
        base = p[2]
        if base.startswith('rounded-') and base[8:] in RADIUS:
            nm = register([tok_name(comp, part, [], 'radius'), tok_name(comp0, part, [], 'radius')], RADIUS[base[8:]], None, comp, f'.spartan-{cls}', SIZE)
            out[i] = f'rounded-(--{nm})'
            STATS['size'] += 1
            continue
        m = SIZE_RE.match(base)
        if m:
            u, n = m.groups()
            nm = register([tok_name(comp, part, [], SIZE_U[u]), tok_name(comp0, part, [], SIZE_U[u])], spacing(n), None, comp, f'.spartan-{cls}', SIZE)
            out[i] = f'{u}-(--{nm})'
            STATS['size'] += 1
    return ' '.join(x for x in out if x is not None)

# ---------- особые случаи: произвольные свойства ----------
SPECIAL = [
    ('hover:shadow-[0_0_0_1px_var(--sidebar-accent)]', 'sidebar-menu-button-outline-hover-shadow-color', 'var(--sidebar-accent)', 'hover:shadow-[0_0_0_1px_var(--sidebar-menu-button-outline-hover-shadow-color)]'),
    (' shadow-[0_0_0_1px_var(--sidebar-border)]', 'sidebar-menu-button-outline-shadow-color', 'var(--sidebar-border)', ' shadow-[0_0_0_1px_var(--sidebar-menu-button-outline-shadow-color)]'),
]


def do_rule(m):
    cls, apply = m.group(2), m.group(4)
    for a, name, val, b in SPECIAL:
        if a in apply:
            register([name], val, None, comp_part(cls)[0] if name.startswith('sidebar') else 'chart', f'.spartan-{cls}')
            apply = apply.replace(a, b)
    return f'{m.group(1)}{m.group(3)}@apply {rewrite(cls, apply)};'


body = SRC[SRC.index('\n@scope') + 1:]
body = body[body.index('{') + 1:]
body = re.sub(r'(\.spartan-([a-z0-9-]+)[^{]*\{)(\s*)@apply\s+([^;]+);', do_rule, body)
leftover = re.findall(r'(?<![-(])dark:', body)

HEADER = """/* JuraLab DS · стиль spartan/ui на компонентных токенах.
   Основа — style-nova.css; геометрия, анимации и состояния совпадают с Nova.
   Отличия:
   - цвета, радиусы, высоты, отступы и зазоры компонентов взяты из компонентных токенов (components.css):
     bg-(color:--button-background), rounded-(--card-radius), h-(--input-height)…;
   - модификаторы прозрачности (/80, /50, /20) заменены производной семантикой (primary-hover, ring-halo, destructive-subtle…);
   - разница светлой и тёмной схем живёт в токенах, а не в dark:-утилитах.
   Сгенерировано libs/juralab-theme/scripts/build-style.py из style-nova.css — не правьте вручную. */
.style-juralab {"""
open(os.path.join(STYLES, 'style-juralab.css'), 'w', encoding='utf-8').write(HEADER + body)

# ссылки: text-primary → link (держит 4.5:1 и в Amber)
for n, t in REG.items():
    if re.search(r'(^|-)link(-[a-z]+)*-color$', n) and t['light'] == 'var(--primary)':
        t['light'] = 'var(--link)'

# ---------- components.css ----------
TITLE = {c: c.replace('-', ' ').title() for c in COMPS}
TITLE.update({'menu': 'Menu (Dropdown Menu, Context Menu, Menubar)', 'listbox': 'Listbox (Select, Combobox, Autocomplete)',
              'dialog': 'Dialog (Dialog, Alert Dialog)', 'input-otp': 'Input OTP', 'toast': 'Sonner'})
by = collections.OrderedDict()
for n, t in REG.items():
    by.setdefault(t['comp'], []).append(n)
s = ('/* JuraLab DS · уровень 3, компонентные токены\n'
     '   Сгенерировано libs/juralab-theme/scripts/build-style.py вместе со style-juralab.css. Не правьте вручную.\n'
     '   Цвета ссылаются на семантику. Если схемам нужны разные ссылки, тёмное значение — в блоке .dark ниже\n'
     '   (как colorScheme у компонентных токенов PrimeNG). Размеры — на --spacing и --radius.\n'
     '   Переопределение для одного места, как dt в PrimeNG:\n'
     '     .checkout { --button-background: var(--brand-11); } */\n\n')
s += ':where(:root, .dark, [data-preset]) {\n'
for c, names in by.items():
    s += f'\t/* {TITLE.get(c, c)} */\n' + ''.join(f'\t--{n}: {REG[n]["light"]};\n' for n in names)
s += '}\n\n/* Тёмная схема: только токены, которым нужна другая ссылка */\n:where(.dark, .dark [data-preset]) {\n'
s += ''.join(f'\t--{n}: {t["dark"]};\n' for n, t in REG.items() if t['dark'])
s += '}\n\n/* Размеры */\n:where(:root) {\n'
bys = collections.OrderedDict()
for n, t in SIZE.items():
    bys.setdefault(t['comp'], []).append(n)
for c, names in bys.items():
    s += f'\t/* {TITLE.get(c, c)} */\n' + ''.join(f'\t--{n}: {SIZE[n]["light"]};\n' for n in names)
s += '}\n'
open(os.path.join(THEME, 'components.css'), 'w', encoding='utf-8').write(s)
print(dict(STATS), 'colors', len(REG), 'dark', sum(1 for t in REG.values() if t['dark']), 'sizes', len(SIZE), 'leftover dark:', len(leftover))
