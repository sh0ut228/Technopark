#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import Database

def main():
    print("Инициализация базы данных...")
    db = Database()
    links = db.get_all_links()
    print(f"Загружено {len(links)} ссылок:")
    for link in links:
        print(f"  {link['code']} - {link['name']}")
    print("\n✅ База данных готова!")

if __name__ == "__main__":
    main()