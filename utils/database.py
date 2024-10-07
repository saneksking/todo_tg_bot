# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2024, A.A. Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/saneksking/
# --------------------------------------------------------
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    completed = Column(Boolean, default=False)


class AppManager:
    def __init__(self):
        self.engine = self.create_connection()
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    @classmethod
    def create_connection(cls):
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        host = os.getenv('DB_HOST', 'localhost')
        database = os.getenv('DB_NAME', 'tasks')
        return create_engine(f'mysql+pymysql://{user}:{password}@{host}/{database}')

    def get_session(self):
        return self.Session()

    def add_user(self, user_id, first_name, last_name, full_name):
        with self.get_session() as session:
            if not session.query(User).filter(User.id == user_id).first():
                user = User(id=user_id, first_name=first_name, last_name=last_name, full_name=full_name)
                session.add(user)
                session.commit()

    def get_user(self, user_id):
        with self.get_session() as session:
            return session.query(User).filter(User.id == user_id).first()

    def update_user(self, user_id, first_name, last_name, full_name):
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.first_name = first_name
                user.last_name = last_name
                user.full_name = full_name
                session.commit()

    def delete_user(self, user_id):
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()

    def add_task(self, user_id, title, description):
        with self.get_session() as session:
            task = Task(user_id=user_id, title=title, description=description)
            session.add(task)
            session.commit()

    def get_tasks(self, user_id):
        with self.get_session() as session:
            return session.query(Task).filter(Task.user_id == user_id).all()

    def update_task(self, task_id, title, description, completed=None):
        with self.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                if title is not None:
                    task.title = title
                if description is not None:
                    task.description = description
                if completed is not None:
                    task.completed = completed
                session.commit()

    def delete_task(self, task_id):
        with self.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                session.delete(task)
                session.commit()

    def mark_task_as_completed(self, task_id):
        self.update_task(task_id, None, None, True)

    def mark_task_as_not_completed(self, task_id):
        self.update_task(task_id, None, None, False)

    def get_task_count(self, user_id):
        with self.get_session() as session:
            return session.query(Task).filter(Task.user_id == user_id).count()

    def get_completed_task_count(self, user_id):
        with self.get_session() as session:
            return session.query(Task).filter(Task.user_id == user_id, Task.completed).count()

    def get_task_by_id(self, task_id):
        with self.get_session() as session:
            return session.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_task_emoji(status):
        return '✅' if status else '❌'