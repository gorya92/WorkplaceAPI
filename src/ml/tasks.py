import asyncio
import datetime
import io
import os
import shutil
import smtplib
import time

import firebase_admin
from PIL import Image
from celery import Celery
import cv2
from firebase_admin import messaging, credentials
from sqlalchemy import select

from src.auth.models import workplace, user_workplace, user, worker
from src.config import REDIS_HOST, REDIS_PORT
from src.database import get_async_session
from src.ml.detectors import yolov9
from src.ml.detectors.face_recognise.face_recognition import recognize_faces_in_image, load_images

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}')

dt = yolov9.YoloV9ImageObjectDetection()


async def process_workplace_async(workplace_id):
    global device_tokens
    current_people = 0
    start_time = time.time()  # Засекаем время начала выполнения таски
    async for session in get_async_session():
        stmt = select(workplace).where(workplace.c.id == workplace_id)
        result = await session.execute(stmt)
        workplace_data = result.all()
    workList = [map_workplace(work) for work in workplace_data]
    workplace_data = workList[0]
    if workplace_data:
        print("workplace_data")
        print(workplace_data)
        camera_url = workplace_data["camera_url"]
        title = workplace_data["title"]
        face_detection = workplace_data["face_detection"]
        green_zone_coordinates = workplace_data["green_zone_coordinates"]
        red_zone_coordinates = workplace_data["red_zone_coordinates"]
        alert_period = workplace_data["alert_period"] if workplace_data["alert_period"] is not None else 0
        last_notification_sent_at = workplace_data["last_notification_sent_at"]
        cap = cv2.VideoCapture(camera_url)
        if not cap.isOpened():
            print(f"Ошибка: не удалось открыть камеру для рабочей зоны {workplace_id}.")
            return

        ret, frame = cap.read()
        if not ret:
            print(f"Ошибка: не удалось захватить кадр с камеры для рабочей зоны {workplace_id}.")
            return

        _, img_bytes = cv2.imencode(".jpg", frame)
        frame_with_zones, green_count, red_count, output_filename = dt.process_image(
            img_bytes, workplace_id=workplace_id, data1=green_zone_coordinates, data2=red_zone_coordinates
        )
        print(output_filename)
        current_people = green_count

        current_time = datetime.datetime.now()

        send_safety_violation_notification = False
        send_unknown_person_notification = False
        if green_count < workplace_data["max_people"] or red_count > 0:
            alert_period += 1
            if alert_period >= 3:
                # Путь к исходному файлу (изображению)
                source_image = f"static/workplace{workplace_id}.jpg"

                # Путь к целевой папке (куда будем копировать)
                destination_folder = 'static-incorrect'

                # Создаем целевую папку, если она еще не существует
                os.makedirs(destination_folder, exist_ok=True)

                # Путь к целевому файлу (куда будем копировать изображение)
                destination_image = os.path.join(destination_folder, f"workplace{workplace_id}.jpg")

                try:
                    shutil.copyfile(source_image, destination_image)
                    print(f"Copied {source_image} to {destination_image}")
                except Exception as e:
                    print(f"Failed to copy {source_image} to {destination_image}: {e}")
                if not last_notification_sent_at or current_time >= last_notification_sent_at + datetime.timedelta(
                        minutes=15):
                    send_safety_violation_notification = True
                    last_notification_sent_at = current_time
                alert_period = 0
        else:
            if (face_detection == True):
                async for sessionName in get_async_session():
                    stmtName = select(worker.c.name).where(worker.c.workplace_id == workplace_id)
                    result = await sessionName.execute(stmtName)
                print(result)
                worker_names = [row[0] for row in result.fetchall()]
                print(worker_names)
                print(f"workplace{workplace_id}.jpg")
                a, face_names = recognize_faces_in_image(f"workplace{workplace_id}.jpg")
                print(a)
                print(face_names)
                # Проверка, что все имена в face_names присутствуют в worker_names
                all_valid_names = all(name in worker_names for name in face_names)

                # Проверка, что все имена из worker_names присутствуют в face_names
                no_extra_names = all(name in face_names for name in worker_names)

                # Список имен, которые присутствуют и в face_names, и в worker_names
                matching_names = [name for name in face_names if name in worker_names]
                # Количество совпавших людей
                current_people = len(matching_names)

                if all_valid_names and no_extra_names:
                    alert_period = 0
                else:
                    alert_period += 1
                    if alert_period >= 3:
                        print("вход")
                        # Путь к исходному файлу (изображению)
                        source_image = f"static/workplace{workplace_id}.jpg"

                        # Путь к целевой папке (куда будем копировать)
                        destination_folder = 'static-incorrect'

                        # Создаем целевую папку, если она еще не существует
                        os.makedirs(destination_folder, exist_ok=True)

                        # Путь к целевому файлу (куда будем копировать изображение)
                        destination_image = os.path.join(destination_folder, f"workplace{workplace_id}.jpg")

                        try:
                            shutil.copyfile(source_image, destination_image)
                            print(f"Copied {source_image} to {destination_image}")
                        except Exception as e:
                            print(f"Failed to copy {source_image} to {destination_image}: {e}")
                        if not last_notification_sent_at or current_time >= last_notification_sent_at + datetime.timedelta(
                                minutes=15):
                            send_unknown_person_notification = True
                            last_notification_sent_at = current_time
                        alert_period = 0
            else:
                alert_period = 0

            # Отправка уведомлений, если необходимо
        async for session in get_async_session():
            stmt = select(user.c.device_token).select_from(user_workplace.join(user)).where(
                user_workplace.c.workplace_id == workplace_id)
            result = await session.execute(stmt)
            device_tokens = [row.device_token for row in result.fetchall()]

        if send_safety_violation_notification:
            for device_token in device_tokens:
                if device_token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="Обнаружено отсутствие на рабочем месте",
                            body=title,
                        ),
                        token=device_token,
                    )
                    # Отправляем сообщение
                    messaging.send(message)

        if send_unknown_person_notification:
            for device_token in device_tokens:
                if device_token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="Неизвестный человек на рабочем месте",
                            body=title,
                        ),
                        token=device_token,
                    )
                    # Отправляем сообщение
                    messaging.send(message)

        async for session in get_async_session():
            stmt = workplace.update().where(workplace.c.id == workplace_id).values(current_people=current_people)
            await session.execute(stmt)
            await session.commit()  # Проверка условий для отправки push-уведомления

        # Обновление значения alert_period в базе данных
        async for session in get_async_session():
            stmt = workplace.update().where(workplace.c.id == workplace_id).values(
                alert_period=alert_period,
                last_notification_sent_at=last_notification_sent_at
            )
            await session.execute(stmt)
            await session.commit()

        end_time = time.time()  # Засекаем время окончания выполнения таски
        execution_time = end_time - start_time  # Рассчитываем время выполнения
        print(f"Время выполнения номера{workplace_id}: {execution_time} секунд.")

        cap.release()


@celery.task(bind=True, name='celery:process_workplace')
def process_workplace(self, workplace_id):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_workplace_async(workplace_id))


def map_workplace(row):
    return {
        "id": row.id,
        "title": row.title,
        "max_people": row.max_people,
        "current_people": row.current_people,
        "camera_url": row.camera_url,
        "green_zone_coordinates": row.green_zone_coordinates,
        "red_zone_coordinates": row.red_zone_coordinates,
        "alert_period": row.alert_period,
        "face_detection": row.face_detection,
        "last_notification_sent_at": row.last_notification_sent_at
    }


async def process_all_workplaces_async():
    async for session in get_async_session():
        query = select(workplace)
        result = await session.execute(query)
        workplaces = result.scalars().all()
        print(workplaces)
    for workplac in workplaces:
        process_workplace.delay(workplac)


start_time = time.time()

firebase_initialized = False


@celery.task(bind=True, ignore_result=True)
def process_all_workplaces(self):
    global firebase_initialized
    current_time = datetime.datetime.now().time()
    if (datetime.time(8, 0) <= current_time <= datetime.time(12, 0)) or (
            datetime.time(13, 0) <= current_time <= datetime.time(18, 0)):
        if not firebase_initialized:
            cred = credentials.Certificate("firebase.json")
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
        load_images()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_all_workplaces_async())


celery.conf.beat_schedule = {
    'run-me-every-n-seconds': {
        'task': 'src.ml.tasks.process_all_workplaces',
        'schedule': 30.0
    },
}
