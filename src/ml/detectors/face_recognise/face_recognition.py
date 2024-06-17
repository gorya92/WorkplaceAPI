import os
import cv2
import numpy as np
import face_recognition

known_face_encodings = []
known_face_names = []

# Путь к папке с известными лицами
known_faces_dir = "static-worker"

def load_images():
    # Загрузка изображений из папки
    for filename in os.listdir(known_faces_dir):
        file_path = os.path.join(known_faces_dir, filename)
        # Проверка, что файл является изображением и не является директорией
        if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:  # Проверка, что лицо было обнаружено
                known_face_encodings.append(encodings[0])
                known_face_names.append(os.path.splitext(filename)[0])  # Имя без расширения

# Путь к папке с изображениями и filename
STATIC_FOLDER = "static"

def recognize_faces_in_image(filename):
    image_path = os.path.join(STATIC_FOLDER, filename)
    unknown_image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(unknown_image)
    if not face_locations:  # Проверка на отсутствие лиц
        return None, []  # Возвращаем пустые результаты
    face_encodings = face_recognition.face_encodings(unknown_image, face_locations)
    face_names = []
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if face_distances.size > 0:  # Проверяем, что face_distances не пуст
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
        face_names.append(name)
        cv2.rectangle(unknown_image, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(unknown_image, name, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 2)
    output_image = cv2.cvtColor(unknown_image, cv2.COLOR_RGB2BGR)
    output_path = os.path.join(STATIC_FOLDER, filename)
    cv2.imwrite(output_path, output_image)
    return output_path, face_names

# Загрузка известных лиц
