import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user
from src.auth.models import workplace, user, user_workplace, WorkerSchema, worker
from src.database import get_async_session
from src.ml.schemas import WorkPlaceCreate
from fastapi.staticfiles import StaticFiles
router = APIRouter(
    prefix="/work",
    tags=["Operation"]
)


@router.post("/worker")
async def create_new_worker(new_worker: WorkerSchema,
                            current : user =Depends(current_user),
                            db: AsyncSession = Depends(get_async_session)):
    print(new_worker)
    stmt = insert(worker).values(**new_worker.dict())
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}


@router.post("/worker/image")
async def upload_image_worker(id: int, image: UploadFile = File(...),current : user =Depends(current_user), db: AsyncSession = Depends(get_async_session)):
    # Читаем данные изображения
    image_data = await image.read()

    query = select(worker).where(worker.c.id == id)
    result = await db.execute(query)
    worker_take = result.all()
    print(worker_take)
    name = ""
    if worker_take is not None:
        print(result)
        name = worker_take[0]["name"]

    filename = f"{name}{id}.jpg"  # Например, можно использовать формат worker_1_image.jpg
    with open(os.path.join("static-worker", filename), "wb") as f:
        f.write(image_data)

        # Формируем URL изображения
    image_url = f"/static-worker/{filename}"  # URL будет вида /static/worker_1_image.jpg

    # Обновляем запись в базе данных с URL изображения
    stmt = update(worker).where(worker.c.id == id).values(image_url=image_url)
    await db.execute(stmt)
    await db.commit()

    return {"status": "success", "image_url": image_url}


@router.post("/workplaces")
async def create_new_workplac(new_workplace: WorkPlaceCreate,current : user =Depends(current_user), db: AsyncSession = Depends(get_async_session)):
    print(new_workplace)
    stmt = insert(workplace).values(**new_workplace.dict())
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}


@router.put("/workplace/{id}")
async def replace_workplace(
        id: int,
        workplace_data: WorkPlaceCreate,
        current : user =Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        # Проверка существования записи
        query = select(workplace).where(workplace.c.id == id)
        result = await session.execute(query)
        existing_workplace = result.fetchone()

        if not existing_workplace:
            raise HTTPException(status_code=404, detail="Workplace not found")

            # Полное обновление записи
        update_query = (
            update(workplace)
            .where(workplace.c.id == id)
            .values(
                max_people=workplace_data.max_people,
                title=workplace_data.title,
                current_people=workplace_data.current_people,
                camera_url=workplace_data.camera_url,
                green_zone_coordinates=workplace_data.green_zone_coordinates,
                red_zone_coordinates=workplace_data.red_zone_coordinates,
                face_detection=workplace_data.face_detection
            )
            .execution_options(synchronize_session="fetch")
        )
        await session.execute(update_query)
        await session.commit()

        # Получение обновленной записи для возврата
        updated_result = await session.execute(query)
        updated_workplace = updated_result.fetchone()

        if not updated_workplace:
            raise HTTPException(status_code=404, detail="Updated workplace not found")

        return {
            "status": "success",
            "data": dict(updated_workplace._mapping),
            "details": None
        }
    except Exception as e:
        await session.rollback()  # Откат транзакции в случае ошибки
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "details": str(e)
            }
        )

# Подключаем папку static для отдачи статических файлов

@router.get("/image/{image_name}")
def get_workplace_image(image_name: str):
    return {"url": f"/static/{image_name}"}

@router.get("/specific/workplace")
async def get_specific_workplace(id: int,current=Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(workplace).where(workplace.c.id == id)
        result = await session.execute(query)
        return {
            "status": "success",
            "workplace": [dict(r._mapping) for r in result],
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.get("/workplace")
async def getworkplace(current : user =Depends(current_user),session: AsyncSession = Depends(get_async_session)):
    query = select(workplace)
    result = await session.execute(query)
    workplaces = result.all()  # Преобразуем
    return {
        "status": "success",
        "data": [dict(work._mapping) for work in workplaces],
        "details": None
    }


@router.delete("/workplace/{id}")
async def delete_workplace(id: int,current : user =Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        # Проверка существования записи
        query = select(workplace).where(workplace.c.id == id)
        result = await session.execute(query)
        existing_workplace = result.scalar_one_or_none()

        if not existing_workplace:
            raise HTTPException(status_code=404, detail="Workplace not found")

            # Удаление записи
        delete_query = delete(workplace).where(workplace.c.id == id)
        await session.execute(delete_query)
        await session.commit()

        return {
            "status": "success",
            "data": None,
            "details": f"Workplace with ID {id} has been deleted"
        }
    except Exception as e:
        await session.rollback()  # Откат транзакции в случае ошибки
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "details": str(e)
            }
        )


@router.post("/user/{user_id}/workplace/{workplace_id}")
async def add_workplace_to_user(user_id: int, workplace_id: int,current : user =Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        # Проверка существования пользователя
        query_user = select(user).where(user.c.id == user_id)
        result_user = await session.execute(query_user)
        existing_user = result_user.scalar_one_or_none()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

            # Проверка существования рабочего места
        query_workplace = select(workplace).where(workplace.c.id == workplace_id)
        result_workplace = await session.execute(query_workplace)
        existing_workplace = result_workplace.scalar_one_or_none()

        if not existing_workplace:
            raise HTTPException(status_code=404, detail="Workplace not found")

            # Проверка существования связи между пользователем и рабочим местом
        query_user_workplace = select(user_workplace).where(
            (user_workplace.c.user_id == user_id) &
            (user_workplace.c.workplace_id == workplace_id)
        )
        result_user_workplace = await session.execute(query_user_workplace)
        existing_user_workplace = result_user_workplace.scalar_one_or_none()

        if existing_user_workplace:
            raise HTTPException(status_code=400, detail="User already has this workplace")

            # Добавление рабочего места пользователю
        insert_query = insert(user_workplace).values(user_id=user_id, workplace_id=workplace_id)
        await session.execute(insert_query)
        await session.commit()

        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "workplace_id": workplace_id
            },
            "details": "Workplace added to user successfully"
        }
    except Exception as e:
        await session.rollback()  # Откат транзакции в случае ошибки
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "details": str(e)
            }
        )


@router.get("/user/{user_id}/workplaces", response_model=List[WorkPlaceCreate])
async def get_user_workplaces(user_id: int,current : user =Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        # Проверка существования пользователя
        query_user = select(user).where(user.c.id == user_id)
        result_user = await session.execute(query_user)
        existing_user = result_user.scalar_one_or_none()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

            # Получение всех рабочих мест пользователя
        query_workplaces = (
            select(workplace)
            .join(user_workplace, user_workplace.c.workplace_id == workplace.c.id)
            .where(user_workplace.c.user_id == user_id)
        )
        result_workplaces = await session.execute(query_workplaces)
        workplaces = result_workplaces.fetchall()

        if not workplaces:
            raise HTTPException(status_code=404, detail="No workplaces found for this user")

        return [dict(w._mapping) for w in workplaces]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "details": str(e)
            }
        )


@router.get("/user/workplaces", response_model=List[WorkPlaceCreate])
async def get_user_workplaces_auth(current : user =Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        # Проверка существования пользователя
        query_user = select(user).where(user.c.id == current.id)
        result_user = await session.execute(query_user)
        existing_user = result_user.scalar_one_or_none()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

            # Получение всех рабочих мест пользователя
        query_workplaces = (
            select(workplace)
            .join(user_workplace, user_workplace.c.workplace_id == workplace.c.id)
            .where(user_workplace.c.user_id == current.id)
        )
        result_workplaces = await session.execute(query_workplaces)
        workplaces = result_workplaces.fetchall()

        if not workplaces:
            raise HTTPException(status_code=404, detail="No workplaces found for this user")

        return [dict(w._mapping) for w in workplaces]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "data": None,
                "details": str(e)
            }
        )
