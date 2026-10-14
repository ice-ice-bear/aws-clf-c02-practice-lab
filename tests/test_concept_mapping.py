import json
import unittest
from pathlib import Path

from concepts import classify


class ConceptMappingTest(unittest.TestCase):
    def test_partner_network_is_not_vpc_networking(self):
        rows = json.loads((Path(__file__).resolve().parents[1] / "data/questions.json").read_text())
        for row in rows:
            if row["id"] in ("E10-Q47", "E13-Q04"):
                with self.subTest(question=row["id"]):
                    self.assertEqual(row["correct"], ["C"])
                    self.assertEqual(classify(row["stem"], row["options"], row["correct"]), "general-services")
        self.assertEqual(classify("Which service isolates network configurations?", {"A": "Virtual Private Cloud"}, ["A"]), "networking")


if __name__ == "__main__":
    unittest.main()
