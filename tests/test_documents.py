import json
import tempfile
import unittest
from pathlib import Path

from silkroad.documents import scan_documents


class DocumentIndexerTests(unittest.TestCase):
    def test_scan_documents_writes_index_and_librarian_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "repo"
            docs_raw = project / "docs" / "raw"
            docs_raw.mkdir(parents=True)
            waypoint = root / "waystation"

            write_json(docs_raw / "001__one.json", {
                "document": {
                    "document-id": "example.doc.v1",
                    "title": "Example Doc",
                    "purpose": "Exercise the Silk Road document indexer.",
                    "tags": ["example"],
                }
            })
            write_json(docs_raw / "002__missing-id.json", {
                "document": {
                    "title": "Missing ID",
                    "purpose": "Should produce a warning.",
                }
            })
            (docs_raw / "003__broken.json").write_text("{ nope", encoding="utf-8")
            (docs_raw / "004__style-card.md").write_text(
                "```\n"
                "document-id: example.style-card.v1\n"
                "title: Example Style Card\n"
                "purpose: Exercise Markdown fenced metadata.\n"
                "tags: style card markdown\n"
                "type: style-card\n"
                "```\n"
                "\n"
                "# Example\n",
                encoding="utf-8",
            )

            config = {
                "waypoints": [{"name": "test", "path": str(waypoint), "enabled": True}],
                "scan_territories": [str(root)],
                "document_roots": [],
                "discovery": {"scan_docs_raw": True, "json_only": True},
            }

            result = scan_documents(config, {})

            self.assertEqual(result["counts"]["files_examined"], 4)
            self.assertEqual(result["counts"]["valid_documents"], 2)
            self.assertEqual(result["counts"]["warnings"], 1)
            self.assertEqual(result["counts"]["failures"], 1)

            index_path = waypoint / "cache" / "silk-road" / "document-index.json"
            librarian_path = waypoint / "cache" / "silk-road" / "librarian-registry.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            librarian = json.loads(librarian_path.read_text(encoding="utf-8"))

            self.assertIn("example.doc.v1", index["documents"])
            self.assertIn("example.style-card.v1", index["documents"])
            style_location = index["documents"]["example.style-card.v1"][0]
            self.assertEqual(style_location["metadata"]["document-id"], "example.style-card.v1")
            self.assertEqual(style_location["metadata"]["type"], "style-card")
            self.assertIn("example.doc.v1", librarian["registry"])
            self.assertIn("example.style-card.v1", librarian["registry"])
            self.assertEqual(librarian["registry"]["example.doc.v1"]["id"], "example.doc.v1")
            style_entry = librarian["registry"]["example.style-card.v1"]
            self.assertEqual(style_entry["tags"][:3], ["style", "card", "markdown"])
            self.assertEqual(style_entry["type"]["logical"]["format"], "md")


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
