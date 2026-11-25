from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_blog.api.user_controller import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(user_router)
