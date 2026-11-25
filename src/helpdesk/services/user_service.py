from fastapi import HTTPException, status
from helpdesk.models.user_model import User
from helpdesk.repositories.user_repository import UserRepository
from helpdesk.schemas.user_create import UserCreate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate) -> User:
        hashed_pw = user_data.password
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw,
        )
        return self.repository.create_user(new_user)

    def get_user_by_id(self, user_id: int):
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with {user_id} is not found",
            )
        return user
