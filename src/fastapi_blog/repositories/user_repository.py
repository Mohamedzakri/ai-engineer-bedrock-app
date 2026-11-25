from sqlalchemy.orm import Session

from fastapi_blog.models.user_model import User
from fastapi_blog.schemas.user_response import UserResponse


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user: User) -> UserResponse | None:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        print(f"Requesting user by the id: {user_id}")
        return self.session.get(User, user_id)
