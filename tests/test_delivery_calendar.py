"""Offline checks for all-day promises and timed carrier delivery windows."""
import ast
import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo('Europe/Berlin')


def calendar_functions(domain, class_name):
    tree = ast.parse((ROOT/'upstream-snapshots'/domain/'calendar.py').read_text('utf-8'))
    nodes = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]
    nodes += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_event_time']
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    nodes += [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in {'_events','event','async_get_events'}]
    for node in nodes:
        if hasattr(node, 'decorator_list'):
            node.decorator_list = []
    parse = lambda x: datetime.fromisoformat(x) if x else None
    scope = dict(date=date, datetime=datetime, timedelta=timedelta,
                 CalendarEvent=lambda **kw: SimpleNamespace(**kw), parse_iso=parse, _parse=parse,
                 dt_util=SimpleNamespace(now=lambda: datetime(2026,10,22,17,tzinfo=ZONE)),
                 _DEFAULT_EVENT_DURATION=timedelta(hours=1))
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])), 'calendar_under_test', 'exec'), scope)
    return scope


class DeliveryCalendarTests(unittest.TestCase):
    def test_all_day_and_overlap(self):
        for domain, cls in [('amazon_orders','AmazonDeliveriesCalendar'),('parcel_aggregator','ParcelAggregatorCalendar')]:
            with self.subTest(domain=domain):
                scope=calendar_functions(domain,cls)
                parcel=dict(carrier='Amazon',barcode='TEST',planned_from='2026-10-24T00:00:00+02:00',planned_to=None)
                data=[parcel] if domain=='amazon_orders' else {'incoming':{'parcels':[parcel]}}
                obj=SimpleNamespace(coordinator=SimpleNamespace(data=data))
                obj._events=lambda:scope['_events'](obj)
                event=obj._events()[0]
                self.assertIs(type(event.start),date)
                self.assertEqual(event.end,date(2026,10,25))
                self.assertEqual(scope['event'](obj).start,date(2026,10,24))
                selected=asyncio.run(scope['async_get_events'](obj,None,datetime(2026,10,24,12,tzinfo=ZONE),datetime(2026,10,25,tzinfo=ZONE)))
                self.assertEqual(len(selected),1)
                excluded=asyncio.run(scope['async_get_events'](obj,None,datetime(2026,10,25,tzinfo=ZONE),datetime(2026,10,26,tzinfo=ZONE)))
                self.assertEqual(excluded,[])
                if domain=='parcel_aggregator':
                    parcel.update(carrier='UPS',planned_from='2026-10-26T13:45:00+01:00',planned_to='2026-10-26T16:45:00+01:00')
                    event=obj._events()[0]
                    self.assertEqual((event.start.hour,event.start.minute,event.end.hour,event.end.minute),(13,45,16,45))

    def test_dashboard_has_one_calendar_source(self):
        config=yaml.safe_load((ROOT/'dashboards/pakete.yaml').read_text('utf-8'))
        def cards(node):
            if isinstance(node,dict):
                if node.get('type')=='calendar': yield node
                for value in node.values(): yield from cards(value)
            elif isinstance(node,list):
                for value in node: yield from cards(value)
        calendars=list(cards(config))
        self.assertEqual(len(calendars),1)
        self.assertEqual(calendars[0]['entities'],['calendar.parcel_aggregator_deliveries'])

if __name__=='__main__':
    unittest.main()
