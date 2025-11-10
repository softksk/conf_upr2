"""
Этап 1: Минимальный прототип с конфигурацией
Визуализатор графа зависимостей для пакетов Ubuntu (apt)
Вариант №11, ИКБО-51-24
"""

import sys
import configparser
from pathlib import Path


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
        print("ЭТАП 1: КОНФИГУРАЦИЯ")
        print("=" * 60)
        print("\nПараметры конфигурации:")
        print("-" * 60)
        for key, value in self.config['settings'].items():
            print(f"{key:20s} = {value}")
        print("-" * 60)
        print()


def main():
    """Главная функция - Этап 1"""
    if len(sys.argv) != 2:
        print("Использование: python stage1_main.py <config.ini>", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Загрузка и валидация конфигурации
        config = Config(sys.argv[1])
        
        # Вывод всех параметров
        config.print_all()
        
        print("✓ Этап 1 выполнен успешно!")
        print("✓ Все параметры загружены и проверены")
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка валидации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
