import json
from pathlib import Path

from app.importers.snapshots import FileRawSnapshotStore


def test_snapshot_is_content_addressed_and_immutable(tmp_path: Path) -> None:
    store = FileRawSnapshotStore(tmp_path)
    first = store.save("parking", b'{"data":[]}', source_url="https://example.gov/data")
    second = store.save("parking", b'{"data":[]}', source_url="https://example.gov/data")

    assert first.content_hash == second.content_hash
    assert first.payload_path == second.payload_path
    assert first.payload_path.read_bytes() == b'{"data":[]}'
    metadata = json.loads(first.metadata_path.read_text(encoding="utf-8"))
    assert metadata["content_hash"] == first.content_hash
    assert metadata["source_url"] == "https://example.gov/data"
