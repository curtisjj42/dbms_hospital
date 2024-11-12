from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar, Optional, Concatenate, ParamSpec

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session

from databaseui.database.db_types import DBCredentials

P = ParamSpec("P")
R = TypeVar("R")


def with_session(func: Callable[Concatenate[Session, P], R]) -> Callable[P, Optional[R]]:
    """
    Decorator to wrap a function with a session handler.
    Database connections don't generally play well with multithreading, so we utilize SQLAlchemy Sessions.
    This wrapper will get a session, run the wrapped function (while handling errors), and then close the session after.
    :param func: Wrapped function
    :return:
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        # Create a new session
        session = DatabaseManager.new_session()
        result: Optional[R]

        try:
            # Call the original function with the session
            result = func(session, *args, **kwargs)

            # Commit changes to the database (if needed)
            session.commit()

        except Exception as e:
            # Handle exceptions (rollback the transaction, log, etc.)
            result = None
            session.rollback()
            print(f"Error: {e}")
            print(e)

        finally:
            # Remove the session to release resources
            DatabaseManager.remove()

        return result

    return wrapper


class DatabaseManager:
    """
    Singleton Database Manager to be easily accessed by session wrappers
    """
    _instance = None

    _engine: Engine
    _Session: scoped_session[Session]

    def __new__(cls):
        if cls._instance is None:
            print('Creating DatabaseManager Singleton')
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def connect(credentials: DBCredentials):
        self = DatabaseManager()
        self._engine = create_engine((
            'mysql+mysqlconnector://'
            f'{credentials.user}:{credentials.passwd}@{credentials.host}/{credentials.db_name}'
        ))
        self._Session = scoped_session(sessionmaker(bind=self._engine))

    @staticmethod
    def new_session() -> Session:
        return DatabaseManager()._Session()

    @staticmethod
    def remove():
        return DatabaseManager()._Session.remove()

    @staticmethod
    def shutdown():
        DatabaseManager()._engine.dispose()
