"""Тесты для этапа 4: порядок загрузки"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import Config, TestRepository, DependencyGraph


def test_loading_order():
    """Тест топологической сортировки"""
    repo = TestRepository('tests/test_repo.json')
    graph_builder = DependencyGraph(repo, 3, '')
    graph_builder.build_graph_bfs_recursive('A')
    order = graph_builder.get_loading_order()
    
    # D и E должны быть перед B и C, B и C перед A
    d_pos = order.index('D')
    e_pos = order.index('E')
    b_pos = order.index('B')
    c_pos = order.index('C')
    a_pos = order.index('A')
    
    assert d_pos < b_pos, "D должен быть перед B"
    assert d_pos < c_pos, "D должен быть перед C"
    assert e_pos < c_pos, "E должен быть перед C"
    assert b_pos < a_pos, "B должен быть перед A"
    assert c_pos < a_pos, "C должен быть перед A"
    print("✓ Тест порядка загрузки пройден")


if __name__ == '__main__':
    test_loading_order()
