# Hulk Roadmap

Hulk is Mimir's first specialist sub-agent. His domain is fitness, training, nutrition, meal estimation, physique feedback, posture, and workout logging.

## Current State

Hulk can currently:

- Answer text-based workout questions.
- Estimate meals, calories, and macros from text.
- Discuss physique, posture, and body composition from descriptions.
- Reply through LINE via Mimir routing.
- Stay mostly within fitness and nutrition scope.
- Add simple workout logs to SQLite.
- Read recent workout history before answering.
- Use Hulk-only tool interfaces for Taiwan food lookup and sports science lookup.
- Create and save structured starter workout plans.
- Reuse the latest saved plan as context in later replies.
- Receive LINE image messages.
- Download LINE image content.
- Run first-pass Gemini Flash physique/posture analysis.

Hulk cannot yet:

- Analyze food photos.
- Reliably extract full nutrition facts from every Taiwanese source.
- Reliably summarize full sports science papers.
- Compare progress across photos or videos.

## Implemented Architecture

```text
app/
  agents/
    mimir.py          # Supervisor routing and reply titles
    hulk.py           # Hulk orchestration: guardrails, memory, tools, Groq
    prompts.py        # Mimir and Hulk system prompts
  memory/
    workout_store.py  # SQLite workout log storage
  planning/
    workout_plan.py   # Structured workout plan models and defaults
    plan_store.py     # SQLite workout plan storage
  media/
    storage.py        # Temporary media storage
    models.py         # Media attachment schema
  vision/
    gemini_client.py  # Vertex AI Gemini image client
    analyzer.py       # Physique photo analyzer
    prompts.py        # Vision safety and output prompts
  tools/
    hulk_tools.py     # Hulk-only tool registry
    web_search.py     # Lightweight web search adapter
    workout_parser.py # Workout log parsing helpers
    models.py         # Tool result schema
```

Current Hulk v1 flow:

1. Mimir routes fitness, training, nutrition, meal, macro, physique, and posture messages to Hulk.
2. Hulk checks whether the message is a workout log.
3. If loggable, Hulk saves the parsed workout to SQLite.
4. Hulk reads recent workout history for the user.
5. Hulk creates or reads a saved workout plan when useful.
6. Hulk optionally calls a Hulk-only food or research lookup tool.
7. For LINE image messages, Mimir downloads the image and routes it to Hulk's physique analyzer.
8. Hulk sends text requests plus private context to Groq, or sends image requests to Gemini Flash.
9. Mimir adds the final title:

```text
🟢💪 Hulk :
```

## Phase 1: Better Knowledge

Goal: reduce hallucination by giving Hulk reliable context before he answers.

### 1. Taiwan Food Lookup

Implemented first-pass backend tool:

```text
get_taiwan_food_info(food_name: str)
```

Use cases:

- Convenience store meals.
- Chain restaurant meals.
- Taiwanese packaged foods.
- Local restaurant dishes when public nutrition or review data exists.

Example:

```text
7-11 星宇航空 雞肉飯
```

Expected output:

- Food name.
- Source links.
- Calories/macros if available.
- Portion assumptions.
- Confidence level.

Current limitation:

- Uses lightweight web search context.
- Needs stronger source extraction and structured nutrition parsing later.

### 2. Sports Science Search

Implemented first-pass backend tool:

```text
get_scientific_workout_research(topic: str)
```

Search preferred sources:

- PubMed.
- Stronger by Science.
- Strength and Conditioning Research.
- Examine.com when relevant.

Use cases:

- Hypertrophy volume.
- Strength progression.
- Rest time.
- Deload timing.
- Exercise alternatives.

Current limitation:

- Uses source-constrained search.
- Does not yet fetch and summarize full papers robustly.

### 3. Tool-Aware Hulk Flow

When Hulk needs facts:

1. Detect whether the user needs food lookup or research context.
2. Call the correct tool.
3. Feed the retrieved context back to Hulk.
4. Reply with:

```text
🟢💪 Hulk :
Estimate:
Reasoning:
Next move:
Sources:
```

## Phase 2: Guardrails

Goal: make Hulk disciplined and domain-specific.

### 1. Strict Scope

Hulk should only answer:

- Workout and training.
- Exercise technique.
- Routine planning.
- Set, rep, and weight tracking.
- Nutrition.
- Meal estimates.
- Calories and macros.
- Physique and body composition.
- Posture.

Out of scope examples:

- Coding.
- Cloud architecture.
- Finance.
- General life advice.
- Random chitchat.

Expected refusal:

```text
🟢💪 Hulk :
I only handle fitness, training, and nutrition. Ask Mimir to route this one.
```

### 2. Separate Tool Registry

Hulk should only have access to Hulk tools.

Implemented:

- `HulkToolRegistry` is separate from Mimir.
- Hulk has no access to deployment, shell, coding, or generic automation tools.

Allowed:

- Food lookup.
- Sports science lookup.
- Workout log read/write.
- Photo/video analysis when implemented.

Not allowed:

- Coding tools.
- Shell/system tools.
- Cloud deployment tools.
- Generic automation tools.

### 3. Boundary Tests

In-scope:

```text
我剛吃了一碗牛肉火鍋，一小時後練腿，怎麼安排？
```

Expected:

- Nutrition estimate.
- Training timing advice.
- Hydration and intensity suggestion.

Out-of-scope:

```text
Hulk, help me write Kubernetes YAML for Mimir.
```

Expected:

- Refuse briefly.
- Redirect to Mimir.

## Phase 3: Workout Memory

Goal: make Hulk useful across weeks, not just one message.

### 1. Workout Log Storage

Implemented simple SQLite storage:

- User ID from LINE.
- Exercise.
- Weight.
- Reps.
- Sets.
- RPE if provided.
- Date.
- Notes.

Example:

```text
Log yesterday's bench: 80kg, 5 reps, 3 sets.
```

Expected:

- Parse workout.
- Save record.
- Confirm entry.

### 2. Workout Recommendation

Example:

```text
How much should I squat today?
```

Expected:

- Read recent squat history.
- Estimate working weight.
- Suggest sets/reps.
- Account for fatigue if user mentions it.

Current limitation:

- Hulk receives recent history as context.
- More deterministic strength calculations can be added later.

### 3. Workout Plan Storage

Implemented starter plan storage:

- Structured `WorkoutPlan` model.
- SQLite persistence.
- Default weekly templates.
- Latest saved plan is injected into future Hulk context.

Example:

```text
Build me a 4-day workout plan for hypertrophy.
```

Expected:

- Create a weekly plan.
- Include days, focus, exercises, sets, and reps.
- Save the plan.
- Use it later when the user asks what to train today.

Current limitation:

- The starter template is simple.
- It does not yet parse all user constraints like equipment, injuries, session length, or preferred training days.
- Plan editing commands are not implemented yet.

## Phase 4: Image Support

Goal: handle food photos, physique photos, and lifting videos.

### 1. LINE Image Intake

Implemented first pass:

- Receive LINE image message.
- Download image from LINE Content API.
- Store temporarily.
- Delete after analysis unless progress tracking is enabled.

### 2. Food Photo Analysis

Use a vision model to identify:

- Food items.
- Portion estimates.
- Calories.
- Protein/carbs/fat.
- Confidence.

### 3. Physique Photo Analysis

Implemented first pass with Gemini Flash on Vertex AI:

- Approximate body-fat range, never exact.
- Posture notes.
- Symmetry notes.
- Progress suggestions.

Safety:

- No body shaming.
- No medical diagnosis.
- No exact body-fat claim.

Current limitation:

- Image messages are treated as physique/posture check-ins.
- Food photo mode is not wired yet.
- Progress comparison is not implemented yet.

### 4. Lifting Video Analysis

Later capability:

- Squat depth.
- Bar path.
- Hip shift.
- Butt wink.
- Bench touch point.
- Deadlift back position.

## Phase 5: External Memory Integrations

Goal: connect Hulk to Wiwi's real fitness data.

Options:

- Notion workout database.
- Google Sheets tracker.
- Google Photos progress album.
- GCS bucket for temporary media.

Potential tools:

```text
read_workout_log(user_id, exercise)
write_workout_log(user_id, workout_entry)
find_progress_photo(user_id, date_or_tag)
compare_progress_photos(current_photo, previous_photo)
```

## Phase 6: Async LINE Pipeline

Goal: avoid LINE timeout issues.

Some tasks may take too long:

- Web search.
- Literature lookup.
- Image analysis.
- Video processing.

Future flow:

1. LINE sends webhook.
2. FastAPI validates and immediately returns HTTP 200.
3. Background task processes the request.
4. Bot sends final answer through LINE Push Message API.

## Recommended Next Build Order

1. Improve workout plan parsing for user preferences, available equipment, injuries, and session length.
2. Add plan editing commands like "move chest day to Tuesday".
3. Add deterministic progression helpers.
4. Add stricter out-of-scope tests for Hulk.
5. Improve workout parser for Chinese logs and RPE.
6. Make Taiwan food lookup return structured calories/macros when sources expose them.
7. Make sports science lookup fetch page abstracts/snippets more reliably.
8. Add LINE image intake.
9. Add food photo analysis.
10. Add physique photo analysis.
11. Add Notion or Google Sheets sync.
