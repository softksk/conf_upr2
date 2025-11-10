"""Тесты для Этапа 1"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Config

def test_valid_config():
    try:
        config = Config('config.ini')
        assert config.config['settings']['package_name'] == 'curl'
        print("✓ Тест 1: Корректная конфигурация")
        return True
    except Exception as e:
        print(f"✗ Тест 1 провален: {e}")
        return False

def test_missing_file():
    try:
        Config('nonexistent.ini')
        print("✗ Тест 2 провален: должна быть ошибка")
        return False
    except FileNotFoundError:
        print("✓ Тест 2: Отсутствующий файл")
        return True

if __name__ == "__main__":
    results = [test_valid_config(), test_missing_file()]
    print(f"\nПройдено: {sum(results)}/{len(results)}")
    sys.exit(0 if all(results) else 1)
