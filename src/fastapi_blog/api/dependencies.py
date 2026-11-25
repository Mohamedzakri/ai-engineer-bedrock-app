from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from fastapi_blog.db.database import get_db
from fastapi_blog.repositories.user_repository import UserRepository
from fastapi_blog.services.user_service import UserService


def get_user_repository(
    session: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repo)
