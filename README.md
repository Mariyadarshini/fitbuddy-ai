# FitBuddy AI – Personalized 7-Day Fitness Planner

FitBuddy is a FastAPI + Jinja2 + SQLite web application that generates personalized 7-day workout plans, nutrition/recovery tips, and feedback-based plan revisions. It follows the architecture described in the supplied project documentation while updating the Gemini integration to Google's current `google-genai` SDK.

## Key features

- Responsive HTML/Jinja2 frontend
- FastAPI web routes and JSON API routes
- SQLite + SQLAlchemy persistence
- Gemini-powered workout generation
- Gemini-powered nutrition/recovery tips
- Feedback-based plan updates
- Admin-style `/view-all-users` page
- Automatic deterministic fallback when the Gemini key is missing or quota is unavailable
- Swagger/OpenAPI docs at `/docs`
- Automated tests that run without a Gemini API key

## Important Gemini update

The original documentation uses the discontinued `google-generativeai` Python package and older Gemini model names. This implementation uses `google-genai` and configurable current model IDs instead. See Google's current Gemini documentation for the supported model list.

## Quick start – Windows PowerShell

```powershell
cd fitbuddy-ai
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and put your Gemini API key in `GEMINI_API_KEY` if you have one. The application also works without a key using the local fallback generator.

Run:

```powershell
uvicorn httpapp.main:app --reload
```

Open:

- http://127.0.0.1:8000
- ://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users

## Tests

```powershell
pytest -q
```

## API examples

### Generate a plan

`POST /api/generate-plan`

```json
{
  "user_id": 10,
  "username": "Arun",
  "age": 25,
  "weight": 70,
  "goal": "muscle gain",
  "intensity": "medium"
}
```

### Nutrition tip

`GET /api/nutrition-tip?goal=muscle%20gain`

### Update a plan

`POST /api/update-plan/10`

```json
{
  "feedback": "Add more cardio and one extra rest day."
}
```

## Safety note

FitBuddy provides general wellness content, not medical diagnosis or treatment. Users with injuries, chronic conditions, pregnancy, or other medical concerns should consult a qualified healthcare professional before starting or changing exercise or nutrition plans.
