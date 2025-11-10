"""Тесты для этапа 5: визуализация"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import TestRepository, DependencyGraph, Visualizer


def test_plantuml_generation():
    """Тест генерации PlantUML"""
    repo = TestRepository('tests/test_repo.json')
    graph_builder = DependencyGraph(repo, 3, '')
    graph = graph_builder.build_graph_bfs_recursive('A')
    
    visualizer = Visualizer(graph)
    output_path = 'visualizations/test_graph.puml'
    visualizer.generate_plantuml(output_path)
    
    assert Path(output_path).exists(), "PlantUML файл не создан"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert '@startuml' in content, "Нет начала PlantUML"
    assert '@enduml' in content, "Нет конца PlantUML"
    assert '"A" --> "B"' in content, "Нет связи A -> B"
    assert '"A" --> "C"' in content, "Нет связи A -> C"
    
    print("✓ Тест генерации PlantUML пройден")


def test_ascii_tree():
    """Тест ASCII дерева"""
    repo = TestRepository('tests/test_repo.json')
    graph_builder = DependencyGraph(repo, 3, '')
    graph = graph_builder.build_graph_bfs_recursive('A')
    
    visualizer = Visualizer(graph)
    
    print("\n--- ASCII дерево зависимостей ---")
    visualizer.print_ascii_tree('A')
    print("✓ Тест ASCII дерева пройден")


if __name__ == '__main__':
    test_plantuml_generation()
    test_ascii_tree()
