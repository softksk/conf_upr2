"""
Этап 1: Минимальный прототип с конфигурацией
Автор: Кирюшин Артём, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path


class Config:
    """Класс для работы с конфигурацией"""
    
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Файл не найден: {config_path}")
        
        self.config.read(config_path, encoding='utf-8')
        self._validate()
    
    def _validate(self):
        """Валидация параметров"""
        required = ['package_name', 'repository_url', 'test_mode', 
                   'package_version', 'ascii_tree', 'max_depth', 'filter_substring']
        
        if 'settings' not in self.config:
            raise ValueError("Отсутствует секция [settings]")
        
        for param in required:
            if param not in self.config['settings']:
                raise ValueError(f"Отсутствует параметр: {param}")
        
        # Проверка max_depth
        try:
            depth = int(self.config['settings']['max_depth'])
            if depth < 0:
                raise ValueError("max_depth должен быть >= 0")
        except ValueError:
            raise ValueError("max_depth должен быть целым числом")
    
    def print_all(self):
        print("=" * 60)
        print("ПАРАМЕТРЫ КОНФИГУРАЦИИ")
        print("=" * 60)
        for key, value in self.config['settings'].items():
            print(f"{key:20s} = {value}")
        print("=" * 60)


def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        config = Config(sys.argv[1])
        config.print_all()
        print("\n✓ Этап 1 выполнен успешно")
    except (FileNotFoundError, ValueError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
