from pydantic import BaseModel
from typing import Optional


class LocationContext(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class UserContext(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    pregnant: Optional[bool] = None
    known_conditions: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []
