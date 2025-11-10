"""Тесты для Этапа 2"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TestRepository

def test_repository():
    try:
        repo = TestRepository('tests/test_repo.json')
        assert repo.get_dependencies('A') == ['B', 'C']
        assert repo.get_dependencies('B') == ['D']
        assert repo.get_dependencies('D') == []
        print("✓ Тест: Тестовый репозиторий")
        return True
    except Exception as e:
        print(f"✗ Тест провален: {e}")
        return False

if __name__ == "__main__":
    result = test_repository()
    print(f"\nПройдено: {1 if result else 0}/1")
    sys.exit(0 if result else 1)
