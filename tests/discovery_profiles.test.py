"""Guard exact co-artist matching against title mentions and ambiguous credits."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from discovery_profiles import extract_verified_credit_relationships

class CreditTests(unittest.TestCase):
    def edges(self, credit, title):
        return extract_verified_credit_relationships(
            [{'name':'Common'}, {'name':'Snow'}, {'name':'Alex Metcalf'}],
            {'source':'https://example.com/credits', 'tracks':[
                {'requestId':'1', 'artistCredit':credit, 'title':title}]})

    def test_complete_artist_tokens(self):
        edges = self.edges('Snow/Alex Metcalf', 'Legal')
        self.assertEqual(edges[0]['artists'], ['Alex Metcalf', 'Snow'])
        self.assertEqual(edges[0]['requestId'], '1')
        self.assertEqual(edges[0]['kind'], 'track-credit')

    def test_featured_credit(self):
        self.assertEqual(len(self.edges('Snow', 'Legal (feat. Alex Metcalf; Explicit)')), 1)

    def test_unknown_host_cannot_make_a_link(self):
        self.assertEqual(self.edges('Unknown', 'Legal (feat. Alex Metcalf)'), [])

    def test_title_mentions_are_not_credits(self):
        self.assertEqual(self.edges('Common', 'An uncommon Snow story'), [])

    def test_self_credit_cannot_make_a_link(self):
        self.assertEqual(self.edges('Snow', 'Legal (feat. Snow)'), [])

if __name__ == '__main__':
    unittest.main()
