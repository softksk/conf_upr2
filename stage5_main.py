"""
Этап 5: Визуализация (PlantUML + ASCII-дерево)
Визуализатор графа зависимостей для пакетов Ubuntu (apt)
Вариант №11, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path
from urllib import request, error
from typing import List, Dict, Set, Optional
import gzip
import json


class Config:
    """Класс для работы с конфигурацией"""
    
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Ошибка: Файл конфигурации не найден: {config_path}")
        
        self.config.read(config_path, encoding='utf-8')
        self._validate()
    
    def _validate(self):
        """Валидация параметров конфигурации"""
        required_params = {
            'package_name': str,
            'repository_url': str,
            'test_mode': bool,
            'package_version': str,
            'ascii_tree': bool,
            'max_depth': int,
            'filter_substring': str
        }
        
        if 'settings' not in self.config:
            raise ValueError("Ошибка: Отсутствует секция [settings] в конфигурации")
        
        settings = self.config['settings']
        
        for param, param_type in required_params.items():
            if param not in settings:
                raise ValueError(f"Ошибка: Отсутствует обязательный параметр: {param}")
            
            value = settings[param]
            
            # Проверка типов
            if param_type == int:
                try:
                    int_val = int(value)
                    if param == 'max_depth' and int_val < 0:
                        raise ValueError(f"Ошибка: Параметр {param} должен быть >= 0")
                except ValueError as e:
                    if "должен быть >=" in str(e):
                        raise
                    raise ValueError(f"Ошибка: Параметр {param} должен быть целым числом, получено: {value}")
            
            elif param_type == bool:
                if value.lower() not in ['true', 'false']:
                    raise ValueError(f"Ошибка: Параметр {param} должен быть 'true' или 'false', получено: {value}")
    
    def get(self, param: str) -> str:
        """Получить значение параметра"""
        return self.config['settings'].get(param, '')
    
    def get_bool(self, param: str) -> bool:
        """Получить булево значение параметра"""
        return self.config['settings'].getboolean(param)
    
    def get_int(self, param: str) -> int:
        """Получить целочисленное значение параметра"""
        return self.config['settings'].getint(param)
    
    def print_all(self):
        """Вывести все параметры конфигурации"""
        print("=" * 60)
        print("КОНФИГУРАЦИЯ")
        print("=" * 60)
        for key, value in self.config['settings'].items():
            print(f"{key:20s} = {value}")
        print("-" * 60)
        print()


class TestRepository:
    """Класс для работы с тестовым репозиторием (JSON файл)"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Ошибка: Тестовый репозиторий не найден: {repo_path}")
        
        with open(self.repo_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"✓ Загружен тестовый репозиторий: {repo_path}")
        print(f"✓ Пакетов в репозитории: {len(self.data)}")
        print()
    
    def get_dependencies(self, package: str) -> List[str]:
        """Получить прямые зависимости пакета из тестового репозитория"""
        return self.data.get(package, [])


class AptRepository:
    """Класс для работы с реальным репозиторием Ubuntu"""
    
    def __init__(self, base_url: str, version: str):
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.cache: Dict[str, List[str]] = {}
        self.packages_data: Dict = {}
    
    def _download_packages_file(self) -> str:
        """Скачать и распарсить файл Packages.gz из репозитория Ubuntu"""
        # URL формата: http://archive.ubuntu.com/ubuntu/dists/focal/main/binary-amd64/Packages.gz
        url = f"{self.base_url}/dists/{self.version}/main/binary-amd64/Packages.gz"
        
        try:
            print(f"Загрузка репозитория из: {url}")
            print("Ожидайте, файл большой (~50 МБ)...")
            
            with request.urlopen(url, timeout=60) as response:
                compressed_data = response.read()
                print(f"✓ Загружено: {len(compressed_data) / 1024 / 1024:.1f} МБ")
                
                # Распаковка gzip
                decompressed = gzip.decompress(compressed_data).decode('utf-8')
                print(f"✓ Распаковано: {len(decompressed) / 1024 / 1024:.1f} МБ")
                return decompressed
                
        except error.HTTPError as e:
            raise RuntimeError(f"Ошибка HTTP {e.code}: {e.reason}. Проверьте URL и версию Ubuntu.")
        except error.URLError as e:
            raise RuntimeError(f"Ошибка сети: {e.reason}. Проверьте подключение к интернету.")
        except Exception as e:
            raise RuntimeError(f"Неизвестная ошибка при загрузке: {e}")
    
    def _parse_packages_file(self, content: str) -> Dict[str, Dict]:
        """Распарсить содержимое файла Packages (формат Debian)"""
        packages = {}
        current_package = {}
        current_field = None
        
        for line in content.split('\n'):
            # Пустая строка = конец описания пакета
            if line.strip() == '':
                if current_package and 'Package' in current_package:
                    pkg_name = current_package['Package']
                    packages[pkg_name] = current_package
                current_package = {}
                current_field = None
                continue
            
            # Строка с отступом = продолжение предыдущего поля
            if line.startswith(' '):
                if current_field and current_field in current_package:
                    current_package[current_field] += ' ' + line.strip()
            else:
                # Новое поле (формат: "Field: Value")
                if ':' in line:
                    field, value = line.split(':', 1)
                    current_field = field.strip()
                    current_package[current_field] = value.strip()
        
        return packages
    
    def _load_repository(self):
        """Загрузить и распарсить репозиторий (выполняется один раз)"""
        if not self.packages_data:
            content = self._download_packages_file()
            self.packages_data = self._parse_packages_file(content)
            print(f"✓ Распарсено пакетов: {len(self.packages_data)}")
            print()
    
    def get_dependencies(self, package: str) -> List[str]:
        """Получить прямые зависимости пакета из реального репозитория"""
        # Проверяем кэш
        if package in self.cache:
            return self.cache[package]
        
        # Загружаем репозиторий, если еще не загружен
        self._load_repository()
        
        # Пакет не найден в репозитории
        if package not in self.packages_data:
            print(f"⚠ Предупреждение: Пакет '{package}' не найден в репозитории")
            self.cache[package] = []
            return []
        
        pkg_info = self.packages_data[package]
        deps = []
        
        # Парсим поле Depends
        if 'Depends' in pkg_info:
            depends_str = pkg_info['Depends']
            
            # Формат: "pkg1 (>= 1.0), pkg2 | pkg3, pkg4"
            for dep_group in depends_str.split(','):
                dep_group = dep_group.strip()
                
                # Берем первый вариант из альтернатив (разделенных |)
                first_alternative = dep_group.split('|')[0].strip()
                
                # Убираем информацию о версии (в скобках)
                pkg_name = first_alternative.split('(')[0].strip()
                pkg_name = first_alternative.split('[')[0].strip()
                
                if pkg_name:
                    deps.append(pkg_name)
        
        self.cache[package] = deps
        return deps


class DependencyGraph:
    """Класс для построения и анализа графа зависимостей"""
    
    def __init__(self, repository, max_depth: int, filter_substring: str):
        self.repository = repository
        self.max_depth = max_depth
        self.filter_substring = filter_substring
        self.graph: Dict[str, List[str]] = {}
        self.visited: Set[str] = set()
    
    def _should_skip(self, package: str) -> bool:
        """Проверить, нужно ли пропустить пакет (фильтрация)"""
        if self.filter_substring and self.filter_substring in package:
            return True
        return False
    
    def build_graph_bfs_recursive(self, package: str, depth: int = 0) -> Dict[str, List[str]]:
        """
        Построить граф зависимостей алгоритмом BFS с рекурсией
        
        Args:
            package: имя пакета для анализа
            depth: текущая глубина рекурсии
        
        Returns:
            Граф зависимостей в виде словаря {пакет: [зависимости]}
        """
        # Проверка глубины
        if depth > self.max_depth:
            return self.graph
        
        # Пропускаем уже посещенные и отфильтрованные пакеты
        if package in self.visited or self._should_skip(package):
            return self.graph
        
        # Отмечаем как посещенный
        self.visited.add(package)
        
        try:
            # Получаем зависимости
            deps = self.repository.get_dependencies(package)
            
            # Фильтруем зависимости
            filtered_deps = [d for d in deps if not self._should_skip(d)]
            
            # Добавляем в граф
            self.graph[package] = filtered_deps
            
            # Рекурсивно обрабатываем зависимости (BFS подход)
            for dep in filtered_deps:
                if dep not in self.visited:
                    self.build_graph_bfs_recursive(dep, depth + 1)
        
        except Exception as e:
            print(f"⚠ Предупреждение: не удалось получить зависимости для {package}: {e}",
                  file=sys.stderr)
            self.graph[package] = []
        
        return self.graph
    
    def get_loading_order(self) -> List[str]:
        """
        Получить порядок загрузки зависимостей (топологическая сортировка)
        Использует алгоритм Кана
        """
        # Подсчет входящих рёбер
        in_degree = {pkg: 0 for pkg in self.graph}
        
        for pkg in self.graph:
            for dep in self.graph[pkg]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Очередь пакетов без входящих ребер
        queue = [pkg for pkg, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            pkg = queue.pop(0)
            result.append(pkg)
            
            # Уменьшаем счетчик для зависимостей
            for dep in self.graph.get(pkg, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result
    
    def print_graph(self):
        """Вывести граф зависимостей"""
        print("=" * 60)
        print("ГРАФ ЗАВИСИМОСТЕЙ")
        print("=" * 60)
        print(f"Всего пакетов в графе: {len(self.graph)}")
        print("-" * 60)
        
        for pkg, deps in sorted(self.graph.items()):
            if deps:
                print(f"{pkg}:")
                for dep in deps:
                    print(f"  → {dep}")
            else:
                print(f"{pkg}: (нет зависимостей)")
        print("-" * 60)


class Visualizer:
    """Класс для визуализации графа зависимостей"""
    
    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph
    
    def generate_plantuml(self) -> str:
        """Сгенерировать код PlantUML"""
        lines = ["@startuml"]
        lines.append("skinparam packageStyle rectangle")
        lines.append("skinparam defaultFontName Arial")
        lines.append("")
        
        for package, deps in self.graph.items():
            for dep in deps:
                lines.append(f'[{package}] --> [{dep}]')
        
        lines.append("@enduml")
        return '\n'.join(lines)
    
    def print_ascii_tree(self, root: str, prefix: str = "", is_last: bool = True, 
                        visited: Optional[Set[str]] = None):
        """Вывести граф в виде ASCII-дерева"""
        if visited is None:
            visited = set()
        
        connector = "└── " if is_last else "├── "
        print(prefix + connector + root)
        
        if root in visited:
            print(prefix + ("    " if is_last else "│   ") + "(цикл)")
            return
        
        visited.add(root)
        deps = self.graph.get(root, [])
        
        for i, dep in enumerate(deps):
            extension = "    " if is_last else "│   "
            self.print_ascii_tree(dep, prefix + extension, i == len(deps) - 1, visited.copy())


def main():
    """Главная функция - Этап 5"""
    if len(sys.argv) != 2:
        print("Использование: python stage5_main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("ЭТАП 5: ВИЗУАЛИЗАЦИЯ")
        print("=" * 60)
        print()
        
        # Этап 1: Загрузка конфигурации
        config = Config(sys.argv[1])
        config.print_all()
        
        # Этап 2: Инициализация репозитория
        package_name = config.get('package_name')
        
        if config.get_bool('test_mode'):
            print("Режим: ТЕСТОВЫЙ РЕПОЗИТОРИЙ")
            print("-" * 60)
            repo = TestRepository(config.get('repository_url'))
        else:
            print("Режим: РЕАЛЬНЫЙ РЕПОЗИТОРИЙ UBUNTU")
            print("-" * 60)
            repo = AptRepository(
                config.get('repository_url'),
                config.get('package_version')
            )
        
        # Получение прямых зависимостей
        print("=" * 60)
        print(f"ПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА: {package_name}")
        print("=" * 60)
        
        direct_deps = repo.get_dependencies(package_name)
        
        if direct_deps:
            print(f"\nНайдено зависимостей: {len(direct_deps)}")
            print("-" * 60)
            for i, dep in enumerate(direct_deps, 1):
                print(f"{i:3d}. {dep}")
            print("-" * 60)
        else:
            print("\n(нет зависимостей или пакет не найден)")
            print("-" * 60)
        
        print()
        
        # Этап 3: Построение графа зависимостей
        print("Построение графа транзитивных зависимостей...")
        print(f"Параметры: max_depth={config.get_int('max_depth')}, filter='{config.get('filter_substring')}'")
        print()
        
        graph_builder = DependencyGraph(
            repo,
            config.get_int('max_depth'),
            config.get('filter_substring')
        )
        
        graph = graph_builder.build_graph_bfs_recursive(package_name)
        
        # Вывод графа
        graph_builder.print_graph()
        
        # Проверка на циклы
        cycles_found = len(graph_builder.visited) < sum(1 for deps in graph.values() for _ in deps)
        if cycles_found:
            print("\n⚠ Внимание: обнаружены циклические зависимости!")
            print("Граф построен с учетом посещенных узлов.")
        
        # Этап 4: Порядок загрузки
        print("\n" + "=" * 60)
        print("ПОРЯДОК ЗАГРУЗКИ ЗАВИСИМОСТЕЙ")
        print("=" * 60)
        loading_order = graph_builder.get_loading_order()
        print(f"Всего пакетов для загрузки: {len(loading_order)}")
        print("-" * 60)
        for i, pkg in enumerate(loading_order, 1):
            print(f"{i:3d}. {pkg}")
        print("-" * 60)
        
        # Этап 5: Визуализация
        visualizer = Visualizer(graph)
        
        # PlantUML
        print("\n" + "=" * 60)
        print("PLANTUML ДИАГРАММА")
        print("=" * 60)
        plantuml_code = visualizer.generate_plantuml()
        print(plantuml_code)
        print()
        
        # Сохранение PlantUML кода в файл
        plantuml_file = f"stage5_{package_name}.puml"
        with open(plantuml_file, 'w', encoding='utf-8') as f:
            f.write(plantuml_code)
        print(f"✓ PlantUML код сохранен: {plantuml_file}")
        print()
        
        # ASCII-дерево
        if config.get_bool('ascii_tree'):
            print("=" * 60)
            print("ASCII-ДЕРЕВО ЗАВИСИМОСТЕЙ")
            print("=" * 60)
            visualizer.print_ascii_tree(package_name)
            print()
        
        print("\n✓ Этап 5 выполнен успешно!")
        print("✓ Визуализация создана")
        print()
        
    except FileNotFoundError as e:
        print(f"\nОшибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nОшибка валидации: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nОшибка загрузки данных: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nНеизвестная ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
