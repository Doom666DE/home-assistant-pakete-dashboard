"""Synthetic merchant-mail fixtures. No mailbox or live shipment access."""
import runpy
f=runpy.run_path('custom_components/dpd_enrichment/parser.py')['mail_details']
code='1Z999AA10123456784'
assert f('Order updated',f'<p>Your order has shipped</p><a href="https://www.ups.com/track?tracknum={code}">Track</a>','Beispielshop <sales@shop.example>') == {'barcode':code,'sender':'Beispielshop','source':'mail'}
assert f('Newsletter',code,'Shop <sales@shop.example>') is None
assert f('Shipped',code+' 1Z999AA10123456785','Shop <sales@shop.example>') is None
assert f('Shipped',code,'UPS <auto@ups.com>') is None
assert f('Shipped',code,'person@gmail.com') is None
assert f('Shipping update',f'UPS {code}','sales@shop.example')['sender']=='shop.example'
assert f('Versand GLS','Sendungsnummer: 123456789012','Mein Shop <mail@shop.example>')['barcode']=='123456789012'
assert f('DPD Versand','Sendungsnummer: 01999999999991','Mein Shop <mail@shop.example>')['sender']=='Mein Shop'
print('PASS: 8 synthetic merchant-mail extraction checks')
