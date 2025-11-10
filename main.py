"""
Визуализатор графа зависимостей для пакетов Ubuntu (apt)
Вариант №11, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path
from urllib import request, error
from typing import Dict, List, Set, Optional
import gzip
import json


class Config:
    """Класс для работы с конфигурацией"""
    
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")
        
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
            raise ValueError("Отсутствует секция [settings] в конфигурации")
        
        settings = self.config['settings']
        
        for param, param_type in required_params.items():
            if param not in settings:
                raise ValueError(f"Отсутствует обязательный параметр: {param}")
            
            value = settings[param]
            
            # Проверка типов
            if param_type == int:
                try:
                    int_val = int(value)
                    if param == 'max_depth' and int_val < 0:
                        raise ValueError(f"Параметр {param} должен быть >= 0")
                except ValueError:
                    raise ValueError(f"Параметр {param} должен быть целым числом")
            
            elif param_type == bool:
                if value.lower() not in ['true', 'false']:
                    raise ValueError(f"Параметр {param} должен быть true или false")
    
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
        """Вывести все параметры"""
        print("Конфигурация:")
        for key, value in self.config['settings'].items():
            print(f"{key} = {value}")
        print()


class TestRepository:
    """Класс для работы с тестовым репозиторием"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Тестовый репозиторий не найден: {repo_path}")
        
        with open(self.repo_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def get_dependencies(self, package: str) -> List[str]:
        """Получить зависимости пакета из тестового репозитория"""
        return self.data.get(package, [])


class AptRepository:
    """Класс для работы с реальным репозиторием Ubuntu"""
    
    def __init__(self, base_url: str, version: str):
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.cache: Dict[str, List[str]] = {}
        self.packages_data: Optional[Dict] = None
    
    def _download_packages_file(self) -> str:
        """Скачать файл Packages.gz из репозитория"""
        # Пример URL: http://archive.ubuntu.com/ubuntu/dists/focal/main/binary-amd64/Packages.gz
        url = f"{self.base_url}/dists/{self.version}/main/binary-amd64/Packages.gz"
        
        try:
            print(f"Загрузка данных из {url}...", file=sys.stderr)
            with request.urlopen(url, timeout=30) as response:
                compressed_data = response.read()
                return gzip.decompress(compressed_data).decode('utf-8')
        except error.HTTPError as e:
            raise RuntimeError(f"HTTP ошибка {e.code}: {e.reason}")
        except error.URLError as e:
            raise RuntimeError(f"Ошибка сети: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Неизвестная ошибка: {e}")
    
    def _parse_packages_file(self, content: str) -> Dict[str, Dict]:
        """Распарсить файл Packages"""
        packages = {}
        current_package = {}
        current_field = None
        
        for line in content.split('\n'):
            if line.strip() == '':
                if current_package and 'Package' in current_package:
                    pkg_name = current_package['Package']
                    packages[pkg_name] = current_package
                current_package = {}
                current_field = None
                continue
            
            if line.startswith(' '):
                # Продолжение предыдущего поля
                if current_field:
                    current_package[current_field] += ' ' + line.strip()
            else:
                # Новое поле
                if ':' in line:
                    field, value = line.split(':', 1)
                    current_field = field.strip()
                    current_package[current_field] = value.strip()
        
        return packages
    
    def _load_repository(self):
        """Загрузить и распарсить репозиторий"""
        if self.packages_data is None:
            content = self._download_packages_file()
            self.packages_data = self._parse_packages_file(content)
            print(f"Загружено {len(self.packages_data)} пакетов", file=sys.stderr)
    
    def get_dependencies(self, package: str) -> List[str]:
        """Получить прямые зависимости пакета"""
        if package in self.cache:
            return self.cache[package]
        
        self._load_repository()
        
        if package not in self.packages_data:
            self.cache[package] = []
            return []
        
        pkg_info = self.packages_data[package]
        deps = []
        
        if 'Depends' in pkg_info:
            depends_str = pkg_info['Depends']
            # Парсинг зависимостей (формат: pkg1 (>= version), pkg2 | pkg3, ...)
            for dep_group in depends_str.split(','):
                dep_group = dep_group.strip()
                # Берем первый вариант из альтернатив
                first_alt = dep_group.split('|')[0].strip()
                # Убираем информацию о версии
                pkg_name = first_alt.split('(')[0].strip()
                pkg_name = first_alt.split('[')[0].strip()
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
        """Проверить, нужно ли пропустить пакет"""
        return self.filter_substring and self.filter_substring in package
    
    def build_graph_bfs_recursive(self, package: str, depth: int = 0) -> Dict[str, List[str]]:
        """Построить граф зависимостей алгоритмом BFS с рекурсией"""
        if depth > self.max_depth:
            return self.graph
        
        if package in self.visited or self._should_skip(package):
            return self.graph
        
        self.visited.add(package)
        
        try:
            deps = self.repository.get_dependencies(package)
            filtered_deps = [d for d in deps if not self._should_skip(d)]
            self.graph[package] = filtered_deps
            
            # Рекурсивно обрабатываем зависимости
            for dep in filtered_deps:
                if dep not in self.visited:
                    self.build_graph_bfs_recursive(dep, depth + 1)
        except Exception as e:
            print(f"Предупреждение: не удалось получить зависимости для {package}: {e}", 
                  file=sys.stderr)
            self.graph[package] = []
        
        return self.graph
    
    def get_reverse_dependencies(self, target_package: str) -> List[str]:
        """Получить обратные зависимости (пакеты, которые зависят от данного)"""
        reverse_deps = []
        for pkg, deps in self.graph.items():
            if target_package in deps:
                reverse_deps.append(pkg)
        return reverse_deps
    
    def get_loading_order(self) -> List[str]:
        """Получить порядок загрузки зависимостей (топологическая сортировка)"""
        in_degree = {pkg: 0 for pkg in self.graph}
        
        for pkg in self.graph:
            for dep in self.graph[pkg]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        queue = [pkg for pkg, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            pkg = queue.pop(0)
            result.append(pkg)
            
            for dep in self.graph.get(pkg, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result


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
    
    def print_ascii_tree(self, root: str, prefix: str = "", is_last: bool = True):
        """Вывести граф в виде ASCII-дерева"""
        connector = "└── " if is_last else "├── "
        print(prefix + connector + root)
        
        deps = self.graph.get(root, [])
        for i, dep in enumerate(deps):
            extension = "    " if is_last else "│   "
            self.print_ascii_tree(dep, prefix + extension, i == len(deps) - 1)


def main():
    """Главная функция"""
    if len(sys.argv) != 2:
        print("Использование: python main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Этап 1: Загрузка конфигурации
        config = Config(sys.argv[1])
        config.print_all()
        
        # Этап 2: Получение прямых зависимостей
        package_name = config.get('package_name')
        
        if config.get_bool('test_mode'):
            repo = TestRepository(config.get('repository_url'))
        else:
            repo = AptRepository(
                config.get('repository_url'),
                config.get('package_version')
            )
        
        print(f"Прямые зависимости пакета {package_name}:")
        direct_deps = repo.get_dependencies(package_name)
        if direct_deps:
            for dep in direct_deps:
                print(f"  {dep}")
        else:
            print("  (нет зависимостей)")
        print()
        
        # Этап 3: Построение графа
        graph_builder = DependencyGraph(
            repo,
            config.get_int('max_depth'),
            config.get('filter_substring')
        )
        graph = graph_builder.build_graph_bfs_recursive(package_name)
        
        print(f"Построен граф зависимостей: {len(graph)} пакетов")
        print()
        
        # Этап 4: Обратные зависимости
        print(f"Обратные зависимости для {package_name}:")
        reverse_deps = graph_builder.get_reverse_dependencies(package_name)
        if reverse_deps:
            for pkg in reverse_deps:
                print(f"  {pkg}")
        else:
            print("  (нет обратных зависимостей)")
        print()
        
        # Порядок загрузки
        print("Порядок загрузки зависимостей:")
        loading_order = graph_builder.get_loading_order()
        for pkg in loading_order:
            print(f"  {pkg}")
        print()
        
        # Этап 5: Визуализация
        visualizer = Visualizer(graph)
        
        # PlantUML
        plantuml_code = visualizer.generate_plantuml()
        print("PlantUML диаграмма:")
        print(plantuml_code)
        print()
        
        # ASCII-дерево
        if config.get_bool('ascii_tree'):
            print("ASCII-дерево зависимостей:")
            visualizer.print_ascii_tree(package_name)
    
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()