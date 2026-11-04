# JuraLab DS

Тема и стиль компонентов дизайн-системы JuraLab DS для spartan/ui и Tailwind v4.

Токены устроены в три уровня:

1. **Шкалы** Radix Colors: `brand-*`, `neutral-*`, `danger-*`, по 12 сплошных и 12 альфа-шагов.
2. **Семантика.** Переменные spartan с прежними именами и производные токены: `primary-hover`, `ring-halo`, `control`, `link`.
3. **Компонентные токены**: `--button-background`, `--input-height`, `--card-radius`.

Есть три пресета — JuraLab, Neutral и Amber, — каждый в светлой и тёмной схеме.

## Что где лежит

| Путь                                         | Что это                                                                         |
| -------------------------------------------- | ------------------------------------------------------------------------------- |
| `libs/juralab-theme/tokens.json`             | Источник уровней 1–2: шкалы и семантика по шести темам                          |
| `libs/juralab-theme/src/presets/*.css`       | Уровень 1: шкалы, по файлу на пресет                                            |
| `libs/juralab-theme/src/semantic.css`        | Уровень 2: семантика                                                            |
| `libs/juralab-theme/src/components.css`      | Уровень 3: компонентные токены (цвета и размеры)                                |
| `libs/juralab-theme/src/juralab-theme.css`   | Точка входа темы                                                                |
| `libs/registry/src/styles/style-juralab.css` | Стиль `juralab`: правила Nova, переписанные на компонентные токены              |
| `libs/brain/hlm-tailwind-preset.css`         | Блок `juralab:colors` — новые цвета Tailwind: `bg-primary-hover`, `bg-brand-3`… |
| `libs/juralab-theme/scripts/`                | Генераторы                                                                      |

Всё в `src/`, `style-juralab.css` и блок `juralab:colors` — сгенерированные файлы. Руками их не правьте.

## Как менять

Цвета и семантику меняйте в `tokens.json`, затем запустите из корня репозитория:

```bash
python3 libs/juralab-theme/scripts/build-theme.py   # tokens.json → src/*.css и блок цветов в пресете
python3 libs/juralab-theme/scripts/build-style.py   # style-nova.css → style-juralab.css и src/components.css
pnpm nx format:write                                # prettier-plugin-tailwindcss отсортирует классы в @apply
```

`build-style.py` нужно перезапускать и после обновления `style-nova.css` из upstream spartan: стиль `juralab` выводится из Nova автоматически.

Как `build-style.py` переписывает правила:

- **Цвета.** Цветовая утилита становится токеном `--компонент-[часть]-[состояние]-свойство`. Например, `hover:bg-primary/80` в `.spartan-button-variant-default` становится `hover:bg-(color:--button-hover-background)`, а токен ссылается на `primary-hover`.
- **Прозрачности.** Модификаторы `/80`, `/50`, `/20` заменяются производной семантикой из таблицы `OPA`.
- **Пары «светлая + `dark:`».** Они сворачиваются в один токен:
  - если подходит темизированная семантика (таблица `PAIRS`: `outline`, `control`, `ghost-hover`…), токен ссылается на неё;
  - иначе тёмное значение уходит в блок `.dark` в `components.css`.
- **Размеры.** Радиусы, высоты, отступы и зазоры без вариантов становятся токенами `--button-height`, `--button-sm-height`, `--card-radius`.
- **Общие наборы токенов.**
  - Dropdown Menu — `menu-*`.
  - Содержимое Select, Combobox и Autocomplete — `listbox-*`.
  - Оверлей и окно Alert Dialog — `dialog-*`.

## Подключение в приложении

1. В `components.json` укажите `"style": "juralab"` и сгенерируйте компоненты: `ng g @spartan-ng/cli:ui`. Например, в `hlm-button.ts` окажется `bg-(color:--button-background) h-(--button-height)`, а не `bg-primary h-8`.
2. В `styles.css` удалите блоки `:root { --background: … }` и `:root.dark { … }`, которые записал `ui-theme`. Селекторы темы обёрнуты в `:where()`, и старые блоки их перекроют.
3. Подключите тему:

```css
@import 'tailwindcss';
@import '@spartan-ng/brain/hlm-tailwind-preset.css';
@import '<путь>/libs/juralab-theme/src/juralab-theme.css';
```

4. Выберите тему атрибутами на `<html>` или на любом контейнере:

```html
<html data-preset="amber" class="dark"></html>
```

Без атрибута действует JuraLab, без класса `.dark` — светлая схема.

## Переопределения

```css
:root {
	--ring: var(--brand-11); /* семантика для всей системы */
	--button-radius: 9999px; /* компонент везде */
}
.checkout {
	--button-background: var(--brand-11); /* компонент в одном месте, как dt в PrimeNG */
}
```

## Ограничения

- **docs-приложение.** Стиль `juralab` есть в `STYLES`, но в `apps/app` он не подключён. В переключателе стилей документации превью `juralab` будут без темы.
- **Вложенные пресеты.** Контейнер `data-preset="juralab"` внутри другого пресета, а в нём ещё `.dark`, получит тёмную схему внешнего пресета.
