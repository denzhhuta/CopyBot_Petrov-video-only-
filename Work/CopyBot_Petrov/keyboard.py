from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    b1 = KeyboardButton(text="Вимкнути бота ❌")
    kb.add(b1)
    return kb

def bot_turnoff_keyboard() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Так ✅', callback_data=f'turnoff_accept')],
        [InlineKeyboardButton('Ні ❌', callback_data=f'turnoff_cancel')]
    ])
    return ikb