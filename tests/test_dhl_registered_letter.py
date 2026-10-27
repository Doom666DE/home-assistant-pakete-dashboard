"""Offline regression tests for the DHL registered-letter delivery exception."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'upstream-snapshots/dhl/account/countries/de/__init__.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8'))
# Exercise the actual guarded exception without importing HA or transport code.
GUARDS = [n for n in ast.walk(TREE) if isinstance(n, ast.If)
          and 'derived_delivered' in ast.unparse(n.test)
          and 're.fullmatch' in ast.unparse(n.test)]
assert len(GUARDS) == 1, 'Registered-letter delivery exception missing or ambiguous'
CODE = compile(ast.Module(body=GUARDS, type_ignores=[]), str(SOURCE), 'exec')


def resolve(barcode='A0000000000000000000', completed=True,
            text='Die Sendung wurde am 09.10.2026 ausgeliefert.'):
    scope = dict(re=re, barcode=barcode, raw_status=text,
                 derived_delivered=completed, delivered=False, status='unknown',
                 ParcelStatus=SimpleNamespace(DELIVERED='delivered'))
    exec(CODE, scope)
    return scope['delivered'], scope['status']


class RegisteredLetterTests(unittest.TestCase):
    def test_completed_letter_overrides_false_delivery_flag(self):
        self.assertEqual(resolve(), (True, 'delivered'))

    def test_incomplete_ladder_does_not_override(self):
        self.assertEqual(resolve(completed=False), (False, 'unknown'))

    def test_other_barcode_family_does_not_override(self):
        self.assertEqual(resolve(barcode='00340000000000000000'), (False, 'unknown'))

    def test_unconfirmed_or_negated_message_does_not_override(self):
        for text in ['Die Sendung wurde noch nicht ausgeliefert.',
                     'Die Sendung wurde am 09.10.2026 ausgeliefert. Weitere Meldung',
                     'Die Sendung wurde angekündigt.']:
            with self.subTest(text=text):
                self.assertEqual(resolve(text=text), (False, 'unknown'))


if __name__ == '__main__':
    unittest.main()
