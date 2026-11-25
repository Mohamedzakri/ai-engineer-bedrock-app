from typing import Annotated

from fastapi import APIRouter, Depends, status

from helpdesk.api.dependencies import get_user_service
from helpdesk.schemas.user_create import UserCreate
from helpdesk.schemas.user_response import UserResponse
from helpdesk.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
):
    return service.create_user(user)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: int, service: Annotated[UserService, Depends(get_user_service)]
):
    print(f"Requesting user by the id: {user_id}")
    return service.get_user_by_id(user_id)
