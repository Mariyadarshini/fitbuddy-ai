from app.schemas import DayPlan, WorkoutPlanAI


def _goal_key(goal: str) -> str:
    text = goal.lower()
    if any(word in text for word in ("muscle", "strength", "gain", "hypertrophy")):
        return "muscle"
    if any(word in text for word in ("weight", "fat", "lose", "loss", "cut")):
        return "weight_loss"
    if "flex" in text or "mobility" in text:
        return "flexibility"
    return "general"


def generate_fallback_plan(username: str, age: int, weight: float, goal: str, intensity: str) -> WorkoutPlanAI:
    key = _goal_key(goal)
    intensity = intensity.lower()

    focus_map = {
        "muscle": ["Upper body strength", "Lower body strength", "Active recovery", "Push strength", "Pull strength", "Lower body + core", "Full-body recovery"],
        "weight_loss": ["Full-body cardio", "Lower body + intervals", "Active recovery", "Upper body + cardio", "Low-impact conditioning", "Full-body circuit", "Recovery walk + mobility"],
        "flexibility": ["Full-body mobility", "Hips + hamstrings", "Shoulders + spine", "Yoga flow", "Lower-body mobility", "Full-body stretching", "Gentle recovery"],
        "general": ["Full body", "Lower body", "Active recovery", "Upper body", "Core + cardio", "Full body", "Recovery + mobility"],
    }
    focuses = focus_map[key]

    days: list[DayPlan] = []
    for index, focus in enumerate(focuses, start=1):
        if index in (3, 7):
            workout = ["20–30 min easy walk", "10–15 min gentle mobility"]
            warm = ["5 min easy walking", "Gentle joint circles"]
            cooldown = ["5 min slow breathing", "Easy full-body stretches"]
            recovery = "Keep the effort comfortable and prioritize sleep, hydration, and recovery."
        else:
            if key == "muscle":
                workout = [
                    f"{focus}: 3 sets × 8–12 controlled reps",
                    "Bodyweight squat or split squat: 3 × 8–12",
                    "Push-up or incline push-up: 3 × 6–12",
                    "Row variation with safe resistance: 3 × 8–12",
                    "Core exercise: 3 × 20–40 seconds",
                ]
            elif key == "weight_loss":
                workout = [
                    f"{focus}: 5-minute easy + 15-minute moderate effort",
                    "Bodyweight squat: 3 × 10–15",
                    "Incline push-up: 3 × 8–12",
                    "Marching or step-up intervals: 6 × 45 seconds",
                    "Core exercise: 3 × 20–40 seconds",
                ]
            elif key == "flexibility":
                workout = [
                    f"{focus}: 20–30 min controlled mobility flow",
                    "Hamstring stretch: 2 × 30 seconds each side",
                    "Hip-flexor stretch: 2 × 30 seconds each side",
                    "Thoracic rotation: 2 × 8 each side",
                    "Child's pose or comfortable recovery stretch: 2 × 30 seconds",
                ]
            else:
                workout = [
                    f"{focus}: 3 rounds at a sustainable pace",
                    "Bodyweight squat: 3 × 10–15",
                    "Incline push-up: 3 × 8–12",
                    "Hip hinge or glute bridge: 3 × 10–15",
                    "Plank: 3 × 20–40 seconds",
                ]
            warm = ["5–8 min easy walking", "Arm circles and hip mobility"]
            cooldown = ["3–5 min easy walking", "Gentle stretches without bouncing"]
            recovery = "Use a pace that lets you maintain good form; reduce volume if fatigue or discomfort builds."

        if intensity == "low" and index not in (3, 7):
            workout = [item.replace("3 ×", "2 ×") for item in workout]
        elif intensity == "high" and index not in (3, 7):
            workout.append("Optional: one additional easy round if technique remains strong.")

        days.append(
            DayPlan(
                day=f"Day {index}",
                focus=focus,
                warm_up=warm,
                workout=workout,
                cooldown=cooldown,
                recovery_tip=recovery,
            )
        )

    summary = (
        f"A 7-day {intensity}-intensity plan for {username}, age {age}, {weight:.1f} kg, "
        f"with the goal: {goal}. Build consistency first and adjust the workload to your experience."
    )
    return WorkoutPlanAI(summary=summary, days=days)


def fallback_nutrition_tip(goal: str) -> str:
    key = _goal_key(goal)
    tips = {
        "muscle": "Include a protein-rich food in each main meal and pair it with carbohydrates and vegetables for balanced recovery.",
        "weight_loss": "Build meals around vegetables, a protein source, whole-food carbohydrates, and a portion that matches your hunger and activity level.",
        "flexibility": "Hydrate regularly and include a varied diet with protein, fruits, vegetables, and whole grains to support training and recovery.",
        "general": "Prioritize regular meals, vegetables and fruit, protein-rich foods, whole grains, and enough fluids to support everyday activity.",
    }
    return tips[key]
