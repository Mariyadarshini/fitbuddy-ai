import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .crud import (
    get_all_users,
    get_latest_plan,
    get_user_with_plan,
    save_plan,
    update_plan,
    upsert_user,
)
from .database import get_db
from .schemas import FeedbackRequest, PlanResponse, UpdateResponse, UserInput
from .services.gemini_service import ai_service
from .services.serializers import plan_from_json, plan_to_json, user_to_dict


logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent

TEMPLATES = Jinja2Templates(
    directory=str(BASE_DIR / "../templates")
)


# ============================================================
# HOME PAGE
# ============================================================

@router.get("/", response_class=HTMLResponse, name="home")
def home(request: Request):
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
        },
    )


# ============================================================
# GENERATE WORKOUT - WEB FORM
# ============================================================

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
    request: Request,
    user_id: int = Form(...),
    username: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Create user input data
        data = UserInput(
            user_id=user_id,
            username=username,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

        # Generate workout using AI
        ai_plan = ai_service.generate_workout(data)

        # Generate nutrition tip
        nutrition = ai_service.generate_nutrition_tip(data.goal)

        # Save user
        user = upsert_user(db, data)

        # Save workout plan
        plan = save_plan(
            db,
            data.user_id,
            plan_to_json(ai_plan.value),
            nutrition.value,
            ai_plan.mode,
        )

        # Commit database changes
        db.commit()

        # Show result page
        return TEMPLATES.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "request": request,
                "user": user,
                "plan": ai_plan.value,
                "nutrition_tip": nutrition.value,
                "generation_mode": ai_plan.mode,
                "model": ai_plan.model,
                "plan_id": plan.id,
                "message": None,
            },
        )

    except Exception as exc:
        db.rollback()

        logger.exception("Web plan generation failed")

        # Show error page
        return TEMPLATES.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "request": request,
                "message": str(exc),
            },
            status_code=400,
        )


# ============================================================
# SUBMIT FEEDBACK
# ============================================================

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request,
    user_id: int = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Get user and stored workout plan
        user, stored_plan = get_user_with_plan(db, user_id)

        if not user or not stored_plan:
            raise HTTPException(
                status_code=404,
                detail="No workout plan found for this user ID.",
            )

        # Convert stored JSON back to workout plan
        original = plan_from_json(stored_plan.original_plan)

        # Update workout using feedback
        result = ai_service.update_workout(
            original,
            feedback,
        )

        # Update database
        update_plan(
            db,
            stored_plan,
            plan_to_json(result.value),
            result.mode,
        )

        # Commit changes
        db.commit()

        # Show updated result
        return TEMPLATES.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "request": request,
                "user": user,
                "plan": result.value,
                "nutrition_tip": (
                    stored_plan.nutrition_tip
                    or "Stay hydrated and prioritize recovery."
                ),
                "generation_mode": result.mode,
                "model": result.model,
                "plan_id": stored_plan.id,
                "message": "Your plan has been updated based on your feedback!",
            },
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        logger.exception("Feedback update failed")

        return TEMPLATES.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "request": request,
                "message": str(exc),
            },
            status_code=400,
        )


# ============================================================
# VIEW ALL USERS
# ============================================================

@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):
    records = [
        user_to_dict(user, plan)
        for user, plan in get_all_users(db)
    ]

    return TEMPLATES.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "request": request,
            "users": records,
        },
    )


# ============================================================
# API HEALTH CHECK
# ============================================================

@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "FitBuddy AI",
        "ai_configured": ai_service.configured,
        "fallback_enabled": (
            os.getenv(
                "AI_FALLBACK_ENABLED",
                "true",
            ).lower()
            == "true"
        ),
    }


# ============================================================
# API - GENERATE PLAN
# ============================================================

@router.post(
    "/api/generate-plan",
    response_model=PlanResponse,
)
def generate_plan_api(
    data: UserInput,
    db: Session = Depends(get_db),
):
    try:
        # Generate workout
        workout = ai_service.generate_workout(data)

        # Generate nutrition tip
        nutrition = ai_service.generate_nutrition_tip(
            data.goal
        )

        # Save user
        upsert_user(db, data)

        # Save workout plan
        save_plan(
            db,
            data.user_id,
            plan_to_json(workout.value),
            nutrition.value,
            workout.mode,
        )

        # Commit database changes
        db.commit()

        # Return API response
        return PlanResponse(
            message="Workout plan generated and saved successfully.",
            user_id=data.user_id,
            model=workout.model,
            generation_mode=workout.mode,
            workout_plan=workout.value,
            nutrition_tip=nutrition.value,
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong: {exc}",
        ) from exc


# ============================================================
# API - GEMINI WORKOUT
# ============================================================

@router.post(
    "/api/generate-workout/gemini",
    response_model=PlanResponse,
)
def generate_gemini_workout(
    data: UserInput,
    db: Session = Depends(get_db),
):
    return generate_plan_api(data, db)


# ============================================================
# API - NUTRITION TIP
# ============================================================

@router.get("/api/nutrition-tip")
def nutrition_tip(goal: str):
    if not goal.strip():
        raise HTTPException(
            status_code=400,
            detail="Goal is required.",
        )

    result = ai_service.generate_nutrition_tip(
        goal.strip()
    )

    return {
        "goal": goal,
        "nutrition_tip": result.value,
        "model": result.model,
        "generation_mode": result.mode,
    }


# ============================================================
# API - UPDATE WORKOUT PLAN
# ============================================================

@router.post(
    "/api/update-plan/{user_id}",
    response_model=UpdateResponse,
)
def update_user_plan(
    user_id: int,
    data: FeedbackRequest,
    db: Session = Depends(get_db),
):
    # Find user and stored plan
    user, stored_plan = get_user_with_plan(
        db,
        user_id,
    )

    if not user or not stored_plan:
        raise HTTPException(
            status_code=404,
            detail="Original plan not found for this user.",
        )

    try:
        # Convert stored JSON to workout plan
        original = plan_from_json(
            stored_plan.original_plan
        )

        # Update workout using feedback
        result = ai_service.update_workout(
            original,
            data.feedback,
        )

        # Save updated plan
        update_plan(
            db,
            stored_plan,
            plan_to_json(result.value),
            result.mode,
        )

        # Commit database changes
        db.commit()

        # Return response
        return UpdateResponse(
            message="Workout plan updated successfully.",
            user_id=user_id,
            model=result.model,
            generation_mode=result.mode,
            updated_plan=result.value,
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not update plan: {exc}",
        ) from exc