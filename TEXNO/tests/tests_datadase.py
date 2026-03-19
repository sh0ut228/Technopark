import pytest
import os
import tempfile
from bot.database import Database

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    db = Database(db_path)
    yield db
    db.get_connection().close()
    os.unlink(db_path)

def test_initial_links_loaded(temp_db):
    links = temp_db.get_all_links()
    assert len(links) == 10

def test_get_link_by_code(temp_db):
    link = temp_db.get_link_by_code('1.1.1')
    assert link is not None
    assert link['name'] == 'Запуск бизнеса'

def test_get_link_by_menu_code(temp_db):
    link = temp_db.get_link_by_menu_code('sub_technopark')
    assert link is not None
    assert link['code'] == '3.1.1'

def test_links_by_category(temp_db):
    finance = temp_db.get_links_by_category('finance')
    assert len(finance) == 3
    
    infrastructure = temp_db.get_links_by_category('infrastructure')
    assert len(infrastructure) == 4

def test_user_management(temp_db):
    user = temp_db.get_or_create_user('12345', 'testuser', 'Test', 'User')
    assert user['user_id'] == '12345'
    assert user['interactions_count'] == 1
    
    user2 = temp_db.get_or_create_user('12345')
    assert user2['interactions_count'] > 1

def test_link_clicks(temp_db):
    temp_db.get_or_create_user('12345')
    temp_db.log_link_click('1.1.1', '12345')
    
    stats = temp_db.get_link_stats()
    startup = next((s for s in stats if s['code'] == '1.1.1'), None)
    assert startup['clicks'] >= 1

def test_settings(temp_db):
    temp_db.set_setting('test_key', 'test_value')
    value = temp_db.get_setting('test_key')
    assert value == 'test_value'