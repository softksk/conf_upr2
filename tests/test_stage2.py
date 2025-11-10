"""
Тесты для Этапа 2: Сбор данных о зависимостях
"""

import sys
import os
import json

# Добавляем путь к stage2_main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from stage2_main import Config, TestRepository


def test_test_repository():
    """Тест 2.1: Работа с тестовым репозиторием"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.1: Работа с тестовым репозиторием")
    print("=" * 60)
    
    try:
        repo = TestRepository('tests/stage2_test_repo.json')
        
        # Проверяем зависимости пакета A
        deps_a = repo.get_dependencies('A')
        assert deps_a == ['B', 'C'], f"Ожидалось ['B', 'C'], получено {deps_a}"
        
        # Проверяем зависимости пакета B
        deps_b = repo.get_dependencies('B')
        assert deps_b == ['D'], f"Ожидалось ['D'], получено {deps_b}"
        
        # Проверяем пакет без зависимостей
        deps_d = repo.get_dependencies('D')
        assert deps_d == [], f"Ожидалось [], получено {deps_d}"
        
        # Проверяем несуществующий пакет
        deps_x = repo.get_dependencies('X')
        assert deps_x == [], f"Ожидалось [], получено {deps_x}"
        
        print("✓ PASSED: Тестовый репозиторий работает корректно")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_missing_repository():
    """Тест 2.2: Отсутствующий файл репозитория"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.2: Отсутствующий файл репозитория")
    print("=" * 60)
    
    try:
        _ = TestRepository('nonexistent.json')
        print("✗ FAILED: Должна быть ошибка FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False


def test_invalid_json():
    """Тест 2.3: Некорректный JSON в репозитории"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.3: Некорректный JSON в репозитории")
    print("=" * 60)
    
    # Создаем временный файл с невалидным JSON
    with open('test_invalid.json', 'w') as f:
        f.write("{ invalid json }")
    
    try:
        _ = TestRepository('test_invalid.json')
        print("✗ FAILED: Должна быть ошибка json.JSONDecodeError")
        return False
    except json.JSONDecodeError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✓ PASSED (альтернативная ошибка): {e}")
        return True
    finally:
        if os.path.exists('test_invalid.json'):
            os.remove('test_invalid.json')


def test_config_with_test_mode():
    """Тест 2.4: Конфигурация в тестовом режиме"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.4: Конфигурация в тестовом режиме")
    print("=" * 60)
    
    try:
        config = Config('stage2_config_test.ini')
        assert config.get('package_name') == 'A'
        assert config.get('repository_url') == 'tests/stage2_test_repo.json'
        assert config.get_bool('test_mode') is True
        print("✓ PASSED: Конфигурация загружена корректно")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_repository_all_packages():
    """Тест 2.5: Проверка всех пакетов в репозитории"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.5: Проверка всех пакетов в репозитории")
    print("=" * 60)
    
    try:
        repo = TestRepository('tests/stage2_test_repo.json')
        
        expected = {
            'A': ['B', 'C'],
            'B': ['D'],
            'C': ['D', 'E'],
            'D': [],
            'E': ['F'],
            'F': []
        }
        
        for pkg, expected_deps in expected.items():
            actual_deps = repo.get_dependencies(pkg)
            assert actual_deps == expected_deps, \
                f"Пакет {pkg}: ожидалось {expected_deps}, получено {actual_deps}"
        
        print("✓ PASSED: Все пакеты возвращают корректные зависимости")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_empty_dependencies():
    """Тест 2.6: Пакеты без зависимостей"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2.6: Пакеты без зависимостей")
    print("=" * 60)
    
    try:
        repo = TestRepository('tests/stage2_test_repo.json')
        
        # Проверяем все пакеты без зависимостей
        empty_deps_packages = ['D', 'F']
        for pkg in empty_deps_packages:
            deps = repo.get_dependencies(pkg)
            assert deps == [], f"Пакет {pkg} должен иметь пустой список зависимостей"
        
        print("✓ PASSED: Пакеты без зависимостей обработаны корректно")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def main():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("ЗАПУСК ТЕСТОВ ДЛЯ ЭТАПА 2")
    print("=" * 60)
    
    tests = [
        test_test_repository,
        test_missing_repository,
        test_invalid_json,
        test_config_with_test_mode,
        test_repository_all_packages,
        test_empty_dependencies
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Пройдено: {passed}/{total}")
    print(f"Успешность: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n✗ ПРОВАЛЕНО ТЕСТОВ: {total - passed}")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
