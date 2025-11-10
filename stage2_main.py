"""
Этап 2: Сбор данных о зависимостях
Визуализатор графа зависимостей для пакетов Ubuntu (apt)
Вариант №11, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path
from urllib import request, error
from typing import List, Dict
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


def main():
    """Главная функция - Этап 2"""
    if len(sys.argv) != 2:
        print("Использование: python stage2_main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("ЭТАП 2: СБОР ДАННЫХ О ЗАВИСИМОСТЯХ")
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
        
        print("\n✓ Этап 2 выполнен успешно!")
        print("✓ Данные о прямых зависимостях получены")
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
