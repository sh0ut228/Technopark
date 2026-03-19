import pytest
from unittest.mock import Mock, AsyncMock
from bot.max_bot import make_keyboard

@pytest.mark.asyncio
async def test_make_keyboard():
    buttons = [
        [("Тест 1", "data1")],
        [("Тест 2", "data2")]
    ]
    
    keyboard = make_keyboard(buttons)
    assert len(keyboard.inline_keyboard) == 2
    assert keyboard.inline_keyboard[0][0].text == "Тест 1"
    assert keyboard.inline_keyboard[0][0].callback_data == "data1"