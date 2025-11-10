"""
Этап 2: Сбор данных о зависимостях
Автор: Кирюшин Артём, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path
from urllib import request, error
from typing import List, Dict
import gzip
import json


class Config:
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Файл не найден: {config_path}")
        self.config.read(config_path, encoding='utf-8')
        self._validate()
    
    def _validate(self):
        required = ['package_name', 'repository_url', 'test_mode', 
                   'package_version', 'ascii_tree', 'max_depth', 'filter_substring']
        if 'settings' not in self.config:
            raise ValueError("Отсутствует секция [settings]")
        for param in required:
            if param not in self.config['settings']:
                raise ValueError(f"Отсутствует параметр: {param}")
    
    def get(self, param: str) -> str:
        return self.config['settings'].get(param, '')
    
    def get_bool(self, param: str) -> bool:
        return self.config['settings'].getboolean(param)


class TestRepository:
    """Работа с тестовым репозиторием (JSON)"""
    def __init__(self, repo_path: str):
        if not Path(repo_path).exists():
            raise FileNotFoundError(f"Репозиторий не найден: {repo_path}")
        with open(repo_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def get_dependencies(self, package: str) -> List[str]:
        return self.data.get(package, [])


class AptRepository:
    """Работа с реальным репозиторием Ubuntu"""
    def __init__(self, base_url: str, version: str):
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.packages_data: Dict = {}
    
    def _download_packages_file(self) -> str:
        url = f"{self.base_url}/dists/{self.version}/main/binary-amd64/Packages.gz"
        try:
            print(f"Загрузка {url}...", file=sys.stderr)
            with request.urlopen(url, timeout=60) as response:
                compressed = response.read()
                return gzip.decompress(compressed).decode('utf-8')
        except error.HTTPError as e:
            raise RuntimeError(f"HTTP ошибка {e.code}: {e.reason}")
    
    def _parse_packages_file(self, content: str) -> Dict[str, Dict]:
        packages = {}
        current = {}
        current_field = None
        
        for line in content.split('\n'):
            if line.strip() == '':
                if current and 'Package' in current:
                    packages[current['Package']] = current
                current = {}
                current_field = None
            elif line.startswith(' '):
                if current_field:
                    current[current_field] += ' ' + line.strip()
            elif ':' in line:
                field, value = line.split(':', 1)
                current_field = field.strip()
                current[current_field] = value.strip()
        
        return packages
    
    def _load_repository(self):
        if not self.packages_data:
            content = self._download_packages_file()
            self.packages_data = self._parse_packages_file(content)
            print(f"Загружено пакетов: {len(self.packages_data)}", file=sys.stderr)
    
    def get_dependencies(self, package: str) -> List[str]:
        self._load_repository()
        
        if package not in self.packages_data:
            return []
        
        pkg_info = self.packages_data[package]
        deps = []
        
        if 'Depends' in pkg_info:
            for dep_group in pkg_info['Depends'].split(','):
                first_alt = dep_group.split('|')[0].strip()
                pkg_name = first_alt.split('(')[0].strip()
                if pkg_name:
                    deps.append(pkg_name)
        
        return deps


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
        
        print(f"\nПрямые зависимости пакета '{package_name}':")
        deps = repo.get_dependencies(package_name)
        if deps:
            for i, dep in enumerate(deps, 1):
                print(f"  {i}. {dep}")
        else:
            print("  (нет зависимостей)")
        
        print("\n✓ Этап 2 выполнен успешно")
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
