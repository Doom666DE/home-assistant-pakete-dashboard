import ast
import asyncio
import importlib
import pathlib
import sys
import types
import unittest
from datetime import date
from enum import StrEnum
from zoneinfo import ZoneInfo

base = pathlib.Path(__file__).resolve().parents[1] / 'upstream-snapshots'
for name in ['homeassistant','homeassistant.const','homeassistant.config_entries']:
    sys.modules[name] = types.ModuleType(name)
class Platform(StrEnum):
    BUTTON='button'
    CALENDAR='calendar'
    SENSOR='sensor'
sys.modules['homeassistant.const'].Platform=Platform
sys.modules['homeassistant.config_entries'].ConfigEntry=object
for name, folder in [('amazon_orders',base/'amazon_orders'),('amazon_orders.account',base/'amazon_orders/account')]:
    p=types.ModuleType(name); p.__path__=[str(folder)]; sys.modules[name]=p
pages=importlib.import_module('amazon_orders.account.pages')
parcels=importlib.import_module('amazon_orders.account.parcels')
# Extract the orchestration method so these tests cannot make HTTP/auth requests.
tree=ast.parse((base/'amazon_orders/account/client.py').read_text(encoding='utf-8'))
method=next(n for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='AmazonClient' for n in c.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_read_shipment')
ns={**vars(pages),'__builtins__':__builtins__}
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),method],type_ignores=[])),'client_method','exec'),ns)
class OfflineClient:
    _read_shipment=ns['_read_shipment']
    def __init__(self,*args): self._domain='amazon.de'
DAY=date(2026,10,22)
# Entirely invented fixture: no customer account/page content is included.
HTML='<script id="page-state">{"trackingId":"DE0000000000","timezone":"Europe/Berlin","promise":{"promiseMessage":"Zustellung: Samstag"},"progressTracker":{"lastReachedMilestone":"SHIPPED"}}</script>'
ORDER_HTML='<a class="item-card__link" href="/progress-tracker/package?orderId=000-0000000-0000000&amp;shipmentId=TEST&amp;packageIndex=0" aria-label="Testartikel, Bestellung aufgegeben 21. Oktober 2026, Zustellung: Samstag">Test</a>'
TILE=pages.parse_order_tiles(ORDER_HTML,DAY)[0]


class ModernTrackingTests(unittest.TestCase):
    def test_direct_page(self):
        calls=[]
        c=OfflineClient()
        async def fetch(path): calls.append(path); return HTML
        c._fetch_page=fetch
        raw=asyncio.run(c._read_shipment([TILE],DAY))
        p=parcels.normalize_parcel(raw)
        self.assertEqual(calls,[TILE.pop_path])
        self.assertEqual(p['barcode'],'DE0000000000')
        self.assertEqual(p['status'],'in_transit')
        self.assertEqual(p['planned_from'],'2026-10-24T00:00:00+02:00')
        self.assertIsNone(p['planned_to'])
        self.assertEqual(TILE.placed_on,date(2026,10,21))
        self.assertEqual(TILE.status_text,'Zustellung: Samstag')

    def test_legacy_indirect_page(self):
        from dataclasses import replace
        tile=replace(TILE,pop_path='/your-orders/pop?orderId=test')
        calls=[]
        c=OfflineClient()
        async def fetch(path):
            calls.append(path)
            return '<a href="/gp/your-account/ship-track?shipmentId=test">Tracking</a>' if len(calls)==1 else HTML
        c._fetch_page=fetch
        raw=asyncio.run(c._read_shipment([tile],DAY))
        self.assertEqual(len(calls),2)
        self.assertEqual(raw['tracking_id'],'DE0000000000')

    def test_link_variants(self):
        self.assertEqual(pages.parse_track_link("<a href='/progress-tracker/package?orderId=test&amp;packageIndex=0'>x</a>"),'/progress-tracker/package?orderId=test&packageIndex=0')
        self.assertFalse(pages.is_tracking_path('/your-orders/pop?orderId=test'))

    def test_dates_and_ranges(self):
        def promise(s,day=DAY): return pages._promise_delivery({'promise':{'promiseMessage':s}},day,ZoneInfo('Europe/Berlin'))
        self.assertEqual(promise('Zustellung: Samstag'),'2026-10-24T00:00:00+02:00')
        self.assertEqual(promise('Zustellung: Morgen'),'2026-10-23T00:00:00+02:00')
        self.assertEqual(promise('Zustellung: 24. Oktober'),'2026-10-24T00:00:00+02:00')
        self.assertEqual(promise('Arriving Monday',date(2026,10,25)),'2026-10-26T00:00:00+01:00')
        for text in ['Zustellung: 24.-26. Oktober','Zustellung: Freitag bis Samstag','Delivery unavailable','Zustellung: unbekannt']:
            self.assertIsNone(promise(text),text)

    def test_newer_event_takes_precedence(self):
        raw={'milestone':'SHIPPED','events':[{'timestamp':'2026-10-24T08:00:00+02:00','message':'Sendung wird zugestellt.'}]}
        self.assertEqual(parcels.resolve_status(raw),'out_for_delivery')
        raw['milestone']='DELIVERED'
        self.assertEqual(parcels.resolve_status(raw),'delivered')

if __name__=='__main__': unittest.main()
