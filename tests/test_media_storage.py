from app.media.storage import TemporaryMediaStorage


def test_temporary_media_storage_saves_and_deletes_file(tmp_path):
    storage = TemporaryMediaStorage(str(tmp_path))

    attachment = storage.save(
        content=b"image-bytes",
        mime_type="image/jpeg",
        source="test",
    )

    assert attachment.path.exists()
    assert attachment.path.read_bytes() == b"image-bytes"
    assert attachment.mime_type == "image/jpeg"

    storage.delete(attachment)

    assert not attachment.path.exists()

