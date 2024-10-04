import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=f'{os.getenv("TODO_TG_BOT_TOKEN")}')

dp = Dispatcher()


@dp.message(Command('start'))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Create ToDo", callback_data="create_todo")
    )
    builder.add(types.InlineKeyboardButton(
        text="ToDo list", callback_data="todo_list")
    )
    builder.row(types.InlineKeyboardButton(
        text="My GitHub", url="https://github.com/saneksking")
    )
    await message.answer("Hello! I'm a ToDo Telegram bot. My tasks is saving your ToDos!\n"
                         "--------------------\n"
                         "I can:\n"
                         "1. Create ToDos\n"
                         "2. Show ToDos\n"
                         "3. Manage ToDos\n"
                         "--------------------\n"
                         "Choose what you want to do! :)",
                         reply_markup=builder.as_markup())


@dp.callback_query(F.data == "create_todo")
async def create_todo(callback: types.CallbackQuery):
    await callback.message.answer('Creating todo...')


@dp.callback_query(F.data == "todo_list")
async def send_random_value(callback: types.CallbackQuery):
    await callback.message.answer('Showing todo list...')


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
