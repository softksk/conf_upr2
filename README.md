# Визуализатор графа зависимостей пакетов Ubuntu

**Автор:** Кирюшин Артём  
**Группа:** ИКБО-51-24  
**Дисциплина:** Конфигурационное управление  
**Вариант:** №11

---

## 1. Общее описание

Инструмент для анализа и визуализации зависимостей пакетов Ubuntu. Программа работает напрямую с репозиториями Ubuntu (парсит Packages.gz без использования apt), строит граф зависимостей, определяет порядок загрузки и создаёт визуализацию.

**Возможности:**
- Построение графа зависимостей (BFS + рекурсия)
- Обработка циклических зависимостей
- Топологическая сортировка (алгоритм Кана)
- Генерация PlantUML диаграмм
- Вывод ASCII-дерева
- Фильтрация пакетов и настройка глубины анализа

---

## 2. Описание функций и настроек

### Основные классы:

**Config** - загрузка и валидация INI-конфигурации
- `get(param)` - получить параметр как строку
- `get_bool(param)` - получить как boolean
- `get_int(param)` - получить как integer

**TestRepository** - тестовый JSON-репозиторий
- `get_dependencies(package)` - список зависимостей пакета

**AptRepository** - работа с реальным репозиторием Ubuntu
- `get_dependencies(package)` - парсит Packages.gz и возвращает зависимости

**DependencyGraph** - построение графа
- `build_graph_bfs_recursive(package, depth)` - BFS с рекурсией
- `get_loading_order()` - топологическая сортировка

**Visualizer** - визуализация
- `generate_plantuml(path)` - создаёт .puml файл
- `print_ascii_tree(root)` - выводит дерево в консоль

### Параметры конфигурации:

```ini
[settings]
package_name = curl              # Пакет для анализа
repository_url = http://...      # URL репозитория или путь к JSON
test_mode = false                # true - JSON, false - реальный репозиторий
package_version = focal          # Версия Ubuntu
max_depth = 2                    # Глубина анализа
filter_substring =               # Фильтр пакетов (пустая строка = без фильтра)
plantuml_output = graph.puml     # Путь для PlantUML
show_ascii_tree = true           # Показывать ASCII-дерево
```

---

## 3. Сборка и тестирование

### Установка:
```bash
git clone https://github.com/softksk/conf_upr2.git
cd conf_upr2
```

Требования: Python 3.7+, доступ к интернету (для реальных репозиториев)

### Запуск программы:
```bash
# Тестовый режим
python main.py config.ini

# Реальный репозиторий
python main.py config_real.ini

# Примеры для git, python3, nginx
python main.py configs/config_example1.ini
python main.py configs/config_example2.ini
python main.py configs/config_example3.ini
```

### Запуск тестов:

Проект разделён на 5 этапов в ветке `stages-clean`. Каждый этап - отдельный коммит с тестами:

```bash
# Этап 1: Конфигурация
git checkout 814e974
python tests/test_stage1.py

# Этап 2: Репозитории
git checkout 4ca4e24
python tests/test_stage2.py

# Этап 3: Граф зависимостей
git checkout 90e3ec2
python tests/test_stage3.py

# Этап 4: Порядок загрузки
git checkout 5181912
python tests/test_stage4.py

# Этап 5: Визуализация
git checkout 9845d32
python tests/test_stage5.py
```

Для возврата к финальной версии:
```bash
git checkout stages-clean
```

---

## 4. Примеры использования

### Пример 1: Простой граф (тестовый режим)

```bash
python main.py config.ini
```

**Вывод:**
```
Граф зависимостей для 'A':
Всего пакетов: 5
  A: ['B', 'C']
  B: ['D']
  C: ['D', 'E']
  D: (нет зависимостей)
  E: (нет зависимостей)

Порядок загрузки:
  1. D
  2. E
  3. B
  4. C
  5. A

PlantUML диаграмма сохранена: visualizations/graph.puml

Дерево зависимостей для 'A':
A
├── B
├── └── D
└── C
└── ├── D
└── └── E
```

### Пример 2: Реальный пакет curl

```bash
python main.py config_real.ini
```

Результат: граф из 15 пакетов, обнаружены циклы (libc6 ↔ libcrypt1), создана PlantUML диаграмма, ASCII-дерево с отметками циклов.

### Пример 3: Анализ git, python3, nginx

```bash
bash examples/run_all_examples.sh
```

Запустит анализ трёх разных пакетов и создаст диаграммы для каждого.

### Пример 4: Работа с циклами

Файл `tests/test_repo_cycle.json` содержит цикл A→B→C→A. Программа корректно обрабатывает через множество `visited` и отмечает циклы в ASCII-дереве.

---

## Этапы разработки

История коммитов в ветке `stages-clean`:

1. **814e974** - Этап 1: Конфигурация и валидация
2. **4ca4e24** - Этап 2: Парсинг репозиториев (JSON + Packages.gz)
3. **90e3ec2** - Этап 3: BFS + рекурсия + обработка циклов
4. **5181912** - Этап 4: Топологическая сортировка
5. **9845d32** - Этап 5: Визуализация (PlantUML + ASCII)

Каждый этап содержит только код своего уровня и соответствующие тесты.

---

## Структура проекта

```
conf_upr/
├── main.py                    # Основная программа
├── config.ini                 # Тестовая конфигурация
├── config_real.ini            # Конфигурация для реальных пакетов
├── configs/                   # Примеры конфигураций
│   ├── config_example1.ini
│   ├── config_example2.ini
│   └── config_example3.ini
├── tests/                     # Тесты и тестовые данные
│   ├── test_repo.json
│   ├── test_repo_cycle.json
│   └── test_stage5.py
├── examples/
│   └── run_all_examples.sh
└── visualizations/            # Сгенерированные диаграммы
    ├── graph.puml
    └── curl_graph.puml
```

---

**GitHub:** [softksk/conf_upr2](https://github.com/softksk/conf_upr2)
