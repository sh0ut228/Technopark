import sqlite3
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str = "bot_database.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация таблиц и загрузка ссылок"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица для ссылок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    menu_code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    category TEXT,
                    parent_category TEXT,
                    full_path TEXT,
                    order_num INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица для пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interactions_count INTEGER DEFAULT 0,
                    current_menu TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Таблица для действий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action_type TEXT,
                    menu_path TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица для кликов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS link_clicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_code TEXT,
                    user_id TEXT,
                    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (link_code) REFERENCES links(code),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица для настроек
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self.load_initial_links()
    
    def load_initial_links(self):
        """Загрузка начальных ссылок"""
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT COUNT(*) as count FROM links')
        if cursor.fetchone()['count'] > 0:
            return
        
        initial_links = [
            # Финансовые услуги
            ('1.1.1', 'sub_startup', 'Запуск бизнеса', 
             'https://spbtech.ru/mery-podderzhki/zapusk-biznesa',
             'finance', '1', '1 > 1.1 > 1.1.1', 1),
            
            ('1.2.1', 'sub_funding', 'Программы финансирования',
             'https://spbtech.ru/mery-podderzhki',
             'finance', '1', '1 > 1.2 > 1.2.1', 2),
            
            ('1.3.1', 'sub_investments', 'Частные инвестиции',
             'https://spbtech.ru/ekosistema/navigator-po-investiciyam?tfc_page%5B1121505371%5D=2&tfc_div=:::',
             'finance', '1', '1 > 1.3 > 1.3.1', 3),
            
            # Программы развития
            ('2.1.1', 'sub_residence', 'Резидентура в технопарк СПб',
             'https://spbtech.ru/tekhnopark-sankt-peterburga/biznes-inkubator/rezidentura',
             'development', '2', '2 > 2.1 > 2.1.1', 1),
            
            ('2.2.1', 'sub_gov', 'Гос программы',
             'https://spbtech.ru/mery-podderzhki/gos-programmy',
             'development', '2', '2 > 2.2 > 2.2.1', 2),
            
            ('2.3.1', 'sub_market', 'Протестировать программы и выйти на рынок',
             'https://spbtech.ru/mery-podderzhki/vyhod-na-rynok',
             'development', '2', '2 > 2.3 > 2.3.1', 3),
            
            # Доступ к инфраструктуре
            ('3.1.1', 'sub_technopark', 'Технопарк СПб',
             'https://spbtech.ru/tekhnopark-sankt-peterburga',
             'infrastructure', '3', '3 > 3.1 > 3.1.1', 1),
            
            ('3.2.1', 'sub_innovation', 'Объекты инновационно технологической инфраструктуры',
             'https://spbtech.ru/ekosistema/innovacionno-tekhnologicheskaya-infrastruktura',
             'infrastructure', '3', '3 > 3.2 > 3.2.1', 2),
            
            ('3.3.1', 'sub_tech_companies', 'Технологические компании',
             'https://spbtech.ru/ekosistema/tekhnologicheskie-kompanii',
             'infrastructure', '3', '3 > 3.3 > 3.3.1', 3),
            
            ('3.4.1', 'sub_tech_services', 'Технологические услуги',
             'https://spbtech.ru/ekosistema/infrastruktura-i-tekhnologicheskie-uslugi',
             'infrastructure', '3', '3 > 3.4 > 3.4.1', 4),
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for link in initial_links:
                cursor.execute('''
                    INSERT INTO links 
                    (code, menu_code, name, url, category, parent_category, full_path, order_num)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', link)
            
            # Настройки по умолчанию
            default_settings = [
                ('welcome_message', 'Добро пожаловать! Выберите раздел:', 'Приветствие'),
                ('bot_name', 'Бизнес поддержка', 'Имя бота'),
                ('admin_ids', json.dumps([]), 'Администраторы'),
            ]
            cursor.executemany('INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)', 
                             default_settings)
            
            conn.commit()
            logger.info(f"Загружено {len(initial_links)} ссылок")
    
    # Методы для ссылок
    def get_link_by_menu_code(self, menu_code: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM links WHERE menu_code = ? AND is_active = 1', (menu_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_link_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM links WHERE code = ? AND is_active = 1', (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_links(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM links WHERE is_active = 1 ORDER BY code')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_links_by_category(self, category: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM links 
                WHERE category = ? AND is_active = 1 
                ORDER BY order_num
            ''', (category,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_link(self, code: str, menu_code: str, name: str, url: str, 
                 category: str = None, parent_category: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO links (code, menu_code, name, url, category, parent_category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(code) DO UPDATE SET
                    name = excluded.name,
                    url = excluded.url,
                    menu_code = excluded.menu_code,
                    category = excluded.category,
                    parent_category = excluded.parent_category,
                    updated_at = CURRENT_TIMESTAMP,
                    is_active = 1
            ''', (code, menu_code, name, url, category, parent_category))
            conn.commit()
            return cursor.lastrowid
    
    def update_link(self, code: str, **kwargs) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            
            for key, value in kwargs.items():
                if value is not None and key in ['name', 'url', 'category', 'menu_code', 'is_active']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if fields:
                values.append(code)
                query = f"UPDATE links SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE code = ?"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        return False
    
    def delete_link(self, code: str, soft_delete: bool = True) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if soft_delete:
                cursor.execute('UPDATE links SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?', (code,))
            else:
                cursor.execute('DELETE FROM links WHERE code = ?', (code,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Методы для пользователей
    def get_or_create_user(self, user_id: str, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                cursor.execute('''
                    UPDATE users 
                    SET last_seen = CURRENT_TIMESTAMP, 
                        interactions_count = interactions_count + 1,
                        username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name)
                    WHERE user_id = ?
                ''', (username, first_name, last_name, user_id))
                return dict(user)
            else:
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, interactions_count)
                    VALUES (?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return {
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'interactions_count': 1
                }
    
    def update_user_menu(self, user_id: str, menu_path: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET current_menu = ? WHERE user_id = ?', (menu_path, user_id))
            conn.commit()
    
    # Методы для логирования
    def log_action(self, user_id: str, action_type: str, menu_path: str = None, details: dict = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_actions (user_id, action_type, menu_path, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action_type, menu_path, json.dumps(details, ensure_ascii=False) if details else None))
            conn.commit()
    
    def log_link_click(self, link_code: str, user_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO link_clicks (link_code, user_id)
                VALUES (?, ?)
            ''', (link_code, user_id))
            conn.commit()
    
    # Методы для статистики
    def get_link_stats(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.code, l.name, l.category, COUNT(lc.id) as clicks
                FROM links l
                LEFT JOIN link_clicks lc ON l.code = lc.link_code
                WHERE l.is_active = 1
                GROUP BY l.code
                ORDER BY clicks DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT COUNT(*) as active_today 
                FROM users 
                WHERE date(last_seen) = date('now')
            ''')
            active_today = cursor.fetchone()['active_today']
            
            cursor.execute('SELECT COUNT(*) as total_actions FROM user_actions')
            total_actions = cursor.fetchone()['total_actions']
            
            return {
                'total_users': total,
                'active_today': active_today,
                'total_actions': total_actions
            }
    
    # Методы для настроек
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default
    
    def set_setting(self, key: str, value: Any, description: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            json_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            cursor.execute('''
                INSERT INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    description = COALESCE(excluded.description, description),
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, json_value, description))
            conn.commit()