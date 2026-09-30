from typing import Literal

from pydantic import BaseModel, Field, field_validator

Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    user_id: int = Field(ge=1, le=2_147_483_647)
    username: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=400)
    goal: str = Field(min_length=3, max_length=500)
    intensity: Intensity

    @field_validator("username", "goal")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


class FeedbackRequest(BaseModel):
    feedback: str = Field(min_length=3, max_length=2000)


class DayPlan(BaseModel):
    day: str
    focus: str
    warm_up: list[str]
    workout: list[str]
    cooldown: list[str]
    recovery_tip: str


class WorkoutPlanAI(BaseModel):
    summary: str
    days: list[DayPlan] = Field(min_length=7, max_length=7)


class PlanResponse(BaseModel):
    message: str
    user_id: int
    model: str
    generation_mode: str
    workout_plan: WorkoutPlanAI
    nutrition_tip: str


class UpdateResponse(BaseModel):
    message: str
    user_id: int
    model: str
    generation_mode: str
    updated_plan: WorkoutPlanAI
