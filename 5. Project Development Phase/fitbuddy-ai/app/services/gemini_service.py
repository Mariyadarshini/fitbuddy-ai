import logging
from typing import Any

from pydantic import ValidationError

from app.config import settings
from app.schemas import UserInput, WorkoutPlanAI
from .fallback_generator import fallback_nutrition_tip, generate_fallback_plan

logger = logging.getLogger(__name__)

try:
    from google import genai
except ImportError:  # pragma: no cover - requirements installs it
    genai = None


class AIResult:
    def __init__(self, value: Any, mode: str, model: str):
        self.value = value
        self.mode = mode
        self.model = model


class GeminiService:
    def __init__(self) -> None:
        self.client = None
        if settings.gemini_api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except Exception:
                logger.exception("Could not initialise Gemini client; fallback mode will be used.")

    @property
    def configured(self) -> bool:
        return self.client is not None

    def _generate_text(self, model: str, prompt: str, schema: type[WorkoutPlanAI] | None = None) -> str:
        if self.client is None:
            raise RuntimeError("Gemini API key is not configured.")

        config: dict[str, Any] = {"temperature": 0.7, "max_output_tokens": 5000}
        if schema is not None:
            config.update({"response_mime_type": "application/json", "response_schema": schema})
        response = self.client.models.generate_content(model=model, contents=prompt, config=config)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text.strip()

    def generate_workout(self, user: UserInput) -> AIResult:
        prompt = f"""
You are a careful fitness-planning assistant. Create a practical 7-day general wellness workout plan.
User name: {user.username}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Preferred intensity: {user.intensity}

Requirements:
- Return exactly 7 days.
- Every day must contain warm_up, workout, cooldown, and recovery_tip.
- Keep the plan beginner-friendly unless the requested intensity says otherwise.
- Do not diagnose conditions or prescribe medical treatment.
- Avoid dangerous claims and avoid extreme calorie restriction.
- If an exercise can be modified, give a simple alternative.
""".strip()

        if self.client is not None:
            try:
                text = self._generate_text(settings.workout_model, prompt, WorkoutPlanAI)
                plan = WorkoutPlanAI.model_validate_json(text)
                return AIResult(plan, "gemini", settings.workout_model)
            except (ValidationError, ValueError, RuntimeError, Exception) as exc:
                logger.warning("Gemini workout generation failed: %s", exc)
                if not settings.ai_fallback_enabled:
                    raise

        if not settings.ai_fallback_enabled:
            raise RuntimeError("AI generation failed and fallback is disabled.")
        return AIResult(
            generate_fallback_plan(user.username, user.age, user.weight, user.goal, user.intensity),
            "fallback",
            "local-fallback",
        )

    def generate_nutrition_tip(self, goal: str) -> AIResult:
        prompt = f"""
Give one concise, practical nutrition or recovery tip for someone whose fitness goal is: {goal}.
Use friendly, non-medical language. Do not recommend extreme diets or supplements as a requirement.
Return only the tip, in 1–3 sentences.
""".strip()

        if self.client is not None:
            try:
                text = self._generate_text(settings.nutrition_model, prompt)
                return AIResult(text, "gemini", settings.nutrition_model)
            except Exception as exc:
                logger.warning("Gemini nutrition generation failed: %s", exc)
                if not settings.ai_fallback_enabled:
                    raise

        return AIResult(fallback_nutrition_tip(goal), "fallback", "local-fallback")

    def update_workout(self, original_plan: WorkoutPlanAI, feedback: str) -> AIResult:
        prompt = f"""
You are revising a 7-day fitness plan.

Original plan:
{original_plan.model_dump_json(indent=2)}

User feedback:
{feedback}

Create a revised 7-day plan. Keep useful parts of the original, apply the feedback where sensible,
and preserve the exact JSON structure required by the schema. Do not provide medical diagnosis or
unsafe exercise instructions.
""".strip()

        if self.client is not None:
            try:
                text = self._generate_text(settings.workout_model, prompt, WorkoutPlanAI)
                plan = WorkoutPlanAI.model_validate_json(text)
                return AIResult(plan, "gemini", settings.workout_model)
            except Exception as exc:
                logger.warning("Gemini plan update failed: %s", exc)
                if not settings.ai_fallback_enabled:
                    raise

        # A deterministic fallback keeps the application usable even during API quota errors.
        fallback = generate_fallback_plan(
            "FitBuddy user", 30, 70.0, "general fitness", "medium"
        )
        fallback.summary += f" Feedback incorporated locally: {feedback.strip()}"
        return AIResult(fallback, "fallback", "local-fallback")


ai_service = GeminiService()
