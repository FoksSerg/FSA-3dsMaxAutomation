#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования FSA-3dsMaxAutomation
Создание тестовой планировки квартиры и генерация MAXScript
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from apartment_model import ApartmentModel, Room, OpeningType
from max_script_generator import MaxScriptGenerator


def create_test_apartment():
    """Создание тестовой квартиры с комнатами"""
    
    # Создание модели квартиры
    apartment = ApartmentModel(name="Тестовая квартира", ceiling_height=2.7)
    
    # Добавление гостиной
    living = Room(
        name="Гостиная",
        x=0, y=0,
        width=5.0, length=4.0,
        room_type="living",
        height=2.7
    )
    living.add_window(width=1.5, height=1.5, position=0.5, name="Окно в гостиной")
    living.add_door(width=0.9, height=2.1, position=0.3, name="Дверь в гостиную")
    apartment.add_room(living)
    
    # Добавление спальни
    bedroom = Room(
        name="Спальня",
        x=5.5, y=0,
        width=4.0, length=3.5,
        room_type="bedroom",
        height=2.7
    )
    bedroom.add_window(width=1.2, height=1.5, position=0.5, name="Окно в спальне")
    bedroom.add_door(width=0.9, height=2.1, position=0.4, name="Дверь в спальню")
    apartment.add_room(bedroom)
    
    # Добавление кухни
    kitchen = Room(
        name="Кухня",
        x=0, y=4.5,
        width=3.0, length=3.0,
        room_type="kitchen",
        height=2.7
    )
    kitchen.add_window(width=1.2, height=1.3, position=0.6, name="Окно в кухне")
    kitchen.add_door(width=0.9, height=2.1, position=0.5, name="Дверь в кухню")
    apartment.add_room(kitchen)
    
    # Добавление ванной
    bathroom = Room(
        name="Ванная",
        x=3.5, y=4.5,
        width=2.0, length=2.0,
        room_type="bathroom",
        height=2.7
    )
    bathroom.add_window(width=0.6, height=1.0, position=0.5, name="Окно в ванной")
    bathroom.add_door(width=0.7, height=2.0, position=0.3, name="Дверь в ванную")
    apartment.add_room(bathroom)
    
    return apartment


def main():
    """Главная функция"""
    print("=" * 70)
    print("FSA-3dsMaxAutomation - Тестовый пример")
    print("=" * 70)
    
    # Создание квартиры
    print("\n[1/3] Создание тестовой квартиры...")
    apartment = create_test_apartment()
    print(f"✓ Квартира создана: {apartment.name}")
    print(f"  Комнат: {apartment.get_rooms_count()}")
    print(f"  Площадь: {apartment.get_total_area():.2f} кв.м")
    print(f"  Высота потолка: {apartment.ceiling_height} м")
    
    # Список комнат
    print("\n[2/3] Список комнат:")
    for idx, room in enumerate(apartment.rooms, 1):
        area = room.width * room.length
        print(f"  {idx}. {room.name} ({room.room_type})")
        print(f"     Размеры: {room.width}м x {room.length}м = {area:.2f} кв.м")
        print(f"     Окон: {len(room.windows)}, Дверей: {len(room.doors)}")
    
    # Генерация MAXScript
    print("\n[3/3] Генерация MAXScript...")
    generator = MaxScriptGenerator(apartment, scale_factor=1.0)
    generator.generate_full_apartment()
    
    # Сохранение в файл
    output_dir = "tests"
    os.makedirs(output_dir, exist_ok=True)
    
    ms_file = os.path.join(output_dir, "test_apartment.ms")
    generator.save_to_file(ms_file)
    print(f"✓ MAXScript сохранен: {ms_file}")
    
    # Сохранение JSON
    json_file = os.path.join(output_dir, "test_apartment.json")
    import json
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(apartment.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"✓ JSON сохранен: {json_file}")
    
    print("\n" + "=" * 70)
    print("✓ Тестовый пример успешно выполнен!")
    print("=" * 70)
    print("\nДля использования в 3ds Max:")
    print(f"  1. Откройте 3ds Max")
    print(f"  2. Выберите MAXScript → Run Script...")
    print(f"  3. Откройте файл: {ms_file}")
    print(f"  4. 3D модель будет создана автоматически")


if __name__ == "__main__":
    main()

