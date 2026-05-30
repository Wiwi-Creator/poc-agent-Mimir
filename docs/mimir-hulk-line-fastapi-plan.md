# Mimir + Hulk LINE Chatbot Plan

## Product Goal

Mimir is a personal supervisor agent that talks with you through a LINE chatbot and delegates specialized tasks to sub-agents. The first sub-agent is **Hulk**, a heavy-lifting fitness coach and nutrition analyzer.

The first milestone is a FastAPI service that receives LINE webhook events, asks Mimir to classify the request, routes fitness and nutrition messages to Hulk, calls Groq for LLM reasoning, and replies back to LINE.

## Agent Roles

### Mimir

Mimir is the top-level supervisor.

Responsibilities:

- Receive all user messages from LINE.
- Maintain the user-facing tone and context.
- Decide whether a message should be handled directly or delegated to a sub-agent.
- Route fitness, workout, physique, body-fat, meal, calorie, and macro requests to Hulk.
- Summarize sub-agent output into a concise LINE-friendly response.
- Later: coordinate multiple sub-agents and shared memory.

### Hulk

Hulk is the first sub-agent.

Role:

> Your heavy-lifting fitness coach and nutrition analyzer.

Capabilities:

- **Physique & Body Fat Analysis**
  - Evaluate body photos for visible shape, symmetry, posture, and approximate body-fat range.
  - Provide non-medical, approximate visual feedback.
  - Suggest training/nutrition focus areas.

- **Meal & Calorie Tracking**
  - Analyze food photos or text descriptions.
  - Estimate calories, protein, carbs, fat, and confidence level.
  - Ask follow-up questions when portion size is unclear.

- **Workout Advice**
  - Provide quick routine adjustments.
  - Suggest exercise alternatives.
  - Track sets/reps/weight from chat messages.
  - Give short coaching responses suitable for LINE.

## Architecture

```text
LINE User
   |
   v
LINE Messaging API
   |
   v
FastAPI Webhook /line/webhook
   |
   v
Webhook Verification + Event Parser
   |
   v
Mimir Supervisor Agent
   |
   +--> Hulk Agent
   |      |
   |      +--> Groq LLM API
   |      +--> Optional image analysis pipeline
   |
   v
LINE Reply API
   |
   v
LINE User
```

## Proposed Tech Stack

- **Backend:** FastAPI
- **Server:** Uvicorn
- **LINE SDK:** `line-bot-sdk`
- **LLM Provider:** Groq API
- **Config:** `.env` with `pydantic-settings`
- **HTTP Client:** `httpx`
- **Image Handling:** LINE content API download, local temp file or object storage later
- **Testing:** `pytest`, `httpx.AsyncClient`
- **Deployment Options:** Render, Fly.io, Railway, Cloud Run, or any public HTTPS host

## Environment Variables

```env
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
GROQ_API_KEY=
GROQ_MODEL=
APP_ENV=local
LOG_LEVEL=info
```

Suggested initial Groq model:

```env
GROQ_MODEL=llama-3.1-8b-instant
```

If image understanding is required through Groq, confirm which Groq vision model is currently available before implementation. If Groq vision is not suitable, use an image-captioning or multimodal provider behind a separate adapter while keeping Hulk's interface unchanged.

## Repository Structure

```text
poc-agent-Mimir/
  app/
    __init__.py
    main.py
    config.py
    line/
      __init__.py
      webhook.py
      client.py
      parser.py
    agents/
      __init__.py
      mimir.py
      hulk.py
      prompts.py
      schemas.py
    llm/
      __init__.py
      groq_client.py
    memory/
      __init__.py
      store.py
    services/
      __init__.py
      image_service.py
      nutrition_estimator.py
      workout_tracker.py
  tests/
    test_line_webhook.py
    test_mimir_routing.py
    test_hulk.py
  docs/
    mimir-hulk-line-fastapi-plan.md
  .env.example
  pyproject.toml
  README.md
```

## Core Request Flow

### Text Message

1. LINE sends webhook event to `POST /line/webhook`.
2. FastAPI verifies LINE signature using `LINE_CHANNEL_SECRET`.
3. Parser converts LINE event into an internal `UserMessage`.
4. Mimir classifies the intent.
5. If the intent is fitness, meal, calories, macros, physique, or workout tracking, Mimir delegates to Hulk.
6. Hulk builds a focused prompt and calls Groq.
7. Mimir optionally formats Hulk's result.
8. FastAPI replies using LINE Reply API.

### Image Message

1. LINE sends an image event.
2. FastAPI verifies signature.
3. Backend downloads the image from LINE content API using `message_id`.
4. Mimir routes the image based on optional user context:
   - Recent text says meal, food, calories, macros -> Hulk meal analysis.
   - Recent text says physique, body fat, progress, posture -> Hulk physique analysis.
   - Unknown image intent -> ask a short clarification.
5. Hulk analyzes image using the selected vision strategy.
6. Reply includes estimates, confidence, and one useful next action.

## Internal Message Schema

```python
class UserMessage(BaseModel):
    user_id: str
    platform: Literal["line"]
    message_type: Literal["text", "image"]
    text: str | None = None
    image_path: str | None = None
    line_reply_token: str
    timestamp_ms: int
```

```python
class AgentResponse(BaseModel):
    agent_name: str
    text: str
    confidence: float | None = None
    structured_data: dict | None = None
```

## Mimir Routing Policy

Initial routing can be rule-assisted before adding a full router model.

Route to Hulk when the message includes:

- Workout terms: `bench`, `squat`, `deadlift`, `sets`, `reps`, `PR`, `program`, `routine`
- Nutrition terms: `meal`, `food`, `calorie`, `protein`, `carbs`, `fat`, `macros`
- Physique terms: `body fat`, `cut`, `bulk`, `lean`, `posture`, `progress photo`
- Image plus recent context related to food, physique, or training

Otherwise, Mimir can answer directly or say that only Hulk is enabled for now.

## Hulk Response Style

Hulk should be:

- Direct and practical.
- Fitness-coach-like, but not aggressive.
- Honest about uncertainty.
- Short enough for LINE.
- Clear when something is an estimate.
- Careful with health claims and eating disorder-sensitive language.

Example response pattern:

```text
Estimate: 650-800 kcal
Protein: 35-45g
Carbs: 70-90g
Fat: 18-28g

Confidence: medium. Rice portion is the biggest unknown.
Next move: add one palm-sized lean protein if this is post-workout.
```

## Safety Boundaries

Hulk should not:

- Diagnose medical conditions.
- Claim exact body-fat percentage from a photo.
- Encourage extreme dieting, dehydration, or unsafe training.
- Give injury treatment beyond basic caution and recommending a professional.
- Shame the user's body or food choices.

Use phrasing like:

- "Approximate visual range"
- "This is an estimate"
- "If pain is sharp or persistent, stop and check with a qualified professional"

## API Endpoints

### Health

```http
GET /health
```

Returns service status.

### LINE Webhook

```http
POST /line/webhook
```

Receives LINE events and replies through LINE Messaging API.

### Optional Local Debug Endpoint

```http
POST /debug/chat
```

Allows testing Mimir/Hulk without LINE.

Request:

```json
{
  "user_id": "local-test",
  "message_type": "text",
  "text": "I did bench 80kg for 5, 5, 4. What should I do next?"
}
```

## Implementation Milestones

### Milestone 1: FastAPI Skeleton

- Create `pyproject.toml`.
- Add FastAPI app in `app/main.py`.
- Add `/health`.
- Add `.env.example`.
- Add config loading.
- Add basic tests.

### Milestone 2: LINE Webhook

- Add LINE SDK.
- Implement signature verification.
- Parse text messages.
- Reply with a fixed test response.
- Test with ngrok or deployed HTTPS endpoint.

### Milestone 3: Groq Client

- Add `GroqClient`.
- Load `GROQ_API_KEY` and `GROQ_MODEL`.
- Implement text completion helper.
- Add `/debug/chat` for local Mimir testing.

### Milestone 4: Mimir Supervisor

- Add routing rules.
- Add Mimir prompt.
- Return direct response or delegate to Hulk.
- Add tests for routing.

### Milestone 5: Hulk Text Workflows

- Implement workout advice prompt.
- Implement text-based meal estimation prompt.
- Implement structured response schema.
- Add tests for common workout and meal cases.

### Milestone 6: Image Handling

- Download images from LINE content API.
- Store temporarily.
- Add image intent detection.
- Add adapter interface for vision models.
- Implement meal-photo and physique-photo workflows.

### Milestone 7: Memory

- Start with simple local JSON or SQLite memory.
- Store recent messages and workout logs.
- Store user profile basics:
  - Body weight
  - Training goal
  - Dietary target
  - Injury notes
  - Preferred units

### Milestone 8: Deployment

- Choose host.
- Configure HTTPS webhook URL in LINE Developers Console.
- Add production environment variables.
- Add logging.
- Add basic request tracing.

## First Development Order

1. Build FastAPI skeleton.
2. Add LINE webhook verification and text reply.
3. Add Groq text client.
4. Add Mimir router.
5. Add Hulk for text workout and meal requests.
6. Add image download and vision adapter.
7. Add memory.
8. Deploy.

## Questions To Resolve Before Coding

- Should Mimir respond in English, Chinese, or mixed language by default?
- Should Hulk use metric units only, or support both kg/lb?
- Which deployment target do you prefer?
- Do you want workout and nutrition history stored locally first, or in a cloud database from day one?
- Should body photos be deleted immediately after analysis, or retained for progress comparison?

## Recommended MVP Scope

For the first usable version:

- LINE text webhook.
- Groq-powered Mimir + Hulk.
- Text-based workout advice.
- Text-based meal and macro estimation.
- Simple memory for recent context.
- Ask clarification for image messages instead of analyzing them immediately.

Then add image analysis once the LINE and agent workflow is reliable.
