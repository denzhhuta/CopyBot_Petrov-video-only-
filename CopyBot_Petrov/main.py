import aiogram
import asyncio
from aiogram import types, Bot, Dispatcher, executor, filters
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram_media_group import media_group_handler
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted, MessageToDeleteNotFound, CantRestrictChatOwner)
import contextlib
from contextlib import suppress
from configuration import CONFIGURATION, ERRORS
import time
import schedule
from database import *
from keyboard import main_reply_keyboard, bot_turnoff_keyboard, database_keyboard
import sys
from datetime import datetime
import traceback

async def handle_bot_error(error: Exception):
    # Send a notification or take other actions
    turn_off_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await user_announcement("turn_off", turn_off_time)
    
class CheckSubscriptionUserMiddleware(BaseMiddleware):
    def __init__(self):
         self.prefix = 'key_prefix'
         super(CheckSubscriptionUserMiddleware, self).__init__()
         
    async def on_process_update(self, update: types.Update, data: dict):
        if "message" in update:
            this_user = update.message.from_user
            if update.message.text:
                if "start" in update.message.text:
                    return
    
        elif "callback_query" in update:
            this_user = update.callback_query.from_user
        
        else:
            this_user = None
        
        if this_user is not None:
            get_prefix = self.prefix
                     
            if not this_user.is_bot:                       
                user_id = this_user.id
                if this_user.username != "morkovka2005" and this_user.username != "andrey_prac" and this_user.username != "auditoreold" and this_user.username != "YuliiaBuha":
                    await bot.send_message(user_id, "<b>😔 You are not allowed to use this bot!</b>", parse_mode="HTML") 
                    raise CancelHandler()  
                
                
bot = aiogram.Bot(CONFIGURATION['TOKEN_API'])
storage = MemoryStorage()
dp = aiogram.Dispatcher(bot, storage=storage)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message) -> None:
    last_name = message.from_user.last_name
    
    if last_name is None:
        await bot.send_message(chat_id=message.from_user.id,
                           text=f"<b>Привіт, {message.from_user.first_name}!</b>",
                           parse_mode="HTML",
                           reply_markup = main_reply_keyboard())
    else:
        await bot.send_message(chat_id=message.from_user.id,
                           text=f"<b>Привіт, {message.from_user.first_name} {message.from_user.last_name}!</b>",
                           parse_mode="HTML",
                           reply_markup = main_reply_keyboard())
    

@dp.message_handler(text='Вимкнути бота ❌')
async def shut_down_handler(message: types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text="<b>🤨 Дійсно вимкнути?</b>",
                           reply_markup=bot_turnoff_keyboard(),
                           parse_mode="HTML")

@dp.message_handler(text='Переглянути БД 📄')
async def database_decision_handler(message: types.Message):
    await bot.send_message(chat_id=message.chat.id,
                           text='<b>Меню 📃</b>',
                           reply_markup= database_keyboard(),
                           parse_mode="HTML")

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('database_'))
async def database_final_handler(callback: types.CallbackQuery):
    query_option = callback.data.split('_')[1]
    try:
        posts = await database_check(query_option)
        
        if not posts:
            await bot.send_message(chat_id=callback.message.chat.id,
                                   text="<b>🤨 База даних(список) пуста!</b>",
                                   parse_mode="HTML")
        
        else:
            response = "<b>Всі пости:\nID | ID повідомлення | Дата | Статус</b>\n\n"
            for post in posts:
                response +=f"<b>{post['id']} | {post['message_id']} | {post['approval_date']} | {post['sent_status']}\n</b>"
            
            await bot.send_message(chat_id=callback.message.chat.id,
                                   text=response,
                                   parse_mode="HTML")
    
    except Exception as ex:
         await bot.send_message(chat_id=callback.message.chat.id,
                                text=ERRORS['ERROR_SEND'],
                                parse_mode="HTML")
        
         print("Unknows mistake, probably with Database!")

@dp.message_handler(text='Переглянути БД(fast) 📄')
async def database_check_handler(message: types.Message):
     try:
        posts = await database_check("all")
        
        if not posts:
            await bot.send_message(chat_id=message.chat.id,
                                   text="<b><🤨 База даних пуста!</b>",
                                   parse_mode="HTML")
        
        else:
            response = "<b>Всі пости:\nID | ID повідомлення | Дата | Статус</b>\n\n"
            for post in posts:
                response +=f"<b>{post['id']} | {post['message_id']} | {post['approval_date']} | {post['sent_status']}\n</b>"
            
            await bot.send_message(chat_id=message.chat.id,
                                   text=response,
                                   parse_mode="HTML")
    
     except Exception as ex:
         await bot.send_message(chat_id=message.chat.id,
                                text=ERRORS['ERROR_SEND'],
                                parse_mode="HTML")
        
         print("Unknows mistake, probably with Database!")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('turnoff_'))
async def shut_down_proof(callback: types.CallbackQuery):
    details = callback.data.split('_')[1]
    
    if details == "accept":
        turn_off_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await bot.send_message(chat_id=callback.message.chat.id,
                               text='<b>👋 Бота вимкнено!</b>',
                               parse_mode="HTML")
        
        announcement_type = 'turn_off'
        await user_announcement(announcement_type, turn_off_time, None)
        sys.exit()
    
    if details == "cancel":
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    message_id=callback.message.message_id,
                                    text='<b>❌ Відміна</b>',
                                    parse_mode="HTML")
        
@dp.message_handler(filters.MediaGroupFilter(is_media_group=False), content_types=types.ContentTypes.VIDEO)
async def process_forwarded_message(message: types.Message, state: FSMContext):
    
    buttons_row1 = [
        aiogram.types.InlineKeyboardButton("🗑 Видалити", callback_data=f"delete:{message.message_id}"),
        aiogram.types.InlineKeyboardButton("📩 Переслати", callback_data=f"forward:{message.message_id}"),
        aiogram.types.InlineKeyboardButton("📩 ID", callback_data=f"id:{message.message_id+1}")

    ]

    keyboard = aiogram.types.InlineKeyboardMarkup().row(*buttons_row1)

    if message.video and message.caption:
        await bot.send_video(chat_id=message.chat.id,
                             video=message.video.file_id,
                             caption='<a href="https://www.apple.com/de/iphone-14/">Petrov</a>',
                             reply_markup=keyboard,
                             parse_mode="HTML")

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('id:'))
async def id_check(callback: types.CallbackQuery):
    message_id = callback.data.split(':')[1]
    await bot.send_message(chat_id=callback.message.chat.id,
                           text=message_id)
    
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('forward:'))
async def forward_callback_handler(callback: types.CallbackQuery):
    try:
        message_id = int(callback.data.split(':')[1])
        
        # await bot.copy_message(chat_id=CONFIGURATION['CHANNEL_ID'], 
        #                         from_chat_id=callback.message.chat.id, 
        #                         message_id=callback.message.message_id)
        
        result = await add_post_to_database(int(message_id) + 1)
        
        if result:
            await bot.send_message(chat_id=callback.message.chat.id,
                                   text=result,
                                   parse_mode="HTML")
            
    except Exception as ex:
        await bot.send_message(chat_id=callback.message.chat.id, 
                               text=f"{ERRORS['ERROR_FORWARD']}\n{ex}",
                               parse_mode="HTML")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('delete:'))
async def delete_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        message_id = int(callback.data.split(':')[1])

        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        
        # Delete the user's message if it exists
        with contextlib.suppress(
            aiogram.utils.exceptions.MessageCantBeDeleted,
            aiogram.utils.exceptions.MessageToDeleteNotFound
        ):
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=message_id)
        
    except Exception as ex:
        await bot.send_message(chat_id=callback.message.chat.id, text=ERRORS['ERROR_DELETE'], parse_mode="HTML")
        
async def send_at_specific_time():
    consecutive_error_count = 0
    
    while True:
        print("send_at_specific_time is running")
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        
        #ТУТ ВИСТАВЛЯТИ ГОДИНИ
        specific_time = [(1,26), (1,27), (1,28), (1,29)]
        if (current_hour, current_minute) in specific_time:
            try:
                print("Matching specific time, executing action")
                row_information = await post_sender()
                if row_information:
                    print(row_information)
                    await bot.copy_message(chat_id=1013673667,
                                           from_chat_id=1013673667,
                                           message_id=int(row_information),
                                           parse_mode="HTML")
                    print(f"Успішно надіслано повідомлення {int(row_information)}")
                    consecutive_error_count = 0
                    #6064195503
                    #1013673667
                    #-1001900232820
                else:
                    print("No message to resend")
                    consecutive_error_count += 1
                    if consecutive_error_count >=2:
                        await bot.send_message(chat_id=1013673667,
                                               text="<b>😔 Список постів пустий!</b>",
                                               parse_mode="HTML")

                        if consecutive_error_count % 5 == 0:
                            no_posts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            await user_announcement("error", no_posts, "😔 Пости відсутні уже тривалий час!")
                        
            except aiogram.utils.exceptions.BadRequest as e:
                print("Error copying message:", e)
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await user_announcement("error", error_time, f"{e} ID: {row_information}")

                                
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(send_at_specific_time())
    
       
if __name__ == "__main__":
    dp.middleware.setup(CheckSubscriptionUserMiddleware())
    asyncio.get_event_loop().create_task(main())
    executor.start_polling(dp, skip_updates=True)