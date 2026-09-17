"""Read only the text needed for archive questions from a Galpi backup ZIP."""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


MAX_DATA_JSON_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_JSON_BYTES = 64 * 1024
MAX_RECORDS = 100_000
APPLE_REFERENCE_DATE = datetime(2001, 1, 1, tzinfo=timezone.utc)


class ArchiveError(ValueError):
    pass


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _iso_date(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return (APPLE_REFERENCE_DATE + timedelta(seconds=value)).isoformat()
        except (OverflowError, ValueError):
            return None
    return value if isinstance(value, str) and value else None


def _snippet(value: str, maximum: int = 320) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    return compact[:maximum] + ("…" if len(compact) > maximum else "")


def _uuid(value: Any) -> str:
    try:
        return str(UUID(_text(value)))
    except (ValueError, AttributeError):
        return ""


@dataclass(frozen=True)
class Record:
    id: str
    kind: str
    title: str
    body: str
    date: str | None
    url: str | None
    related_ids: tuple[str, ...]
    source_title: str | None = None
    source_page: str | None = None

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "snippet": _snippet(self.body),
            "date": self.date,
            "relatedIds": list(self.related_ids),
        }
        if self.kind == "saved_source":
            result["galpiURL"] = f"thoughtarchive://sources/{self.id}"
            if self.url:
                result["originalURL"] = self.url
        return result

    def detail(self) -> dict[str, Any]:
        result = self.summary()
        result["body"] = self.body[:20_000]
        result["truncated"] = len(self.body) > 20_000
        if self.source_title:
            result["sourceTitle"] = self.source_title
        if self.source_page:
            result["sourcePage"] = self.source_page
        if self.kind == "thought" and self.url:
            result["sourceURL"] = self.url
        result["textProvenance"] = (
            "user_recorded_thought" if self.kind == "thought" else "saved_external_source"
        )
        return result


class GalpiArchive:
    """A snapshot, never a live connection to the user's iPhone or iCloud."""

    def __init__(self, backup_path: str | Path):
        self.backup_path = Path(backup_path).expanduser().resolve(strict=True)
        if not self.backup_path.is_file():
            raise ArchiveError("GALPI_BACKUP_PATH must point to a backup ZIP file")
        self._records = self._read_records()
        self._by_id = {record.id: record for record in self._records}
        self.exported_at = self._read_export_date()

    def _read_export_date(self) -> str | None:
        try:
            with zipfile.ZipFile(self.backup_path) as package:
                manifests = [info for info in package.infolist()
                             if Path(info.filename).name == "manifest.json" and not info.is_dir()]
                if len(manifests) != 1 or manifests[0].file_size > MAX_MANIFEST_JSON_BYTES:
                    return None
                with package.open(manifests[0]) as stream:
                    raw = stream.read(MAX_MANIFEST_JSON_BYTES + 1)
            if len(raw) > MAX_MANIFEST_JSON_BYTES:
                return None
            return _text(json.loads(raw).get("exportedAt")) or None
        except (OSError, RuntimeError, zipfile.BadZipFile, UnicodeError,
                json.JSONDecodeError, AttributeError):
            return None

    def _read_records(self) -> list[Record]:
        try:
            with zipfile.ZipFile(self.backup_path) as archive:
                candidates = [info for info in archive.infolist()
                              if Path(info.filename).name == "data.json" and not info.is_dir()]
                if len(candidates) != 1:
                    raise ArchiveError("Backup must contain exactly one data.json")
                info = candidates[0]
                if info.file_size > MAX_DATA_JSON_BYTES:
                    raise ArchiveError("Backup text data exceeds the local bridge limit")
                with archive.open(info) as stream:
                    raw = stream.read(MAX_DATA_JSON_BYTES + 1)
                if len(raw) > MAX_DATA_JSON_BYTES:
                    raise ArchiveError("Backup text data exceeds the local bridge limit")
            data = json.loads(raw)
        except (OSError, RuntimeError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as error:
            raise ArchiveError("Could not read Galpi backup data") from error

        if not isinstance(data, dict):
            raise ArchiveError("Galpi backup data has an unexpected shape")
        for key in ("entries", "sourceItems", "entrySourceLinks"):
            if not isinstance(data.get(key), list):
                raise ArchiveError(f"Galpi backup is missing {key}")
        if not isinstance(data.get("trashItemStates", []), list):
            raise ArchiveError("Galpi backup has malformed trash state")
        if len(data["entries"]) + len(data["sourceItems"]) > MAX_RECORDS:
            raise ArchiveError("Backup contains too many records for this local bridge")

        trashed_ids = {
            _uuid(item.get("itemID"))
            for item in data.get("trashItemStates", [])
            if isinstance(item, dict)
        }
        active_entries = {
            _uuid(item.get("id")): item
            for item in data["entries"]
            if isinstance(item, dict) and item.get("archivedAt") is None
            and _uuid(item.get("id")) and _uuid(item.get("id")) not in trashed_ids
        }
        active_sources = {
            _uuid(item.get("id")): item
            for item in data["sourceItems"]
            if isinstance(item, dict) and item.get("archivedAt") is None
            and _uuid(item.get("id")) and _uuid(item.get("id")) not in trashed_ids
        }
        links_by_entry: dict[str, set[str]] = {}
        links_by_source: dict[str, set[str]] = {}
        for link in data["entrySourceLinks"]:
            if not isinstance(link, dict):
                continue
            entry_id = _uuid(link.get("entryID"))
            source_id = _uuid(link.get("sourceItemID"))
            if entry_id in active_entries and source_id in active_sources:
                links_by_entry.setdefault(entry_id, set()).add(source_id)
                links_by_source.setdefault(source_id, set()).add(entry_id)

        records: list[Record] = []
        for record_id, entry in active_entries.items():
            body = _text(entry.get("editedText")) or _text(entry.get("rawText"))
            if not body:
                continue
            source_title = _text(entry.get("sourceTitle"))
            records.append(Record(
                id=record_id,
                kind="thought",
                title=_snippet(body, 80),
                body=body,
                date=_iso_date(entry.get("createdAt")),
                url=_text(entry.get("sourceURL")) or None,
                related_ids=tuple(sorted(links_by_entry.get(record_id, set()))),
                source_title=source_title or None,
                source_page=_text(entry.get("sourcePage")) or None,
            ))
        for record_id, source in active_sources.items():
            title = _text(source.get("title")) or _text(source.get("url")) or "Untitled source"
            body = "\n".join(filter(None, [
                _text(source.get("excerpt")),
                _text(source.get("note")),
            ]))
            records.append(Record(
                id=record_id,
                kind="saved_source",
                title=title,
                body=body,
                date=_iso_date(source.get("capturedAt")),
                url=_text(source.get("url")) or None,
                related_ids=tuple(sorted(links_by_source.get(record_id, set()))),
            ))
        return records

    def counts(self) -> dict[str, int]:
        return {
            "thoughts": sum(record.kind == "thought" for record in self._records),
            "savedSources": sum(record.kind == "saved_source" for record in self._records),
        }

    def search(self, query: str, kind: str = "all", limit: int = 8) -> list[dict[str, Any]]:
        if len(query) > 200:
            raise ArchiveError("query is too long")
        words = [
            word.casefold() for word in re.findall(r"[\w가-힣]+", query)
            if len(word) > 1 or any("가" <= character <= "힣" for character in word)
        ]
        if not words:
            return []
        if kind not in {"all", "thought", "saved_source"}:
            raise ArchiveError("kind must be all, thought, or saved_source")
        limit = max(1, min(limit, 20))
        scored: list[tuple[int, Record]] = []
        for record in self._records:
            if kind != "all" and record.kind != kind:
                continue
            title = record.title.casefold()
            body = record.body.casefold()
            source_title = (record.source_title or "").casefold()
            score = sum((5 if word in title else 0) + (2 if word in body else 0)
                        + (3 if word in source_title else 0) for word in words)
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: (item[0], item[1].date or ""), reverse=True)
        return [record.summary() for _, record in scored[:limit]]

    def recent(self, kind: str = "all", limit: int = 8) -> list[dict[str, Any]]:
        if kind not in {"all", "thought", "saved_source"}:
            raise ArchiveError("kind must be all, thought, or saved_source")
        limit = max(1, min(limit, 20))
        records = [record for record in self._records if kind == "all" or record.kind == kind]
        records.sort(key=lambda record: record.date or "", reverse=True)
        return [record.summary() for record in records[:limit]]

    def get(self, record_id: str) -> dict[str, Any] | None:
        record = self._by_id.get(_uuid(record_id))
        return record.detail() if record else None
