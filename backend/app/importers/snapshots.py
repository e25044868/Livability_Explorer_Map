from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RawSnapshot:
    dataset_key: str
    content_hash: str
    fetched_at: str
    payload_path: Path
    metadata_path: Path
    byte_count: int


class FileRawSnapshotStore:
    """以 content hash 保存不可變原始回應；同內容重跑不覆寫。"""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, dataset_key: str, content: bytes, *, source_url: str) -> RawSnapshot:
        digest = hashlib.sha256(content).hexdigest()
        fetched_at = datetime.now(UTC).isoformat()
        target_dir = self.root / dataset_key / digest[:2]
        target_dir.mkdir(parents=True, exist_ok=True)
        payload_path = target_dir / f"{digest}.json"
        metadata_path = target_dir / f"{digest}.metadata.json"
        snapshot = RawSnapshot(
            dataset_key=dataset_key,
            content_hash=digest,
            fetched_at=fetched_at,
            payload_path=payload_path,
            metadata_path=metadata_path,
            byte_count=len(content),
        )
        if not payload_path.exists():
            self._atomic_write(payload_path, content)
        if not metadata_path.exists():
            metadata = asdict(snapshot)
            metadata["payload_path"] = str(payload_path)
            metadata["metadata_path"] = str(metadata_path)
            metadata["source_url"] = source_url
            self._atomic_write(
                metadata_path,
                json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
            )
        return snapshot

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
