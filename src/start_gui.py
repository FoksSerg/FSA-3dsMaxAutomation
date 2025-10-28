#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSA-3dsMaxAutomation - Запуск GUI приложения
Точка входа для запуска графического интерфейса
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apartment_gui import main

if __name__ == "__main__":
    main()

