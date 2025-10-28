#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSA-3dsMaxAutomation - Система сборки
Универсальный скрипт для сборки исполняемых файлов на всех платформах
"""

# Глобальные переменные проекта
PROJECT_NAME = "FSA-3dsMaxAutomation"
VERSION = "V1.0.0 (2025.10.26)"
DEVELOPER = "@FoksSegr"

import os
import sys
import platform
import subprocess
import shutil

def print_header():
    """Вывод заголовка"""
    print("=" * 70)
    print(f"FSA-3dsMaxAutomation - Система сборки")
    print(f"Версия: {VERSION}")
    print(f"Разработчик: {DEVELOPER}")
    print("=" * 70)


def check_pyinstaller():
    """Проверка установки PyInstaller"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller установлен (версия: {PyInstaller.__version__})")
        return True
    except ImportError:
        print("✗ PyInstaller не установлен")
        print("  Установка PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller установлен")
        return True


def clean_build():
    """Очистка временных файлов сборки"""
    print("\n[ШАГ 1/5] Очистка временных файлов...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for item in dirs_to_clean:
        if os.path.exists(item):
            shutil.rmtree(item)
            print(f"  Удалено: {item}")
    
    for item in files_to_clean:
        files = subprocess.run(['find', '.', '-name', item], capture_output=True)
        for file in files.stdout.decode().strip().split('\n'):
            if file:
                os.remove(file)
                print(f"  Удалено: {file}")


def get_build_command():
    """Получить команду сборки для текущей платформы"""
    system = platform.system()
    
    base_cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=FSA-3dsMaxAutomation',
        '--distpath=./dist',
        '--workpath=./build',
        '--specpath=./build',
        '--icon=NONE' if system != 'Windows' else '',  # Добавить иконку если есть
        'src/apartment_gui.py'
    ]
    
    # Убираем пустые строки
    return [item for item in base_cmd if item]


def build_application():
    """Сборка приложения"""
    print("\n[ШАГ 2/5] Проверка зависимостей...")
    check_pyinstaller()
    
    print("\n[ШАГ 3/5] Компиляция исполняемого файла...")
    
    build_cmd = get_build_command()
    print(f"Команда: {' '.join(build_cmd)}")
    
    result = subprocess.run(build_cmd)
    
    if result.returncode == 0:
        print("\n✓ Сборка успешно завершена!")
        
        # Проверка результата
        system = platform.system()
        if system == "Windows":
            exe_path = "dist/FSA-3dsMaxAutomation.exe"
            if os.path.exists(exe_path):
                print(f"✓ Исполняемый файл: {exe_path}")
        elif system == "Darwin":
            app_path = "dist/FSA-3dsMaxAutomation.app"
            if os.path.exists(app_path):
                print(f"✓ Приложение: {app_path}")
        else:  # Linux
            exe_path = "dist/FSA-3dsMaxAutomation"
            if os.path.exists(exe_path):
                print(f"✓ Исполняемый файл: {exe_path}")
        
        return True
    else:
        print("\n✗ Ошибка при сборке")
        return False


def create_output_structure():
    """Создание структуры выходных директорий"""
    print("\n[ШАГ 4/5] Создание структуры выходных директорий...")
    
    dist_path = "./dist/FSA-3dsMaxAutomation"
    if not os.path.exists(dist_path):
        os.makedirs(dist_path)
        print(f"  Создано: {dist_path}")
    
    # Копирование необходимых файлов
    files_to_copy = ['README.md', 'ASSISTANT_RULES.md']
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, dist_path)
            print(f"  Скопировано: {file}")


def post_build_cleanup():
    """Очистка после сборки"""
    print("\n[ШАГ 5/5] Очистка временных файлов...")
    
    # Удаление .spec файла
    spec_file = "build/apartment_gui.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"  Удалено: {spec_file}")
    
    print("✓ Временные файлы очищены")


def main():
    """Главная функция"""
    print_header()
    
    # Определение платформы
    system = platform.system()
    print(f"\nПлатформа: {system} ({platform.machine()})")
    
    # Изменение директории на корень проекта
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    print(f"Рабочая директория: {os.getcwd()}")
    
    try:
        # Шаг 1: Очистка
        clean_build()
        
        # Шаг 2-3: Сборка
        if build_application():
            # Шаг 4: Структура
            create_output_structure()
            
            # Шаг 5: Очистка
            post_build_cleanup()
            
            print("\n" + "=" * 70)
            print("✓ Сборка проекта завершена успешно!")
            print("=" * 70)
            
            # Информация о результатах
            system = platform.system()
            if system == "Windows":
                print(f"\n✓ Исполняемый файл: dist/FSA-3dsMaxAutomation.exe")
            elif system == "Darwin":
                print(f"\n✓ Приложение: dist/FSA-3dsMaxAutomation.app")
            else:
                print(f"\n✓ Исполняемый файл: dist/FSA-3dsMaxAutomation")
            
            print("\nДля запуска приложения:")
            if system == "Windows":
                print("  cd dist && FSA-3dsMaxAutomation.exe")
            elif system == "Darwin":
                print("  open dist/FSA-3dsMaxAutomation.app")
            else:
                print("  cd dist && ./FSA-3dsMaxAutomation")
        
    except Exception as e:
        print(f"\n✗ Ошибка при сборке: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

