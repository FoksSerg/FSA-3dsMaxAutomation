#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSA-3dsMaxAutomation - Модель данных квартиры
Модуль для хранения и управления данными планировки квартиры
"""

# Глобальные переменные проекта
PROJECT_NAME = "FSA-3dsMaxAutomation"
VERSION = "V1.0.0 (2025.10.26)"
DEVELOPER = "@FoksSegr"

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class OpeningType(Enum):
    """Типы проемов"""
    DOOR = "door"
    WINDOW = "window"
    ARCH = "arch"


@dataclass
class Opening:
    """Проем (дверь, окно, арка)"""
    opening_type: OpeningType
    width: float = 0.9  # Ширина в метрах
    height: float = 2.1  # Высота в метрах
    position: float = 0.5  # Позиция на стене (0.0-1.0)
    name: str = ""
    material: Optional[str] = None


@dataclass
class Wall:
    """Стена квартиры"""
    x1: float  # Начало стены (метры)
    y1: float
    x2: float  # Конец стены (метры)
    y2: float
    height: float = 2.7  # Высота стены в метрах
    thickness: float = 0.2  # Толщина стены в метрах
    name: str = "Стена"
    openings: List[Opening] = field(default_factory=list)
    
    def add_opening(self, opening: Opening):
        """Добавить проем в стену"""
        self.openings.append(opening)
    
    def get_length(self) -> float:
        """Получить длину стены"""
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return (dx ** 2 + dy ** 2) ** 0.5


@dataclass
class Room:
    """Комната в квартире"""
    name: str
    x: float  # Координата левого нижнего угла
    y: float
    width: float  # Ширина комнаты (метры)
    length: float  # Длина комнаты (метры)
    height: float = 2.7  # Высота потолка (метры)
    room_type: str = "living"  # Тип комнаты (living, bedroom, kitchen, bathroom)
    windows: List[Opening] = field(default_factory=list)
    doors: List[Opening] = field(default_factory=list)
    materials: dict = field(default_factory=dict)  # Материалы для стен, пола, потолка
    
    def add_window(self, width: float, height: float, position: float, name: str = ""):
        """Добавить окно"""
        window = Opening(
            opening_type=OpeningType.WINDOW,
            width=width,
            height=height,
            position=position,
            name=name if name else f"Окно в {self.name}"
        )
        self.windows.append(window)
    
    def add_door(self, width: float, height: float, position: float, name: str = ""):
        """Добавить дверь"""
        door = Opening(
            opening_type=OpeningType.DOOR,
            width=width,
            height=height,
            position=position,
            name=name if name else f"Дверь в {self.name}"
        )
        self.doors.append(door)


class ApartmentModel:
    """Модель квартиры - основной класс для хранения всех данных"""
    
    def __init__(self, name: str = "Новая квартира", ceiling_height: float = 2.7):
        self.name = name
        self.ceiling_height = ceiling_height
        self.rooms: List[Room] = []
        self.walls: List[Wall] = []
        self.metadata = {
            "created": "",
            "modified": "",
            "author": "",
            "project_path": ""
        }
    
    def add_room(self, room: Room):
        """Добавить комнату в квартиру"""
        self.rooms.append(room)
    
    def add_wall(self, wall: Wall):
        """Добавить стену"""
        self.walls.append(wall)
    
    def get_total_area(self) -> float:
        """Получить общую площадь квартиры"""
        return sum(room.width * room.length for room in self.rooms)
    
    def get_rooms_count(self) -> int:
        """Получить количество комнат"""
        return len(self.rooms)
    
    def to_dict(self) -> dict:
        """Преобразовать модель в словарь для сохранения"""
        return {
            "name": self.name,
            "ceiling_height": self.ceiling_height,
            "rooms": [
                {
                    "name": room.name,
                    "x": room.x,
                    "y": room.y,
                    "width": room.width,
                    "length": room.length,
                    "height": room.height,
                    "room_type": room.room_type,
                    "windows": [
                        {
                            "type": w.opening_type.value,
                            "width": w.width,
                            "height": w.height,
                            "position": w.position,
                            "name": w.name
                        } for w in room.windows
                    ],
                    "doors": [
                        {
                            "type": d.opening_type.value,
                            "width": d.width,
                            "height": d.height,
                            "position": d.position,
                            "name": d.name
                        } for d in room.doors
                    ],
                    "materials": room.materials
                } for room in self.rooms
            ],
            "walls": [
                {
                    "x1": wall.x1,
                    "y1": wall.y1,
                    "x2": wall.x2,
                    "y2": wall.y2,
                    "height": wall.height,
                    "thickness": wall.thickness,
                    "name": wall.name,
                    "openings": [
                        {
                            "type": o.opening_type.value,
                            "width": o.width,
                            "height": o.height,
                            "position": o.position,
                            "name": o.name
                        } for o in wall.openings
                    ]
                } for wall in self.walls
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ApartmentModel':
        """Создать модель из словаря"""
        apartment = cls(data.get("name", "Новая квартира"), 
                       data.get("ceiling_height", 2.7))
        
        # Загружаем комнаты
        for room_data in data.get("rooms", []):
            room = Room(
                name=room_data["name"],
                x=room_data["x"],
                y=room_data["y"],
                width=room_data["width"],
                length=room_data["length"],
                height=room_data.get("height", 2.7),
                room_type=room_data.get("room_type", "living"),
                materials=room_data.get("materials", {})
            )
            
            # Загружаем окна
            for window_data in room_data.get("windows", []):
                room.add_window(
                    width=window_data["width"],
                    height=window_data["height"],
                    position=window_data["position"],
                    name=window_data.get("name", "")
                )
            
            # Загружаем двери
            for door_data in room_data.get("doors", []):
                room.add_door(
                    width=door_data["width"],
                    height=door_data["height"],
                    position=door_data["position"],
                    name=door_data.get("name", "")
                )
            
            apartment.add_room(room)
        
        # Загружаем стены
        for wall_data in data.get("walls", []):
            wall = Wall(
                x1=wall_data["x1"],
                y1=wall_data["y1"],
                x2=wall_data["x2"],
                y2=wall_data["y2"],
                height=wall_data.get("height", 2.7),
                thickness=wall_data.get("thickness", 0.2),
                name=wall_data.get("name", "Стена")
            )
            
            # Загружаем проемы в стенах
            for opening_data in wall_data.get("openings", []):
                opening = Opening(
                    opening_type=OpeningType(opening_data["type"]),
                    width=opening_data["width"],
                    height=opening_data["height"],
                    position=opening_data["position"],
                    name=opening_data.get("name", "")
                )
                wall.add_opening(opening)
            
            apartment.add_wall(wall)
        
        apartment.metadata = data.get("metadata", {})
        
        return apartment

