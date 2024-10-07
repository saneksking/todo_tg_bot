# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2024, A.A. Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/saneksking/
# --------------------------------------------------------
import os
import logging
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from utils.config import AppConfig
from utils.database import AppManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class TaskStates(StatesGroup):
    title = State()
    description = State()


class TaskEditStates(StatesGroup):
    title = State()
    description = State()


class TelegramBot:
    config = AppConfig()

    def __init__(self, token):
        self.app_manager = AppManager()
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        self.dp = Dispatcher()
        self.dp.message(Command("start"))(self.cmd_start)
        self.dp.callback_query()(self.callback_handler)
        self.dp.message(TaskStates.title)(self.process_task_title)
        self.dp.message(TaskStates.description)(
            self.process_task_description)
        self.dp.message(TaskEditStates.title)(self.process_edit_task_title)
        self.dp.message(TaskEditStates.description)(self.process_edit_task_description)

    async def callback_handler(self, callback_query: types.CallbackQuery, state: FSMContext) -> None:
        if callback_query.data.startswith("task_"):
            task_index = int(callback_query.data.split("_")[1]) - 1
            tasks = self.app_manager.get_tasks(callback_query.from_user.id)
            if 0 <= task_index < len(tasks):
                task = tasks[task_index]
                await self.show_task_details(callback_query.message, task, callback_query.from_user)
        elif callback_query.data.startswith("edit_task_"):
            task_id = int(callback_query.data.split("_")[2])
            await self.edit_task(callback_query.message, task_id, state)
        elif callback_query.data.startswith("complete_task_"):
            task_id = int(callback_query.data.split("_")[2])
            await self.complete_task(callback_query.message, task_id, callback_query.from_user)
        elif callback_query.data.startswith("delete_task_"):
            task_id = int(callback_query.data.split("_")[2])
            await self.delete_task(callback_query.message, task_id, callback_query.from_user)
        elif callback_query.data == "show_tasks":
            await self.show_tasks(callback_query.message, user=callback_query.from_user)
        elif callback_query.data == "back_to_start":
            await self.cmd_start(callback_query.message, user=callback_query.from_user)
        elif callback_query.data == "add_task":
            await self.add_task(callback_query.message, user=callback_query.from_user, state=state)
        elif callback_query.data.startswith("toggle_task_"):
            task_id = int(callback_query.data.split("_")[2])
            await self.toggle_task(callback_query.message, task_id, callback_query.from_user)

    async def cmd_start(self, message: types.Message, user: types.User = None) -> None:
        if user is None:
            user = message.from_user

        self.app_manager.add_user(
            user_id=user.id,
            first_name=user.first_name or 'Anonim',
            last_name=user.last_name or 'Anonim',
            full_name=user.full_name or 'Anonim',
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text="✚ Add task",
                callback_data="add_task"
            )
        )
        builder.row(types.InlineKeyboardButton(
            text=f"📝 My tasks [{self.app_manager.get_completed_task_count(user.id)}"
                 f"/{self.app_manager.get_task_count(user.id)}]",
            callback_data="show_tasks")
        )
        builder.row(types.InlineKeyboardButton(
            text="🐱 GitHub", url=self.config.github_url)
        )

        msg = (f"<b>{user.full_name}</b>! Welcome to <b>{self.config.app_name}</b>.\n\n"
               f"<b>Tasks completed ✅/📝: </b>{self.app_manager.get_completed_task_count(user.id)}/"
               f"{self.app_manager.get_task_count(user.id)}\n\n"
               f'To view your tasks, click "My tasks"')

        await message.answer(msg, reply_markup=builder.as_markup())

    async def show_task_details(self, message: types.Message, task, user: types.User) -> None:
        button_text = "❌ Mark as not completed" if task.completed else "✅ Mark as done"
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            types.InlineKeyboardButton(
                text="✏️ Change",
                callback_data=f"edit_task_{task.id}"
            )
        )
        keyboard.row(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"toggle_task_{task.id}"
            )
        )
        keyboard.row(
            types.InlineKeyboardButton(
                text="🔥 Delete",
                callback_data=f"delete_task_{task.id}"
            )
        )
        keyboard.row(
            types.InlineKeyboardButton(
                text="◀️ To the tasks",
                callback_data="show_tasks"
            )
        )
        text = (f"📝 Task:\n\n{task.title}\n\n"
                f"✍️ Description:\n\n{task.description}\n\n"
                f"⏳ Status: {self.app_manager.get_task_emoji(task.completed)}\n")
        await message.answer(
            text,
            reply_markup=keyboard.as_markup()
        )

    async def add_task(self, message: types.Message, user: types.User = None, state: FSMContext = None) -> None:
        if user is None:
            user = message.from_user

        await state.set_state(TaskStates.title)
        await message.answer(f"{user.full_name} enter the name of your task: ")

    async def process_task_title(self, message: types.Message, state: FSMContext) -> None:
        task_title = message.text
        if len(task_title) > 50:
            await message.answer("⚠️ The name is too long. Please enter a name no longer than 50 characters:")
            return
        await state.update_data(task_title=task_title)
        await state.set_state(TaskStates.description)
        await message.answer("Now enter a description of your task: ")

    async def process_task_description(self, message: types.Message, state: FSMContext) -> None:
        task_description = message.text
        data = await state.get_data()
        task_title = data.get("task_title")
        self.app_manager.add_task(message.from_user.id, task_title, task_description)
        await message.answer(f"Task '{task_title}' with description '{task_description}' added!")
        await state.clear()
        await self.cmd_start(message)

    async def show_tasks(self, message: Message, user: types.User = None) -> None:
        builder = InlineKeyboardBuilder()
        tasks = self.app_manager.get_tasks(user.id)

        if user is None:
            user = message.from_user

        if not tasks:
            builder.row(types.InlineKeyboardButton(
                text="◀️ To the main page",
                callback_data="back_to_start")
            )
            await message.answer("You have no tasks.", reply_markup=builder.as_markup())
            return

        msg = f'<b>{user.full_name}</b> here are your tasks, choose the right one: '
        for n, task in enumerate(tasks, 1):
            builder.row(types.InlineKeyboardButton(
                text=f"{self.app_manager.get_task_emoji(task.completed)} {n}: {task.title}",
                callback_data=f"task_{n}")
            )
        builder.row(types.InlineKeyboardButton(
            text="◀️ Back",
            callback_data="back_to_start")
        )

        await message.answer(msg, reply_markup=builder.as_markup())

    async def toggle_task(self, message: types.Message, task_id: int, user: types.User) -> None:
        task = self.app_manager.get_task_by_id(task_id)
        if task.completed:
            self.app_manager.mark_task_as_not_completed(task_id)
            await message.answer("The task is marked as not completed!")
        else:
            self.app_manager.mark_task_as_completed(task_id)
            await message.answer("The task is marked as completed!")
        await self.show_tasks(message, user=user)

    async def edit_task(self, message: types.Message, task_id: int, state: FSMContext) -> None:
        task = self.app_manager.get_task_by_id(task_id)
        await state.update_data(task_id=task_id)
        await state.set_state(
            TaskEditStates.title)
        await message.answer(f"Old name:\n{task.title}\nEnter a new task name:")

    async def complete_task(self, message: types.Message, task_id: int, user: types.User) -> None:
        self.app_manager.mark_task_as_completed(task_id)
        await message.answer("The task is marked as completed!")
        await self.show_tasks(message, user=user)

    async def delete_task(self, message: types.Message, task_id: int, user: types.User) -> None:
        self.app_manager.delete_task(task_id)
        await message.answer("🔥 Task deleted!")
        await self.show_tasks(message, user=user)

    async def process_edit_task_title(self, message: types.Message, state: FSMContext) -> None:
        data = await state.get_data()
        task_id = data.get("task_id")
        task_title = message.text
        if len(task_title) > 50:
            await message.answer("⚠️ The title is too long. Please., "
                                 "enter a name no longer than 50 characters:")
            return
        await state.update_data(task_title=task_title)
        await state.set_state(
            TaskEditStates.description)
        await message.answer(
            f"Old description: {self.app_manager.get_task_by_id(task_id).description}\nEnter a new task description:")

    async def process_edit_task_description(self, message: types.Message, state: FSMContext) -> None:
        data = await state.get_data()
        task_id = data.get("task_id")
        task_description = message.text
        task_title = data.get("task_title")
        self.app_manager.update_task(task_id, task_title, task_description)
        await message.answer(
            f"Task updated: '{task_title}' with description '{task_description}'!")
        await state.clear()
        await self.show_tasks(message, user=message.from_user)

    async def run(self):
        await self.dp.start_polling(self.bot)


def main():
    api_token = os.getenv("API_TOKEN")
    bot = TelegramBot(api_token)
    asyncio.run(bot.run())


if __name__ == '__main__':
    main()