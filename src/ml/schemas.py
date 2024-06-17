from pydantic import BaseModel


class WorkPlaceCreate(BaseModel):
    id: int
    max_people: int
    current_people: int
    title: str
    camera_url: str
    green_zone_coordinates: list
    red_zone_coordinates: list
    face_detection: bool
