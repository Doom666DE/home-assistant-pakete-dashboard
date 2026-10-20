"""Exercise the real shared Jinja macros with synthetic parcel sensor data."""
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from jinja2 import Environment

TZ = ZoneInfo('Europe/Berlin')
def as_datetime(value, default=None):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return default

def as_local(value):
    return value.replace(tzinfo=TZ) if value.tzinfo is None else value.astimezone(TZ)

def as_timestamp(value, default=0):
    parsed = as_datetime(value)
    return as_local(parsed).timestamp() if parsed else default

def strptime(value, fmt, default=None):
    try:
        return datetime.strptime(value, fmt)
    except (TypeError, ValueError):
        return default

def parcel(**overrides):
    data = dict(carrier='DPD', barcode='01999999999991', sender='Beispielversand',
                receiver=None, status='delivered', raw_status='Paket zugestellt - 14.10.2026',
                delivered=True, delivered_at=None, planned_from=None, planned_to=None,
                pickup=False, pickup_point=None, url=None, raw={}, history=None)
    return dict(data, **overrides)

def macros(parcels, bucket='delivered_parcels'):
    env = Environment()
    env.filters.update(to_json=json.dumps, from_json=json.loads,
                       regex_findall=lambda value, pattern: re.findall(pattern, value),
                       as_local=as_local, as_datetime=as_datetime, as_timestamp=as_timestamp)
    env.globals.update(
        state_attr=lambda entity, attr: parcels if entity == 'sensor.parcel_aggregator_' + bucket and attr == 'parcels' else None,
        states=lambda entity: '0', as_datetime=as_datetime, as_timestamp=as_timestamp,
        strptime=strptime, now=lambda: datetime(2026, 10, 20, 12, tzinfo=TZ))
    return env.from_string(Path('custom_templates/pakete.jinja').read_text('utf8')).module

def normalized(item, bucket='delivered_parcels'):
    return json.loads(macros([item], bucket).pakete(bucket))[0]

assert normalized(parcel())['delivered_at'] == '2026-10-14T00:00:00'
assert normalized(parcel(carrier='dpd'))['delivered_at'] == '2026-10-14T00:00:00'
exact = '2026-10-14T12:57:00+02:00'
assert normalized(parcel(delivered_at=exact))['delivered_at'] == exact
for text in [None, '', 'Paket zugestellt', 'Paket zugestellt - 31.02.2026',
             'Paket vom 13.10.2026 zugestellt am 14.10.2026']:
    assert normalized(parcel(raw_status=text))['delivered_at'] is None
assert normalized(parcel(carrier='UPS'))['delivered_at'] is None
assert normalized(parcel(delivered=False))['delivered_at'] is None
assert normalized(parcel(delivered=False, status='in_transit'), 'incoming_parcels')['delivered_at'] is None
assert normalized(parcel(), 'outgoing_delivered_parcels')['delivered_at'] == '2026-10-14T00:00:00'

item = normalized(parcel())
assert macros([item]).zeit(item) == 'Mi, 14.10.'
older = parcel(carrier='DHL', barcode='00340000000000000000', sender='Aeltere Sendung',
               delivered_at='2026-10-10T10:37:00+02:00')
html = macros([older, parcel()]).zugestellt()
assert html.index('Beispielversand') < html.index('Aeltere Sendung')
assert 'Mi, 14.10.' in html
print('PASS: DPD text-date fallback, valid existing timestamp, invalid/ambiguous dates, carrier/bucket guards, rendered date and delivery sort order')
