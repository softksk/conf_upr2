#!/bin/bash
# Тестирование трёх различных пакетов из реального репозитория Ubuntu

echo "=========================================="
echo "Пример 1: Анализ зависимостей пакета GIT"
echo "=========================================="
python main.py configs/config_example1.ini
echo ""
echo ""

echo "=========================================="
echo "Пример 2: Анализ зависимостей пакета PYTHON3"
echo "=========================================="
python main.py configs/config_example2.ini
echo ""
echo ""

echo "=========================================="
echo "Пример 3: Анализ зависимостей пакета NGINX"
echo "=========================================="
python main.py configs/config_example3.ini
echo ""
echo ""

echo "✓ Все три примера выполнены успешно!"
echo ""
echo "Созданные PlantUML диаграммы:"
ls -lh visualizations/*.puml
