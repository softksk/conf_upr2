"""
Этап 5: Визуализация зависимостей (PlantUML + ASCII)
Автор: Кирюшин Артём, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path
from urllib import request, error
from typing import List, Dict, Set
import gzip
import json


class Config:
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Файл не найден: {config_path}")
        self.config.read(config_path, encoding='utf-8')
    
    def get(self, param: str) -> str:
        return self.config['settings'].get(param, '')
    
    def get_bool(self, param: str) -> bool:
        return self.config['settings'].getboolean(param)
    
    def get_int(self, param: str) -> int:
        return self.config['settings'].getint(param)


class TestRepository:
    def __init__(self, repo_path: str):
        with open(repo_path, 'r') as f:
            self.data = json.load(f)
    
    def get_dependencies(self, package: str) -> List[str]:
        return self.data.get(package, [])


class AptRepository:
    def __init__(self, base_url: str, version: str):
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.packages_data: Dict = {}
    
    def _download_packages_file(self) -> str:
        url = f"{self.base_url}/dists/{self.version}/main/binary-amd64/Packages.gz"
        with request.urlopen(url, timeout=60) as response:
            return gzip.decompress(response.read()).decode('utf-8')
    
    def _parse_packages_file(self, content: str) -> Dict[str, Dict]:
        packages, current, field = {}, {}, None
        for line in content.split('\n'):
            if not line.strip():
                if 'Package' in current:
                    packages[current['Package']] = current
                current, field = {}, None
            elif line.startswith(' ') and field:
                current[field] += ' ' + line.strip()
            elif ':' in line:
                field, value = line.split(':', 1)
                current[field.strip()] = value.strip()
        return packages
    
    def _load_repository(self):
        if not self.packages_data:
            self.packages_data = self._parse_packages_file(self._download_packages_file())
    
    def get_dependencies(self, package: str) -> List[str]:
        self._load_repository()
        if package not in self.packages_data:
            return []
        deps = []
        if 'Depends' in self.packages_data[package]:
            for dep_group in self.packages_data[package]['Depends'].split(','):
                pkg_name = dep_group.split('|')[0].split('(')[0].strip()
                if pkg_name:
                    deps.append(pkg_name)
        return deps


class DependencyGraph:
    """Построение графа зависимостей (BFS + рекурсия)"""
    def __init__(self, repository, max_depth: int, filter_substring: str):
        self.repository = repository
        self.max_depth = max_depth
        self.filter_substring = filter_substring
        self.graph: Dict[str, List[str]] = {}
        self.visited: Set[str] = set()
    
    def _should_skip(self, package: str) -> bool:
        return self.filter_substring and self.filter_substring in package
    
    def build_graph_bfs_recursive(self, package: str, depth: int = 0) -> Dict[str, List[str]]:
        """BFS с рекурсией"""
        if depth > self.max_depth or package in self.visited or self._should_skip(package):
            return self.graph
        
        self.visited.add(package)
        deps = self.repository.get_dependencies(package)
        filtered_deps = [d for d in deps if not self._should_skip(d)]
        self.graph[package] = filtered_deps
        
        for dep in filtered_deps:
            if dep not in self.visited:
                self.build_graph_bfs_recursive(dep, depth + 1)
        
        return self.graph
    
    def get_loading_order(self) -> List[str]:
        """Топологическая сортировка (алгоритм Кана)"""
        # Вычисляем входящие степени (сколько зависимостей внутри графа у каждого пакета)
        in_degree = {pkg: 0 for pkg in self.graph}
        
        # Для каждой зависимости: если A -> B, то B загружается раньше A
        for pkg in self.graph:
            deps_in_graph = [dep for dep in self.graph[pkg] if dep in self.graph]
            in_degree[pkg] = len(deps_in_graph)
        
        # Начинаем с пакетов без зависимостей (in_degree == 0)
        queue = [pkg for pkg, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Берем пакет без зависимостей
            pkg = queue.pop(0)
            result.append(pkg)
            
            # Находим все пакеты, которые зависят от текущего
            for other_pkg in self.graph:
                if pkg in self.graph[other_pkg] and other_pkg in in_degree:
                    in_degree[other_pkg] -= 1
                    if in_degree[other_pkg] == 0:
                        queue.append(other_pkg)
        
        # Если остались необработанные пакеты (цикл), добавляем их в конец
        remaining = [pkg for pkg in self.graph if pkg not in result]
        if remaining:
            result.extend(sorted(remaining))  # Добавляем в алфавитном порядке
        
        return result


class Visualizer:
    """Визуализация графа зависимостей"""
    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph
    
    def generate_plantuml(self, output_path: str):
        """Генерация PlantUML диаграммы"""
        lines = ['@startuml', '']
        for pkg, deps in sorted(self.graph.items()):
            for dep in deps:
                lines.append(f'"{pkg}" --> "{dep}"')
        lines.extend(['', '@enduml'])
        
        # Создаем директорию если не существует
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # Генерация PNG через PlantUML сервер
        self._generate_png_from_plantuml(output_path)
    
    def _generate_png_from_plantuml(self, puml_path: str):
        """Генерация PNG изображения через PlantUML сервер"""
        try:
            import zlib
            import base64
            
            # Читаем PlantUML файл
            with open(puml_path, 'r', encoding='utf-8') as f:
                plantuml_code = f.read()
            
            # Кодируем для PlantUML сервера
            zlibbed = zlib.compress(plantuml_code.encode('utf-8'))
            compressed = zlibbed[2:-4]  # Убираем заголовок и футер zlib
            encoded = base64.b64encode(compressed).decode('utf-8')
            
            # PlantUML использует специальную кодировку
            plantuml_encoding = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
            standard_encoding = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
            
            encoded_plantuml = ""
            for char in encoded:
                if char in standard_encoding:
                    idx = standard_encoding.index(char)
                    encoded_plantuml += plantuml_encoding[idx]
                else:
                    encoded_plantuml += char
            
            # Скачиваем PNG с PlantUML сервера
            url = f"http://www.plantuml.com/plantuml/png/{encoded_plantuml}"
            png_path = puml_path.replace('.puml', '.png')
            
            response = request.urlopen(url, timeout=30)
            with open(png_path, 'wb') as f:
                f.write(response.read())
            
            print(f"PNG изображение сохранено: {png_path}")
        except Exception as e:
            print(f"Не удалось создать PNG: {e}")
    
    def print_ascii_tree(self, root: str, prefix: str = '', visited: Set[str] = None):
        """Рекурсивный ASCII вывод дерева зависимостей"""
        if visited is None:
            visited = set()
        
        if root in visited:
            print(f"{prefix}{root} (цикл)")
            return
        
        visited.add(root)
        print(f"{prefix}{root}")
        
        deps = self.graph.get(root, [])
        for i, dep in enumerate(deps):
            is_last = (i == len(deps) - 1)
            connector = "└── " if is_last else "├── "
            self.print_ascii_tree(dep, prefix + connector, visited.copy())


def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        config = Config(sys.argv[1])
        package_name = config.get('package_name')
        
        if config.get_bool('test_mode'):
            repo = TestRepository(config.get('repository_url'))
        else:
            repo = AptRepository(config.get('repository_url'), config.get('package_version'))
        
        graph_builder = DependencyGraph(repo, config.get_int('max_depth'), config.get('filter_substring'))
        graph = graph_builder.build_graph_bfs_recursive(package_name)
        
        print(f"\nГраф зависимостей для '{package_name}':")
        print(f"Всего пакетов: {len(graph)}")
        for pkg, deps in sorted(graph.items()):
            print(f"  {pkg}: {deps if deps else '(нет зависимостей)'}")
        
        print("\nПорядок загрузки:")
        order = graph_builder.get_loading_order()
        for i, pkg in enumerate(order, 1):
            print(f"  {i}. {pkg}")
        
        # Визуализация
        visualizer = Visualizer(graph)
        
        plantuml_path = config.get('plantuml_output')
        if plantuml_path:
            visualizer.generate_plantuml(plantuml_path)
            print(f"\nPlantUML диаграмма сохранена: {plantuml_path}")
        
        if config.get_bool('show_ascii_tree'):
            print(f"\nДерево зависимостей для '{package_name}':")
            visualizer.print_ascii_tree(package_name)
        
        print("\n✓ Этап 5 выполнен успешно")
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
