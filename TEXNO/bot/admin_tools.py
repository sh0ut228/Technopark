#!/usr/bin/env python
"""
Инструменты для управления ботом через консоль
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import Database

db = Database()

def print_menu():
    print("\n" + "="*50)
    print("УПРАВЛЕНИЕ БОТОМ MAX")
    print("="*50)
    print("1. Показать все ссылки")
    print("2. Добавить ссылку")
    print("3. Статистика переходов")
    print("4. Статистика пользователей")
    print("5. Просмотр логов")
    print("0. Выход")
    return input("\nВыберите действие: ")

def show_links():
    links = db.get_all_links()
    print("\n=== ССЫЛКИ ===")
    for link in links:
        clicks = db.get_link_stats()
        click_count = next((c['clicks'] for c in clicks if c['code'] == link['code']), 0)
        print(f"{link['code']} | {link['name']}")
        print(f"   URL: {link['url']}")
        print(f"   Категория: {link['category']}")
        print(f"   Переходов: {click_count}")
        print("-" * 40)

def add_link():
    print("\n=== ДОБАВЛЕНИЕ ССЫЛКИ ===")
    code = input("Код (например 1.1.1): ")
    menu_code = input("Menu code (например sub_startup): ")
    name = input("Название: ")
    url = input("URL: ")
    category = input("Категория (finance/development/infrastructure): ")
    parent = input("Родительская категория (1/2/3): ")
    
    db.add_link(code, menu_code, name, url, category, parent)
    print("✅ Ссылка добавлена!")

def show_stats():
    print("\n=== СТАТИСТИКА ПЕРЕХОДОВ ===")
    stats = db.get_link_stats()
    for stat in stats:
        print(f"{stat['code']} - {stat['name']}: {stat['clicks']} переходов")

def show_user_stats():
    stats = db.get_user_stats()
    print("\n=== СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ ===")
    print(f"Всего пользователей: {stats['total_users']}")
    print(f"Активных сегодня: {stats['active_today']}")
    print(f"Всего действий: {stats['total_actions']}")

def show_logs():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM user_actions 
        ORDER BY timestamp DESC 
        LIMIT 20
    ''')
    logs = cursor.fetchall()
    conn.close()
    
    print("\n=== ПОСЛЕДНИЕ ДЕЙСТВИЯ ===")
    for log in logs:
        print(f"[{log['timestamp']}] {log['user_id']}: {log['action_type']} - {log['menu_path']}")

if __name__ == "__main__":
    while True:
        choice = print_menu()
        
        if choice == "1":
            show_links()
        elif choice == "2":
            add_link()
        elif choice == "3":
            show_stats()
        elif choice == "4":
            show_user_stats()
        elif choice == "5":
            show_logs()
        elif choice == "0":
            break
        else:
            print("Неверный выбор")
        
        input("\nНажмите Enter для продолжения...")