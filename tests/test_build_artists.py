"""Regression tests for artist names extracted from station credits."""

import unittest
from unittest.mock import patch

from build_artists import build_catalogue, split_artists


class ArtistCreditTests(unittest.TestCase):
    def test_verified_ampersand_band_remains_intact(self):
        self.assertEqual(split_artists("Mary & Adelaide"), ["Mary & Adelaide"])
        self.assertEqual(split_artists("mary & adelaide"), ["mary & adelaide"])

    def test_collaboration_splitting_still_works(self):
        self.assertEqual(split_artists("4Korners & Haviah Mighty"), ["4Korners", "Haviah Mighty"])
        self.assertEqual(split_artists("Artist A feat. Artist B"), ["Artist A", "Artist B"])

    def test_case_variants_merge_and_retain_tracks(self):
        rows = [
            {"song": {"artist": "4Korners", "title": "Ogwula", "album": "Ogwula"}, "id": "one"},
            {"song": {"artist": "4korners", "title": "Marathon", "album": "Marathon"}, "id": "two"},
            {"song": {"artist": "Mary & Adelaide", "title": "Hoodie zipper", "album": "Celebrate Another Day of Living"}, "id": "three"},
        ]
        with patch("build_artists.hidden_artists", return_value=set()):
            catalogue = build_catalogue(rows)
        self.assertEqual(list(catalogue), ["4Korners", "Mary & Adelaide"])
        self.assertEqual([t["title"] for t in catalogue["4Korners"]], ["Ogwula", "Marathon"])
        self.assertEqual(catalogue["Mary & Adelaide"][0]["request_id"], "three")

    def test_removals_still_apply_regardless_of_case(self):
        rows = [{"song": {"artist": "REMOVED", "title": "Demo", "album": "Demo"}, "id": "one"}]
        with patch("build_artists.hidden_artists", return_value={"removed"}):
            self.assertEqual(build_catalogue(rows), {})


if __name__ == "__main__":
    unittest.main()
