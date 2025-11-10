"""
Тесты для Этапа 1: Минимальный прототип с конфигурацией
"""

import sys
import os

# Добавляем путь к stage1_main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from stage1_main import Config


def test_valid_config():
    """Тест 1.1: Корректная конфигурация"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.1: Корректная конфигурация")
    print("=" * 60)
    
    try:
        config = Config('stage1_config.ini')
        assert config.get('package_name') == 'curl'
        assert config.get('repository_url') == 'http://archive.ubuntu.com/ubuntu'
        assert config.get_bool('test_mode') == False
        assert config.get('package_version') == 'focal'
        assert config.get_bool('ascii_tree') == True
        assert config.get_int('max_depth') == 2
        assert config.get('filter_substring') == ''
        print("✓ PASSED: Все параметры загружены корректно")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_missing_file():
    """Тест 1.2: Отсутствующий файл конфигурации"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.2: Отсутствующий файл конфигурации")
    print("=" * 60)
    
    try:
        config = Config('nonexistent.ini')
        print("✗ FAILED: Должна быть ошибка FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False


def test_missing_parameter():
    """Тест 1.3: Отсутствующий обязательный параметр"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.3: Отсутствующий обязательный параметр")
    print("=" * 60)
    
    # Создаем временный конфиг без параметра package_name
    config_content = """[settings]
repository_url = http://archive.ubuntu.com/ubuntu
test_mode = false
package_version = focal
ascii_tree = true
max_depth = 2
filter_substring =
"""
    with open('test_invalid_config.ini', 'w') as f:
        f.write(config_content)
    
    try:
        config = Config('test_invalid_config.ini')
        print("✗ FAILED: Должна быть ошибка ValueError")
        return False
    except ValueError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False
    finally:
        if os.path.exists('test_invalid_config.ini'):
            os.remove('test_invalid_config.ini')


def test_invalid_int():
    """Тест 1.4: Некорректное целочисленное значение"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.4: Некорректное целочисленное значение")
    print("=" * 60)
    
    config_content = """[settings]
package_name = test
repository_url = http://example.com
test_mode = false
package_version = focal
ascii_tree = true
max_depth = invalid
filter_substring =
"""
    with open('test_invalid_int.ini', 'w') as f:
        f.write(config_content)
    
    try:
        config = Config('test_invalid_int.ini')
        print("✗ FAILED: Должна быть ошибка ValueError")
        return False
    except ValueError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False
    finally:
        if os.path.exists('test_invalid_int.ini'):
            os.remove('test_invalid_int.ini')


def test_negative_depth():
    """Тест 1.5: Отрицательная глубина"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.5: Отрицательная глубина анализа")
    print("=" * 60)
    
    config_content = """[settings]
package_name = test
repository_url = http://example.com
test_mode = false
package_version = focal
ascii_tree = true
max_depth = -1
filter_substring =
"""
    with open('test_negative_depth.ini', 'w') as f:
        f.write(config_content)
    
    try:
        config = Config('test_negative_depth.ini')
        print("✗ FAILED: Должна быть ошибка ValueError")
        return False
    except ValueError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False
    finally:
        if os.path.exists('test_negative_depth.ini'):
            os.remove('test_negative_depth.ini')


def test_invalid_bool():
    """Тест 1.6: Некорректное булево значение"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1.6: Некорректное булево значение")
    print("=" * 60)
    
    config_content = """[settings]
package_name = test
repository_url = http://example.com
test_mode = yes
package_version = focal
ascii_tree = true
max_depth = 2
filter_substring =
"""
    with open('test_invalid_bool.ini', 'w') as f:
        f.write(config_content)
    
    try:
        config = Config('test_invalid_bool.ini')
        print("✗ FAILED: Должна быть ошибка ValueError")
        return False
    except ValueError as e:
        print(f"✓ PASSED: Корректная обработка ошибки: {e}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Неожиданная ошибка: {e}")
        return False
    finally:
        if os.path.exists('test_invalid_bool.ini'):
            os.remove('test_invalid_bool.ini')


def main():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("ЗАПУСК ТЕСТОВ ДЛЯ ЭТАПА 1")
    print("=" * 60)
    
    tests = [
        test_valid_config,
        test_missing_file,
        test_missing_parameter,
        test_invalid_int,
        test_negative_depth,
        test_invalid_bool
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
