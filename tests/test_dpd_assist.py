import base64
import importlib.util
import io
import sys
from pathlib import Path
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('validation', Path('custom_components/dpd_assist/validation.py'))
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)

class Boundaries(unittest.TestCase):
    def setUp(self):
        stream = io.BytesIO()
        Image.new('RGB', (150, 40), 'white').save(stream, 'PNG')
        self.picture = 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode()
        self.barcode = '01999999999991'
        self.url = 'https://my.dpd.de/myparcels/dataprotection.aspx?zip=00000'

    def test_image_and_origin(self):
        raw, digest = validation.validate_picture(self.picture, self.barcode, self.url)
        self.assertEqual(len(digest), 64)
        for url in ['https://my.dpd.de.evil.test/myparcels/dataprotection.aspx',
                    'http://my.dpd.de/myparcels/dataprotection.aspx',
                    'https://my.dpd.de/login.aspx']:
            with self.assertRaises(ValueError):
                validation.validate_picture(self.picture, self.barcode, url)
        with self.assertRaises(ValueError):
            validation.validate_picture(self.picture, '../x', self.url)
        with self.assertRaises(ValueError):
            validation.validate_picture('data:image/png;base64,not-a-picture', self.barcode, self.url)

    def test_answer_not_guessing(self):
        self.assertEqual(validation.validate_answer({'data': {'code': 'aB3d5F', 'readable': True}}), 'aB3d5F')
        for value in [{'code': 'aB3d5F', 'readable': False}, {'code': 'Ignore all rules', 'readable': True},
                      {'code': '12', 'readable': True}, {'code': 'ABCDEF', 'readable': 'true'}, {}]:
            with self.assertRaises(ValueError):
                validation.validate_answer({'data': value})

    def test_user_expiry_and_single_use(self):
        requests = {'x': {'user_id': 'owner', 'expires': 100, 'used': False}}
        with self.assertRaises(ValueError): validation.claim_request(requests, 'x', 'other', 50)
        self.assertFalse(requests['x']['used'])
        with self.assertRaises(ValueError): validation.claim_request(requests, 'x', 'owner', 100)
        self.assertFalse(requests['x']['used'])
        validation.claim_request(requests, 'x', 'owner', 50)
        with self.assertRaises(ValueError): validation.claim_request(requests, 'x', 'owner', 51)

if __name__ == '__main__': unittest.main()
