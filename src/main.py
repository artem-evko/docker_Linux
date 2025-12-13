import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src import models, schemas
from src.database import init_db, get_db

app = FastAPI()

PREFIX = os.getenv("ROOT_PATH", "").rstrip("/")
# если ROOT_PATH пустой -> PREFIX = ""
# если ROOT_PATH="/banzai" -> PREFIX="/banzai"


@app.on_event("startup")
async def startup():
    await init_db()


@app.post(f"{PREFIX}/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    user = models.User(name=user.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.get(f"{PREFIX}/users/", response_model=list[schemas.User])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    return result.scalars().all()


@app.get(f"{PREFIX}/users/{{user_id}}", response_model=schemas.User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch(f"{PREFIX}/users/{{user_id}}", response_model=schemas.User)
async def update_user(user_id: int, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.name = user.name
    await db.commit()
    return db_user


@app.delete(f"{PREFIX}/users/{{user_id}}", response_model=dict)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(db_user)
    await db.commit()
    return {"detail": "User deleted"}
