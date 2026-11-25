from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from helpdesk.db.database import get_db
from helpdesk.repositories.user_repository import UserRepository
from helpdesk.services.user_service import UserService


def get_user_repository(
    session: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repo)
