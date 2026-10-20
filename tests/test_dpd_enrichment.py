from pathlib import Path
import importlib.util
import ast

spec = importlib.util.spec_from_file_location('dpd_parser', 'custom_components/dpd_enrichment/parser.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
fixture = Path('tests/fixtures/dpd-sender.html').read_text(encoding='utf8')
assert parser.website_sender(fixture, '01999999999991') == ('Beispielversand GmbH', 'website')
assert parser.website_sender(fixture, '01999999999992')[0] is None
assert parser.website_sender(fixture + '<input id="ContentPlaceHolder1_txtCaptchaCode">', '01999999999991')[1] == 'verification_required'
assert parser.website_sender('<p>Anmelden</p>', '01999999999991')[0] is None
assert parser.mail_details('Ihr Paket von Beispiel Shop', 'DPD Paketnummer: 01999999999991', 'DPD <info@dpd.de>')['sender'] == 'Beispiel Shop'
assert parser.mail_details('Ihr Paket von Beispielversand GmbH ist unterwegs', 'DPD Paketnummer: 01999999999991', 'DPD <info@dpd.de>')['sender'] == 'Beispielversand GmbH'
assert parser.mail_details('Versand', 'DPD https://my.dpd.de/myParcel-tracking.aspx?parcelno=01999999999991', 'Beispiel Shop <shop@example.com>')['sender'] == 'Beispiel Shop'
assert parser.mail_details('Versand', 'DPD Paketnummer: 01999999999991', 'DPD <info@dpd.de>') is None
assert parser.mail_details('Versand', 'DPD Paketnummer: 01999999999991\nPaketnummer: 01999999999992', 'Shop <shop@example.com>') is None
assert parser.mail_details('Rechnung', 'Nummer: 01999999999991', 'Shop <shop@example.com>') is None
for path in Path('custom_components/dpd_enrichment').glob('*.py'):
    ast.parse(path.read_text(encoding='utf8'))
print('PASS: real website HTML, barcode mismatch, CAPTCHA, login, explicit sender, merchant mail, carrier mail without sender, ambiguous codes, unrelated mail, syntax')
