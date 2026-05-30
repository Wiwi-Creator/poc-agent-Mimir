from app.memory.workout_store import WorkoutStore


def test_workout_store_adds_and_reads_recent_entries(tmp_path):
    store = WorkoutStore(str(tmp_path / "workouts.sqlite3"))

    store.add_entry(
        user_id="user-1",
        exercise="bench",
        weight_kg=80,
        reps=5,
        sets=3,
        notes="Log bench 80kg for 5 reps, 3 sets",
    )

    entries = store.recent_entries("user-1", exercise="bench")

    assert len(entries) == 1
    assert entries[0].exercise == "bench"
    assert entries[0].weight_kg == 80
    assert entries[0].reps == 5
    assert entries[0].sets == 3

