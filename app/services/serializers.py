from app.models import User, WorkoutPlan
from app.schemas import WorkoutPlanAI


def plan_from_json(text: str) -> WorkoutPlanAI:
    return WorkoutPlanAI.model_validate_json(text)


def plan_to_json(plan: WorkoutPlanAI) -> str:
    return plan.model_dump_json(indent=2)


def user_to_dict(user: User, plan: WorkoutPlan | None) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "original_plan": plan.original_plan if plan else None,
        "updated_plan": plan.updated_plan if plan else None,
        "nutrition_tip": plan.nutrition_tip if plan else None,
        "generation_mode": plan.generation_mode if plan else None,
    }
