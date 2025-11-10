"""
Этап 3: Построение графа зависимостей (BFS + рекурсия)
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
        
        print("\n✓ Этап 3 выполнен успешно")
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
