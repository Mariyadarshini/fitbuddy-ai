from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User, WorkoutPlan
from .schemas import UserInput
from .services.serializers import plan_to_json


def upsert_user(db: Session, data: UserInput) -> User:
    user = db.get(User, data.user_id)
    if user is None:
        user = User(id=data.user_id, name=data.username, age=data.age, weight=data.weight, goal=data.goal, intensity=data.intensity)
        db.add(user)
    else:
        user.name = data.username
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity
    db.flush()
    return user


def save_plan(db: Session, user_id: int, plan_json: str, nutrition_tip: str, generation_mode: str) -> WorkoutPlan:
    plan = WorkoutPlan(
        user_id=user_id,
        original_plan=plan_json,
        nutrition_tip=nutrition_tip,
        generation_mode=generation_mode,
    )
    db.add(plan)
    db.flush()
    return plan


def get_latest_plan(db: Session, user_id: int) -> WorkoutPlan | None:
    return db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.created_at.desc())
        .limit(1)
    )


def update_plan(db: Session, plan: WorkoutPlan, plan_json: str, generation_mode: str) -> WorkoutPlan:
    plan.updated_plan = plan_json
    plan.generation_mode = generation_mode
    db.flush()
    return plan


def get_user_with_plan(db: Session, user_id: int) -> tuple[User | None, WorkoutPlan | None]:
    user = db.get(User, user_id)
    return user, get_latest_plan(db, user_id) if user else None


def get_all_users(db: Session) -> list[tuple[User, WorkoutPlan | None]]:
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [(user, get_latest_plan(db, user.id)) for user in users]
