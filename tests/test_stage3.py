"""Тесты для Этапа 3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TestRepository, DependencyGraph

def test_graph():
    try:
        repo = TestRepository('tests/test_repo.json')
        builder = DependencyGraph(repo, 3, '')
        graph = builder.build_graph_bfs_recursive('A')
        assert 'A' in graph
        assert 'B' in graph
        assert 'C' in graph
        print("✓ Тест: Построение графа")
        return True
    except Exception as e:
        print(f"✗ Тест провален: {e}")
        return False

def test_cycles():
    try:
        repo = TestRepository('tests/test_repo_cycle.json')
        builder = DependencyGraph(repo, 10, '')
        graph = builder.build_graph_bfs_recursive('A')
        assert len(graph) == 3  # A, B, C (цикл обработан)
        print("✓ Тест: Обработка циклов")
        return True
    except Exception as e:
        print(f"✗ Тест провален: {e}")
        return False

if __name__ == "__main__":
    results = [test_graph(), test_cycles()]
    print(f"\nПройдено: {sum(results)}/{len(results)}")
    sys.exit(0 if all(results) else 1)
