from app.memory.user_state_store import UserStateStore


def test_user_state_store_tracks_seen_intro(tmp_path):
    db_path = str(tmp_path / "user_state.sqlite3")
    store = UserStateStore(db_path)

    assert not store.has_seen_intro("user-1")

    store.mark_seen_intro("user-1")

    assert store.has_seen_intro("user-1")
    assert UserStateStore(db_path).has_seen_intro("user-1")

