#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSA-3dsMaxAutomation - Графический интерфейс
GUI для создания планировки квартиры и генерации 3D модели в 3ds Max
"""

# Глобальные переменные проекта
PROJECT_NAME = "FSA-3dsMaxAutomation"
VERSION = "V1.0.0 (2025.10.26)"
DEVELOPER = "@FoksSegr"
FULL_TITLE = f"{PROJECT_NAME} {VERSION} - {DEVELOPER}"

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys

# Добавляем путь к модулям
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from apartment_model import ApartmentModel, Room, OpeningType
from max_script_generator import MaxScriptGenerator


class ApartmentGUI:
    """Графический интерфейс для управления планировкой квартиры"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(FULL_TITLE)
        self.root.minsize(900, 600)
        
        # Открываем окно поверх других на 2 секунды
        self.root.attributes('-topmost', True)
        self.root.after(2000, lambda: self.root.attributes('-topmost', False))
        
        # Модель квартиры
        self.apartment = ApartmentModel()
        
        # Файл проекта
        self.project_file = None
        
        # Для перемещения комнат на плане
        self.dragging_room = None
        self.dragging_room_idx = -1
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.room_canvas_items = {}  # Связь между canvas элементами и комнатами
        self.dragging_tags = None
        self.ghost_room_items = []  # Элементы двойника комнаты при перетаскивании
        self.room_rectangles = {}  # Связь прямоугольников с комнатами
        self.ghost_x = 0  # Текущая позиция двойника
        self.ghost_y = 0
        
        # Автосохранение
        self.auto_save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "autosave")
        os.makedirs(self.auto_save_dir, exist_ok=True)
        self.auto_save_enabled = True
        self.last_auto_save = None
        
        # История для Undo/Redo
        self.undo_stack = []  # Стек для отмены
        self.redo_stack = []  # Стек для возврата
        self.max_undo_steps = 50  # Максимум шагов отмены
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка настроек окна
        self.load_window_settings()
        
        # Привязка событий
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        
        # Привязываем горячие клавиши для Undo/Redo
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-Shift-Z>', lambda e: self.redo())
        
        # Попытка загрузить последнее автосохранение при запуске
        self.load_last_autosave()
        
        # Открываем вкладку просмотра по умолчанию
        self.notebook.select(3)  # Вкладка предпросмотра
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый проект", command=self.new_project)
        file_menu.add_command(label="Открыть проект", command=self.open_project)
        file_menu.add_command(label="Сохранить проект", command=self.save_project)
        file_menu.add_command(label="Сохранить как...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Экспорт
        export_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Экспорт", menu=export_menu)
        export_menu.add_command(label="Генерировать MAXScript", command=self.generate_maxscript)
        export_menu.add_command(label="Сохранить в MAX файл", command=self.export_to_max)
        
        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Отменить (Ctrl+Z)", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Вернуть (Ctrl+Y)", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Очистить историю", command=self.clear_history)
        
        # Меню Автосохранение
        autosave_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Автосохранение", menu=autosave_menu)
        autosave_menu.add_command(label="Включено" if self.auto_save_enabled else "Отключено", 
                                  command=self.toggle_autosave)
        autosave_menu.add_separator()
        autosave_menu.add_command(label="Показать папку автосохранений", command=self.show_autosave_folder)
        autosave_menu.add_command(label="Очистить автосохранения", command=self.clear_autosaves)
        
        # Главный контейнер с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка: Основные настройки
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Основные настройки")
        self.create_settings_tab()
        
        # Вкладка: Комнаты
        self.rooms_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rooms_frame, text="Комнаты")
        self.create_rooms_tab()
        
        # Вкладка: Стены
        self.walls_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.walls_frame, text="Стены")
        self.create_walls_tab()
        
        # Вкладка: Предпросмотр
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="Предпросмотр")
        self.create_preview_tab()
    
    def create_settings_tab(self):
        """Создание вкладки основных настроек"""
        main_frame = ttk.Frame(self.settings_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название проекта
        ttk.Label(main_frame, text="Название проекта:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.project_name_var = tk.StringVar(value="Новая квартира")
        ttk.Entry(main_frame, textvariable=self.project_name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Высота потолка
        ttk.Label(main_frame, text="Высота потолка (м):").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.ceiling_height_var = tk.DoubleVar(value=2.7)
        ttk.Entry(main_frame, textvariable=self.ceiling_height_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Толщина стен по умолчанию
        ttk.Label(main_frame, text="Толщина стен по умолчанию (м):").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.wall_thickness_var = tk.DoubleVar(value=0.2)
        ttk.Entry(main_frame, textvariable=self.wall_thickness_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Информация о квартире
        info_frame = ttk.LabelFrame(main_frame, text="Информация о квартире", padding="15")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20, padx=10)
        
        ttk.Label(info_frame, text="Общая площадь:").grid(row=0, column=0, sticky=tk.W)
        self.total_area_label = ttk.Label(info_frame, text="0.00 кв.м", font=("Arial", 10, "bold"))
        self.total_area_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_frame, text="Количество комнат:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.rooms_count_label = ttk.Label(info_frame, text="0", font=("Arial", 10, "bold"))
        self.rooms_count_label.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_frame, text="Количество стен:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.walls_count_label = ttk.Label(info_frame, text="0", font=("Arial", 10, "bold"))
        self.walls_count_label.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Обновить информацию", command=self.update_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Создать новую квартиру", command=self.new_project).pack(side=tk.LEFT, padx=5)
    
    def create_rooms_tab(self):
        """Создание вкладки управления комнатами"""
        main_frame = ttk.Frame(self.rooms_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Добавить комнату", command=self.add_room_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Редактировать комнату", command=self.edit_room).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить комнату", command=self.delete_room).pack(side=tk.LEFT, padx=5)
        
        # Список комнат
        list_frame = ttk.LabelFrame(main_frame, text="Список комнат")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Таблица комнат
        columns = ('name', 'type', 'width', 'length', 'area')
        self.rooms_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.rooms_tree.heading('name', text='Название')
        self.rooms_tree.heading('type', text='Тип')
        self.rooms_tree.heading('width', text='Ширина (м)')
        self.rooms_tree.heading('length', text='Длина (м)')
        self.rooms_tree.heading('area', text='Площадь (кв.м)')
        
        self.rooms_tree.column('name', width=150)
        self.rooms_tree.column('type', width=100)
        self.rooms_tree.column('width', width=100)
        self.rooms_tree.column('length', width=100)
        self.rooms_tree.column('area', width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscrollcommand=scrollbar.set)
        
        self.rooms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_walls_tab(self):
        """Создание вкладки управления стенами"""
        main_frame = ttk.Frame(self.walls_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Информация
        info_label = ttk.Label(main_frame, text="Стены создаются автоматически для каждой комнаты")
        info_label.pack(pady=20)
        
        # Список стен
        list_frame = ttk.LabelFrame(main_frame, text="Список стен")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.walls_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.walls_listbox.yview)
        self.walls_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.walls_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_preview_tab(self):
        """Создание вкладки предпросмотра"""
        main_frame = ttk.Frame(self.preview_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем PanedWindow для разделения визуального предпросмотра и информации
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - визуальный предпросмотр
        preview_left = ttk.LabelFrame(paned, text="Визуальный предпросмотр планировки")
        
        # Canvas для рисования планировки
        canvas_frame = ttk.Frame(preview_left)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg='white', scrollregion=(0, 0, 1000, 1000))
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.preview_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.preview_canvas.xview)
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        paned.add(preview_left, weight=3)
        
        # Правая панель - информация и кнопки
        preview_right = ttk.Frame(paned)
        
        # Информация о проекте
        info_frame = ttk.LabelFrame(preview_right, text="Информация о проекте")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = tk.Text(info_frame, wrap=tk.WORD, height=15, width=40)
        info_scrollbar = ttk.Scrollbar(info_frame, orient='vertical', command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки экспорта
        export_frame = ttk.LabelFrame(preview_right, text="Экспорт")
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Показать MAXScript", command=self.show_maxscript).pack(pady=3, padx=5, fill=tk.X)
        ttk.Button(export_frame, text="Сохранить MAXScript", command=self.save_maxscript_file).pack(pady=3, padx=5, fill=tk.X)
        ttk.Button(export_frame, text="Генерировать 3D модель", command=self.generate_maxscript).pack(pady=3, padx=5, fill=tk.X)
        
        paned.add(preview_right, weight=1)
    
    def add_room_dialog(self):
        """Диалог добавления новой комнаты"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить комнату")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Словарь для русификации типов комнат
        room_types_ru = {
            "Гостиная": "living",
            "Спальня": "bedroom", 
            "Кухня": "kitchen",
            "Ванная": "bathroom",
            "Коридор": "hallway"
        }
        
        # Поля ввода
        ttk.Label(dialog, text="Название комнаты:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Тип комнаты:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        type_var = tk.StringVar(value="Гостиная")
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=["Гостиная", "Спальня", "Кухня", "Ванная", "Коридор"])
        type_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Ширина (м):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        width_entry = ttk.Entry(dialog, width=30)
        width_entry.insert(0, "3.0")
        width_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Длина (м):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        length_entry = ttk.Entry(dialog, width=30)
        length_entry.insert(0, "4.0")
        length_entry.grid(row=3, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Координата X:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        x_entry = ttk.Entry(dialog, width=30)
        x_entry.insert(0, "0")
        x_entry.grid(row=4, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Координата Y:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=10)
        y_entry = ttk.Entry(dialog, width=30)
        y_entry.insert(0, "0")
        y_entry.grid(row=5, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Толщина стен (м):").grid(row=6, column=0, sticky=tk.W, padx=10, pady=10)
        wall_thickness_entry = ttk.Entry(dialog, width=30)
        wall_thickness_entry.insert(0, str(self.wall_thickness_var.get()))
        wall_thickness_entry.grid(row=6, column=1, padx=10, pady=10)
        
        def add_room():
            try:
                room = Room(
                    name=name_entry.get(),
                    x=float(x_entry.get()),
                    y=float(y_entry.get()),
                    width=float(width_entry.get()),
                    length=float(length_entry.get()),
                    room_type=room_types_ru.get(type_var.get(), "living"),
                    height=self.ceiling_height_var.get(),
                    wall_thickness=float(wall_thickness_entry.get())
                )
                self.apartment.add_room(room)
                self.refresh_rooms_list()
                self.update_info()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
        
        def add_and_save():
            add_room()
            # Автосохранение после добавления комнаты
            self.auto_save()
        
        ttk.Button(dialog, text="Добавить", command=add_and_save).grid(row=6, column=0, columnspan=2, pady=20)
    
    def edit_room(self):
        """Редактирование выбранной комнаты"""
        selection = self.rooms_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите комнату для редактирования")
            return
        
        # Получаем индекс выбранного элемента
        item = self.rooms_tree.item(selection[0])
        name = item['values'][0]
        
        # Находим комнату
        room_to_edit = None
        room_index = -1
        for idx, room in enumerate(self.apartment.rooms):
            if room.name == name:
                room_to_edit = room
                room_index = idx
                break
        
        if not room_to_edit:
            messagebox.showerror("Ошибка", "Комната не найдена")
            return
        
        # Открываем диалог редактирования
        self.edit_room_dialog(room_to_edit, room_index)
    
    def edit_room_dialog(self, room, index):
        """Диалог редактирования комнаты"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать комнату")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Словарь для русификации типов комнат
        room_types_ru = {
            "Гостиная": "living",
            "Спальня": "bedroom", 
            "Кухня": "kitchen",
            "Ванная": "bathroom",
            "Коридор": "hallway"
        }
        room_types_reverse = {v: k for k, v in room_types_ru.items()}
        
        # Поля ввода
        ttk.Label(dialog, text="Название комнаты:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, room.name)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Тип комнаты:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        type_var = tk.StringVar()
        current_type_ru = room_types_reverse.get(room.room_type, "Гостиная")
        type_var.set(current_type_ru)
        type_combo = ttk.Combobox(dialog, textvariable=type_var, values=["Гостиная", "Спальня", "Кухня", "Ванная", "Коридор"])
        type_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Ширина (м):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        width_entry = ttk.Entry(dialog, width=30)
        width_entry.insert(0, str(room.width))
        width_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Длина (м):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        length_entry = ttk.Entry(dialog, width=30)
        length_entry.insert(0, str(room.length))
        length_entry.grid(row=3, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Координата X:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        x_entry = ttk.Entry(dialog, width=30)
        x_entry.insert(0, str(room.x))
        x_entry.grid(row=4, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Координата Y:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=10)
        y_entry = ttk.Entry(dialog, width=30)
        y_entry.insert(0, str(room.y))
        y_entry.grid(row=5, column=1, padx=10, pady=10)
        
        def save_room():
            try:
                # Обновляем комнату
                room.name = name_entry.get()
                room.room_type = room_types_ru.get(type_var.get(), "living")
                room.width = float(width_entry.get())
                room.length = float(length_entry.get())
                room.x = float(x_entry.get())
                room.y = float(y_entry.get())
                
                self.apartment.rooms[index] = room
                
                self.refresh_rooms_list()
                self.update_info()
                # Автосохранение после редактирования
                self.auto_save()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
        
        ttk.Button(dialog, text="Сохранить", command=save_room).grid(row=6, column=0, columnspan=2, pady=20)
    
    def delete_room(self):
        """Удаление выбранной комнаты"""
        selection = self.rooms_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите комнату для удаления")
            return
        
        # Получаем индекс выбранного элемента
        item = self.rooms_tree.item(selection[0])
        name = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить комнату '{name}'?"):
            # Находим и удаляем комнату
            for idx, room in enumerate(self.apartment.rooms):
                if room.name == name:
                    self.apartment.rooms.pop(idx)
                    break
            
            self.refresh_rooms_list()
            self.update_info()
            # Автосохранение после изменения
            self.auto_save()
    
    def refresh_rooms_list(self):
        """Обновление списка комнат"""
        # Очистка списка
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
        
        # Добавление комнат
        for room in self.apartment.rooms:
            area = room.width * room.length
            self.rooms_tree.insert('', 'end', values=(
                room.name,
                room.room_type,
                f"{room.width:.2f}",
                f"{room.length:.2f}",
                f"{area:.2f}"
            ))
    
    def update_info(self):
        """Обновление информации о квартире"""
        self.apartment.name = self.project_name_var.get()
        self.apartment.ceiling_height = self.ceiling_height_var.get()
        
        total_area = self.apartment.get_total_area()
        self.total_area_label.config(text=f"{total_area:.2f} кв.м")
        self.rooms_count_label.config(text=str(self.apartment.get_rooms_count()))
        
        # Обновление списка стен
        walls_count = sum(len([self._generate_walls_for_room(room)]) for room in self.apartment.rooms)
        self.walls_count_label.config(text=str(walls_count))
        
        # Обновление списка комнат
        self.refresh_rooms_list()
        
        # Обновление предпросмотра
        self.update_preview()
    
    def _generate_walls_for_room(self, room: Room):
        """Генерация стен для комнаты (внутренняя утилита)"""
        return 4  # По 4 стены на комнату
    
    def draw_plan_on_canvas(self):
        """Рисование планировки на Canvas"""
        if not hasattr(self, 'preview_canvas'):
            return
        
        # Очистка Canvas
        self.preview_canvas.delete("all")
        self.room_canvas_items = {}
        
        if not self.apartment.rooms:
            # Рисуем надпись что нет комнат
            self.preview_canvas.create_text(500, 500, text="Добавьте комнаты для отображения планировки", 
                                           font=("Arial", 16), fill="gray")
            return
        
        # Сохраняем границы для масштабирования
        self._min_x = min(room.x for room in self.apartment.rooms)
        self._min_y = min(room.y for room in self.apartment.rooms)
        self._max_x = max(room.x + room.length for room in self.apartment.rooms)
        self._max_y = max(room.y + room.width for room in self.apartment.rooms)
        
        # Добавляем отступ
        margin = 50
        width = (self._max_x - self._min_x) * 100 + margin * 2
        height = (self._max_y - self._min_y) * 100 + margin * 2
        
        # Устанавливаем scrollregion
        self.preview_canvas.config(scrollregion=(0, 0, width, height))
        
        # Цвета для разных типов комнат
        room_colors = {
            "living": "#FFD700",      # Золотой для гостиной
            "bedroom": "#87CEEB",      # Голубой для спальни
            "kitchen": "#FF6347",      # Красный для кухни
            "bathroom": "#40E0D0",     # Бирюзовый для ванной
            "hallway": "#D3D3D3"       # Светло-серый для коридора
        }
        
        # Рисуем комнаты
        for idx, room in enumerate(self.apartment.rooms):
            # Координаты для отображения (с учетом отступа)
            x1 = (room.x - self._min_x) * 100 + margin
            y1 = (room.y - self._min_y) * 100 + margin
            x2 = (room.x + room.length - self._min_x) * 100 + margin
            y2 = (room.y + room.width - self._min_y) * 100 + margin
            
            # Толщина стен в пикселях
            wall_px = room.wall_thickness * 100
            
            # Цвет комнаты (внутреннее пространство)
            color = room_colors.get(room.room_type, "#FFFFFF")
            
            # Рисуем стены (4 прямоугольника по периметру)
            wall_color = "#808080"  # Серый цвет для стен
            
            # Нижняя стена
            self.preview_canvas.create_rectangle(
                x1, y1, x2, y1 + wall_px,
                fill=wall_color, outline="black", width=1,
                tags=f"room_{idx}"
            )
            
            # Верхняя стена
            self.preview_canvas.create_rectangle(
                x1, y2 - wall_px, x2, y2,
                fill=wall_color, outline="black", width=1,
                tags=f"room_{idx}"
            )
            
            # Левая стена
            self.preview_canvas.create_rectangle(
                x1, y1, x1 + wall_px, y2,
                fill=wall_color, outline="black", width=1,
                tags=f"room_{idx}"
            )
            
            # Правая стена
            self.preview_canvas.create_rectangle(
                x2 - wall_px, y1, x2, y2,
                fill=wall_color, outline="black", width=1,
                tags=f"room_{idx}"
            )
            
            # Рисуем внутреннее пространство комнаты (без стен)
            inner_x1 = x1 + wall_px
            inner_y1 = y1 + wall_px
            inner_x2 = x2 - wall_px
            inner_y2 = y2 - wall_px
            
            # Определяем ширину контура в зависимости от того, перетаскивается ли эта комната
            outline_width = 3 if (self.dragging_room and self.dragging_room_idx == idx) else 1
            outline_color = "red" if (self.dragging_room and self.dragging_room_idx == idx) else "darkgray"
            
            # Рисуем прямоугольник внутреннего пространства комнаты с тегом для события
            rect_id = self.preview_canvas.create_rectangle(inner_x1, inner_y1, inner_x2, inner_y2, 
                                                fill=color, outline=outline_color, width=outline_width,
                                                tags=f"room_{idx}")
            
            # Связь между элементом Canvas и комнатой
            self.room_canvas_items[f"room_{idx}"] = room
            self.room_rectangles[f"room_{idx}"] = rect_id
            
            # Размеры для подписи
            room_width = room.width
            room_length = room.length
            
            # Подпись комнаты (центр)
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Название комнаты
            self.preview_canvas.create_text(center_x, center_y - 15, 
                                           text=room.name, 
                                           font=("Arial", 12, "bold"), 
                                           fill="black",
                                           tags=f"room_{idx}")
            
            # Размеры
            self.preview_canvas.create_text(center_x, center_y + 10, 
                                           text=f"{room_length:.1f}м × {room_width:.1f}м", 
                                           font=("Arial", 10), 
                                           fill="black",
                                           tags=f"room_{idx}")
            
            # Привязка событий к прямоугольнику
            self.preview_canvas.tag_bind(f"room_{idx}", "<Button-1>", 
                                        lambda e, r=room: self.on_room_press(e, r))
            self.preview_canvas.tag_bind(f"room_{idx}", "<B1-Motion>", self.on_room_drag)
            self.preview_canvas.tag_bind(f"room_{idx}", "<ButtonRelease-1>", self.on_room_release)
        
        # Рисуем оси координат
        self.preview_canvas.create_line(20, margin, 20, height - margin, 
                                        fill="blue", width=2, arrow=tk.LAST)
        self.preview_canvas.create_line(margin, height - 20, width - margin, height - 20, 
                                        fill="blue", width=2, arrow=tk.LAST)
        
        # Подписи осей
        self.preview_canvas.create_text(10, 10, text="Y", font=("Arial", 12, "bold"), fill="blue")
        self.preview_canvas.create_text(width - 30, height - 10, text="X", font=("Arial", 12, "bold"), fill="blue")
        
        # Подсказка о перетаскивании
        self.preview_canvas.create_text(width - 120, 20, text="💡 Зажмите комнату и перетащите мышью | Shift - разрешить пересечение", 
                                       font=("Arial", 9, "italic"), fill="green")
    
    def on_room_press(self, event, room):
        """Обработчик нажатия на комнату"""
        # Находим индекс комнаты
        for idx, r in enumerate(self.apartment.rooms):
            if r == room:
                self.dragging_room_idx = idx
                break
        
        self.dragging_room = room
        # Получаем координаты canvas относительно окна
        canvas_x = self.preview_canvas.canvasx(event.x)
        canvas_y = self.preview_canvas.canvasy(event.y)
        
        # Сохраняем координаты центра комнаты и смещение мыши
        room_center_x = ((room.x - self._min_x) * 100 + 50) + (room.length * 100 / 2)
        room_center_y = ((room.y - self._min_y) * 100 + 50) + (room.width * 100 / 2)
        
        self.drag_offset_x = canvas_x - room_center_x
        self.drag_offset_y = canvas_y - room_center_y
        
        self.drag_start_x = room.x
        self.drag_start_y = room.y
        
        # Сохраняем теги элементов комнаты для перемещения
        self.dragging_tags = [tag for tag in self.room_canvas_items if self.room_canvas_items[tag] == room]
        
        # Изменяем курсор при наведении на комнату
        self.preview_canvas.config(cursor="hand2")
        
        # Выделяем комнату изменением контура
        if f"room_{self.dragging_room_idx}" in self.room_rectangles:
            rect_id = self.room_rectangles[f"room_{self.dragging_room_idx}"]
            self.preview_canvas.itemconfig(rect_id, outline="red", width=4)
    
    def has_intersection(self, room, x, y, exclude_index=-1):
        """Проверка есть ли пересечение комнаты с другими (строгое наложение, не касание)"""
        new_left = x
        new_right = x + room.length
        new_top = y + room.width
        new_bottom = y
        
        for idx, other_room in enumerate(self.apartment.rooms):
            if idx == exclude_index:
                continue
            
            other_left = other_room.x
            other_right = other_room.x + other_room.length
            other_top = other_room.y + other_room.width
            other_bottom = other_room.y
            
            # Проверяем строгое пересечение (наложение, не касание): >
            if (new_right > other_left and new_left < other_right and 
                new_top > other_bottom and new_bottom < other_top):
                return True
        
        return False
    
    def constrain_movement(self, room, new_x, new_y, old_x, old_y, exclude_index=-1, shift_pressed=False):
        """
        Алгоритм скользящей коллизии - ограничиваем движение по осям отдельно
        
        Логика:
        1. Если нет пересечения - разрешаем полное движение
        2. Если есть пересечение - разделяем движение по осям:
           - Сначала пробуем двигаться только по X
           - Потом пробуем двигаться только по Y
           Это позволяет комнате "скользить" вдоль стен
        3. При касании не блокируем (строгое пересечение >)
        """
        if shift_pressed:
            return new_x, new_y
        
        # Если нет пересечения - разрешаем движение
        if not self.has_intersection(room, new_x, new_y, exclude_index):
            return new_x, new_y
        
        # Есть пересечение - разделяем движение по осям
        limited_x = old_x
        limited_y = old_y
        
        # Пробуем двигаться только по X
        if abs(new_x - old_x) > 0.001:  # Есть движение по X
            if not self.has_intersection(room, new_x, old_y, exclude_index):
                limited_x = new_x
        
        # Пробуем двигаться только по Y
        if abs(new_y - old_y) > 0.001:  # Есть движение по Y
            if not self.has_intersection(room, limited_x, new_y, exclude_index):
                limited_y = new_y
        
        return limited_x, limited_y
    
    
    def normalize_coordinates(self):
        """Пересчет координат для устранения отрицательных значений"""
        if not self.apartment.rooms:
            return
        
        # Находим минимальные координаты
        min_x = min(room.x for room in self.apartment.rooms)
        min_y = min(room.y for room in self.apartment.rooms)
        
        # Если есть отрицательные, смещаем все объекты
        if min_x < 0 or min_y < 0:
            offset_x = max(0, -min_x)
            offset_y = max(0, -min_y)
            
            # Смещаем все комнаты
            for room in self.apartment.rooms:
                room.x += offset_x
                room.y += offset_y
    
    def on_room_drag(self, event):
        """Обработчик перетаскивания комнаты"""
        if not self.dragging_room:
            return
        
        # Получаем координаты canvas
        canvas_x = self.preview_canvas.canvasx(event.x)
        canvas_y = self.preview_canvas.canvasy(event.y)
        
        # Вычисляем новое положение центра комнаты
        new_center_x = canvas_x - self.drag_offset_x
        new_center_y = canvas_y - self.drag_offset_y
        
        # Вычисляем новое положение комнаты в метрах (центр - половина размеров)
        margin = 50
        desired_x = self._min_x + (new_center_x - self.dragging_room.length * 100 / 2 - margin) / 100
        desired_y = self._min_y + (new_center_y - self.dragging_room.width * 100 / 2 - margin) / 100
        
        # Проверяем, зажата ли клавиша Shift для свободного перемещения
        shift_pressed = (event.state & 0x1) != 0
        
        # Применяем ограничения скользящей коллизии
        # ВАЖНО: используем текущую позицию двойника, а не начальную!
        current_x = self.ghost_x if hasattr(self, 'ghost_x') and self.ghost_x != 0 else self.dragging_room.x
        current_y = self.ghost_y if hasattr(self, 'ghost_y') and self.ghost_y != 0 else self.dragging_room.y
        
        constrained_x, constrained_y = self.constrain_movement(
            self.dragging_room, desired_x, desired_y, 
            current_x, current_y, 
            self.dragging_room_idx, shift_pressed
        )
        
        # Сохраняем позицию двойника (ограниченную)
        self.ghost_x = constrained_x
        self.ghost_y = constrained_y
        
        # Вычисляем координаты для отображения двойника
        new_x1 = (constrained_x - self._min_x) * 100 + margin
        new_y1 = (constrained_y - self._min_y) * 100 + margin
        new_x2 = new_x1 + (self.dragging_room.length * 100)
        new_y2 = new_y1 + (self.dragging_room.width * 100)
        
        # Удаляем старый двойник
        if self.ghost_room_items:
            for item in self.ghost_room_items:
                self.preview_canvas.delete(item)
            self.ghost_room_items = []
        
        # Рисуем новый двойник комнаты
        room_colors = {
            "living": "#FFD700", "bedroom": "#87CEEB", "kitchen": "#FF6347",
            "bathroom": "#40E0D0", "hallway": "#D3D3D3"
        }
        color = room_colors.get(self.dragging_room.room_type, "#FFFFFF")
        
        # Делаем цвет светлее для эффекта прозрачности (смешиваем с белым)
        def lighten_color(hex_color):
            """Осветляет цвет для эффекта прозрачности"""
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            # Смешиваем с белым (70% белого)
            r = int((r * 0.3 + 255 * 0.7))
            g = int((g * 0.3 + 255 * 0.7))
            b = int((b * 0.3 + 255 * 0.7))
            return f"#{r:02x}{g:02x}{b:02x}"
        
        ghost_color = lighten_color(color)
        
        # Создаем двойник комнаты с полупрозрачным фоном через stipple
        ghost_rect = self.preview_canvas.create_rectangle(
            new_x1, new_y1, new_x2, new_y2, 
            fill=ghost_color, outline="red", width=3, 
            dash=(5, 5), stipple="gray25"
        )
        self.ghost_room_items.append(ghost_rect)
        
        # Создаем двойник текста
        center_x = (new_x1 + new_x2) / 2
        center_y = (new_y1 + new_y2) / 2
        
        ghost_name = self.preview_canvas.create_text(
            center_x, center_y - 15, 
            text=self.dragging_room.name, 
            font=("Arial", 12, "bold"), 
            fill="black"
        )
        self.ghost_room_items.append(ghost_name)
        
        ghost_size = self.preview_canvas.create_text(
            center_x, center_y + 10, 
            text=f"{self.dragging_room.length:.1f}м × {self.dragging_room.width:.1f}м", 
            font=("Arial", 10), 
            fill="black"
        )
        self.ghost_room_items.append(ghost_size)
    
    def on_room_release(self, event):
        """Обработчик отпускания комнаты"""
        if self.dragging_room:
            # Сохраняем состояние для Undo ПЕРЕД изменением
            self.save_state()
            
            # ИСПОЛЬЗУЕМ КООРДИНАТЫ ДВОЙНИКА (не пересчитываем!)
            new_x = self.ghost_x
            new_y = self.ghost_y
            
            # Обновляем координаты комнаты
            self.dragging_room.x = round(new_x, 2)
            self.dragging_room.y = round(new_y, 2)
            
            # Нормализуем координаты (убираем отрицательные)
            self.normalize_coordinates()
            
            # Удаляем двойник
            if self.ghost_room_items:
                for item in self.ghost_room_items:
                    self.preview_canvas.delete(item)
                self.ghost_room_items = []
            
            # Перерисовываем план с новыми координатами
            self.draw_plan_on_canvas()
            
            # Обновляем информацию
            self.refresh_rooms_list()
            self.update_info()
            
            # Автосохранение после перемещения
            self.auto_save()
            
            # Восстанавливаем курсор
            self.preview_canvas.config(cursor="")
            
            # Сбрасываем флаг перетаскивания
            self.dragging_room = None
            self.dragging_room_idx = -1
            self.dragging_tags = None
    
    def update_preview(self):
        """Обновление предпросмотра"""
        self.preview_text.delete(1.0, tk.END)
        
        # Словарь для отображения типов комнат на русском
        room_types_display = {
            "living": "Гостиная",
            "bedroom": "Спальня",
            "kitchen": "Кухня",
            "bathroom": "Ванная",
            "hallway": "Коридор"
        }
        
        info = f"Проект: {self.apartment.name}\n"
        info += f"Высота потолка: {self.apartment.ceiling_height} м\n"
        info += f"Комнат: {self.apartment.get_rooms_count()}\n"
        info += f"Общая площадь: {self.apartment.get_total_area():.2f} кв.м\n\n"
        
        info += "Список комнат:\n"
        for idx, room in enumerate(self.apartment.rooms, 1):
            area = room.width * room.length
            room_type_display = room_types_display.get(room.room_type, room.room_type)
            info += f"{idx}. {room.name} ({room_type_display})\n"
            info += f"   Размеры: {room.width}м x {room.length}м\n"
            info += f"   Площадь: {area:.2f} кв.м\n"
            info += f"   Окон: {len(room.windows)}, Дверей: {len(room.doors)}\n\n"
        
        self.preview_text.insert(1.0, info)
        
        # Обновляем визуальный предпросмотр
        self.draw_plan_on_canvas()
    
    def load_window_settings(self):
        """Загрузка настроек окна"""
        try:
            settings_file = "window_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    geometry = settings.get('geometry', '1200x700')
                    self.root.geometry(geometry)
            else:
                # Если файла нет - используем размеры по умолчанию
                self.root.geometry('1200x700')
        except Exception:
            self.root.geometry('1200x700')
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.save_window_settings()
        self.root.destroy()
    
    def save_window_settings(self):
        """Сохранение настроек окна (размер и положение)"""
        try:
            settings_file = "window_settings.json"
            # Получаем текущую геометрию окна (ширина x высота + X + Y)
            geometry = self.root.geometry()
            settings = {
                'geometry': geometry,
                'last_saved': json.dumps({"timestamp": "now"})
            }
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек окна: {e}")
    
    def new_project(self):
        """Создание нового проекта"""
        if messagebox.askyesno("Новый проект", "Создать новый проект? Все несохраненные изменения будут потеряны."):
            self.apartment = ApartmentModel()
            self.project_file = None
            self.project_name_var.set("Новая квартира")
            self.update_info()
    
    def save_project(self):
        """Сохранение проекта"""
        if self.project_file:
            self.save_to_file(self.project_file)
            messagebox.showinfo("Успех", "Проект сохранен")
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Сохранение проекта как..."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.project_file = filename
            self.save_to_file(filename)
            messagebox.showinfo("Успех", "Проект сохранен")
    
    def open_project(self):
        """Открытие проекта"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.load_from_file(filename)
            messagebox.showinfo("Успех", "Проект загружен")
    
    def save_to_file(self, filename: str):
        """Сохранение в файл"""
        data = self.apartment.to_dict()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filename: str):
        """Загрузка из файла"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.apartment = ApartmentModel.from_dict(data)
        
        self.project_file = filename
        self.project_name_var.set(self.apartment.name)
        self.ceiling_height_var.set(self.apartment.ceiling_height)
        self.update_info()
    
    def show_maxscript(self):
        """Показ MAXScript в окне предпросмотра"""
        generator = MaxScriptGenerator(self.apartment)
        generator.generate_full_apartment()
        script = generator.get_script()
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, script)
        self.notebook.select(3)  # Переключение на вкладку предпросмотра
    
    def generate_maxscript(self):
        """Генерация MAXScript и отображение"""
        if not self.apartment.rooms:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы одну комнату перед генерацией")
            return
        
        self.show_maxscript()
        messagebox.showinfo("Успех", "MAXScript сгенерирован! Проверьте вкладку 'Предпросмотр'")
    
    def save_maxscript_file(self):
        """Сохранение MAXScript в файл"""
        if not self.apartment.rooms:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы одну комнату перед генерацией")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".ms",
            filetypes=[("MAXScript files", "*.ms"), ("All files", "*.*")]
        )
        
        if filename:
            generator = MaxScriptGenerator(self.apartment)
            generator.generate_full_apartment()
            generator.save_to_file(filename)
            messagebox.showinfo("Успех", f"MAXScript сохранен в файл {filename}")
    
    def export_to_max(self):
        """Экспорт в файл .max"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".max",
            filetypes=[("3ds Max files", "*.max"), ("All files", "*.*")]
        )
        
        if filename:
            generator = MaxScriptGenerator(self.apartment)
            generator.generate_full_apartment()
            generator.save_to_max_file(filename)
            messagebox.showinfo("Успех", f"Файл 3ds Max сохранен: {filename}")
    
    def auto_save(self):
        """Автоматическое сохранение проекта"""
        if not self.auto_save_enabled:
            return
        
        try:
            # Создаем имя файла с временной меткой
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.auto_save_dir, f"autosave_{timestamp}.json")
            
            # Сохраняем текущее состояние
            data = self.apartment.to_dict()
            data['metadata']['autosave_time'] = timestamp
            data['metadata']['is_autosave'] = True
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.last_auto_save = filename
            
            # Удаляем старые автосохранения (оставляем последние 10)
            self.cleanup_old_autosaves()
            
        except Exception as e:
            print(f"Ошибка автосохранения: {e}")
    
    def cleanup_old_autosaves(self):
        """Удаление старых автосохранений (оставляем последние 10)"""
        try:
            # Получаем список всех файлов автосохранения
            autosave_files = []
            for filename in os.listdir(self.auto_save_dir):
                if filename.startswith("autosave_") and filename.endswith(".json"):
                    filepath = os.path.join(self.auto_save_dir, filename)
                    autosave_files.append((os.path.getmtime(filepath), filepath))
            
            # Сортируем по времени модификации (последние первыми)
            autosave_files.sort(reverse=True)
            
            # Удаляем все кроме последних 10
            for _, filepath in autosave_files[10:]:
                try:
                    os.remove(filepath)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Ошибка очистки автосохранений: {e}")
    
    def load_last_autosave(self):
        """Загрузка последнего автосохранения"""
        try:
            # Получаем список всех файлов автосохранения
            autosave_files = []
            for filename in os.listdir(self.auto_save_dir):
                if filename.startswith("autosave_") and filename.endswith(".json"):
                    filepath = os.path.join(self.auto_save_dir, filename)
                    autosave_files.append((os.path.getmtime(filepath), filepath))
            
            if not autosave_files:
                return
            
            # Берем последний файл
            autosave_files.sort(reverse=True)
            last_file = autosave_files[0][1]
            
            # Загружаем данные
            with open(last_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Если это автосохранение, загружаем БЕЗ ЗАПРОСА
            if data.get('metadata', {}).get('is_autosave', False):
                # Загружаем данные
                self.apartment = ApartmentModel.from_dict(data)
                self.project_name_var.set(self.apartment.name)
                self.ceiling_height_var.set(self.apartment.ceiling_height)
                self.update_info()
            
        except Exception as e:
            print(f"Ошибка загрузки автосохранения: {e}")
    
    def toggle_autosave(self):
        """Переключение режима автосохранения"""
        self.auto_save_enabled = not self.auto_save_enabled
        status = "включено" if self.auto_save_enabled else "отключено"
        messagebox.showinfo("Автосохранение", f"Автосохранение {status}")
    
    def show_autosave_folder(self):
        """Показать папку автосохранений"""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(self.auto_save_dir)
            elif system == "Darwin":
                subprocess.run(["open", self.auto_save_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.auto_save_dir])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
    
    def clear_autosaves(self):
        """Очистить все автосохранения"""
        if not messagebox.askyesno("Подтверждение", 
                                   "Удалить все автосохранения? Это действие нельзя отменить."):
            return
        
        try:
            # Удаляем все файлы автосохранения
            for filename in os.listdir(self.auto_save_dir):
                if filename.startswith("autosave_") and filename.endswith(".json"):
                    filepath = os.path.join(self.auto_save_dir, filename)
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
            
            messagebox.showinfo("Успех", "Все автосохранения удалены")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить автосохранения: {e}")
    
    def save_state(self):
        """Сохранение текущего состояния для Undo"""
        # Создаём копию состояния квартиры
        state = self.apartment.to_dict()
        self.undo_stack.append(state)
        
        # Очищаем redo стек (после нового действия нельзя вернуть)
        self.redo_stack.clear()
        
        # Ограничиваем размер стека
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
    
    def undo(self):
        """Отмена последнего действия (Ctrl+Z)"""
        if not self.undo_stack:
            messagebox.showinfo("Отмена", "Нет действий для отмены")
            return
        
        # Сохраняем текущее состояние в redo стек
        current_state = self.apartment.to_dict()
        self.redo_stack.append(current_state)
        
        # Восстанавливаем предыдущее состояние
        previous_state = self.undo_stack.pop()
        self.apartment = ApartmentModel.from_dict(previous_state)
        
        # Обновляем интерфейс
        self.project_name_var.set(self.apartment.name)
        self.ceiling_height_var.set(self.apartment.ceiling_height)
        self.refresh_rooms_list()
        self.refresh_walls_list()
        self.update_info()
        self.update_preview()
    
    def redo(self):
        """Возврат отменённого действия (Ctrl+Y)"""
        if not self.redo_stack:
            messagebox.showinfo("Возврат", "Нет действий для возврата")
            return
        
        # Сохраняем текущее состояние в undo стек
        current_state = self.apartment.to_dict()
        self.undo_stack.append(current_state)
        
        # Восстанавливаем следующее состояние
        next_state = self.redo_stack.pop()
        self.apartment = ApartmentModel.from_dict(next_state)
        
        # Обновляем интерфейс
        self.project_name_var.set(self.apartment.name)
        self.ceiling_height_var.set(self.apartment.ceiling_height)
        self.refresh_rooms_list()
        self.refresh_walls_list()
        self.update_info()
        self.update_preview()
    
    def clear_history(self):
        """Очистка истории Undo/Redo"""
        if messagebox.askyesno("Очистка истории", 
                               "Очистить всю историю изменений?\nЭто действие нельзя отменить."):
            self.undo_stack.clear()
            self.redo_stack.clear()
            messagebox.showinfo("Успех", "История изменений очищена")


def main():
    """Главная функция запуска GUI"""
    root = tk.Tk()
    app = ApartmentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

