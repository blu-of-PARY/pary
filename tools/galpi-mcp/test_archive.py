"""Contract tests using a synthetic Galpi backup, never personal archive data."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from archive import ArchiveError, GalpiArchive


THOUGHT = "11111111-1111-4111-8111-111111111111"
SOURCE = "22222222-2222-4222-8222-222222222222"
TRASHED = "33333333-3333-4333-8333-333333333333"
ARCHIVED = "44444444-4444-4444-8444-444444444444"


def make_backup(path: Path) -> None:
    data = {
        "entries": [
            {"id": THOUGHT, "rawText": "old raw text", "editedText": "Read slowly, then write one thought.",
             "createdAt": 0, "archivedAt": None, "sourceTitle": "Reading notebook"},
            {"id": TRASHED, "editedText": "private trash", "createdAt": 0, "archivedAt": None},
            {"id": ARCHIVED, "editedText": "private archive", "createdAt": 0, "archivedAt": 1},
        ],
        "sourceItems": [
            {"id": SOURCE, "title": "A leaf about slow reading", "url": "https://example.org/leaf",
             "excerpt": "Reading at my own pace. 책", "note": "Keep this leaf", "capturedAt": 3600,
             "archivedAt": None},
        ],
        "entrySourceLinks": [{"entryID": THOUGHT, "sourceItemID": SOURCE}],
        "trashItemStates": [{"itemID": TRASHED, "kindRawValue": "entry"}],
        "entryAssets": [{"relativePath": "assets/secret-photo.jpg"}],
        "routineConfigs": [{"apiKey": "synthetic-secret-key"}],
    }
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("ThoughtArchiveBackup/data.json", json.dumps(data))
        package.writestr("ThoughtArchiveBackup/manifest.json",
                         json.dumps({"exportedAt": "2026-09-17T00:00:00Z"}))
        package.writestr("ThoughtArchiveBackup/assets/secret-photo.jpg", b"fake image")


class GalpiArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.backup = Path(self.temp.name) / "galpi.zip"
        make_backup(self.backup)
        self.before_hash = hashlib.sha256(self.backup.read_bytes()).hexdigest()

    def test_search_links_and_privacy_filter(self) -> None:
        archive = GalpiArchive(self.backup)
        self.assertEqual(archive.counts(), {"thoughts": 1, "savedSources": 1})
        self.assertEqual(archive.exported_at, "2026-09-17T00:00:00Z")
        self.assertEqual({r["id"] for r in archive.search("slow")}, {SOURCE, THOUGHT})
        self.assertEqual([r["id"] for r in archive.search("책")], [SOURCE])
        self.assertEqual(archive.get(THOUGHT)["relatedIds"], [SOURCE])
        self.assertEqual(archive.get(SOURCE)["relatedIds"], [THOUGHT])
        self.assertEqual(archive.get(SOURCE)["galpiURL"], f"thoughtarchive://sources/{SOURCE}")
        self.assertEqual(archive.get(THOUGHT)["body"], "Read slowly, then write one thought.")
        self.assertEqual(archive.get(THOUGHT)["date"], "2001-01-01T00:00:00+00:00")
        self.assertIsNone(archive.get(TRASHED))
        self.assertIsNone(archive.get(ARCHIVED))
        exposed = json.dumps(archive.recent(limit=20) + [archive.get(THOUGHT), archive.get(SOURCE)])
        for excluded in ("private trash", "private archive", "old raw text", "synthetic-secret-key", "secret-photo"):
            self.assertNotIn(excluded, exposed)
        self.assertEqual(hashlib.sha256(self.backup.read_bytes()).hexdigest(), self.before_hash)

    def test_bad_package_and_input(self) -> None:
        archive = GalpiArchive(self.backup)
        with self.assertRaises(ArchiveError):
            archive.search("a" * 201)
        with self.assertRaises(ArchiveError):
            archive.recent(kind="delete")
        self.assertIsNone(archive.get("not-a-uuid"))
        bad_path = Path(self.temp.name) / "bad.zip"
        with zipfile.ZipFile(bad_path, "w") as package:
            package.writestr("data.json", "{}")
        with self.assertRaises(ArchiveError):
            GalpiArchive(bad_path)

    def test_stdio_mcp_contract(self) -> None:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        async def check() -> None:
            parameters = StdioServerParameters(
                command=sys.executable,
                args=[str(Path(__file__).with_name("server.py"))],
                env={**os.environ, "GALPI_BACKUP_PATH": str(self.backup)},
            )
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools},
                                     {"archive_info", "search_archive", "get_record", "recent_records"})
                    self.assertTrue(all(tool.annotations.read_only_hint for tool in tools.tools))
                    result = await session.call_tool("search_archive", {"query": "slow"})
                    self.assertFalse(result.is_error)
                    self.assertEqual(len(result.structured_content["results"]), 2)
                    detail = await session.call_tool("get_record", {"record_id": THOUGHT})
                    self.assertEqual(detail.structured_content["record"]["textProvenance"],
                                     "user_recorded_thought")
                    info = await session.call_tool("archive_info")
                    self.assertEqual(info.structured_content["exportedAt"],
                                     "2026-09-17T00:00:00Z")

        asyncio.run(check())
        self.assertEqual(hashlib.sha256(self.backup.read_bytes()).hexdigest(), self.before_hash)


if __name__ == "__main__":
    unittest.main()
