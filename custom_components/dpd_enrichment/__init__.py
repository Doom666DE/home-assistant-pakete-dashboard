"""Local enrichment of DPD data, independent of HACS carrier updates."""
from datetime import timedelta
import asyncio
import time
import aiohttp
import voluptuous as vol
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.exceptions import HomeAssistantError
from .parser import CODE, RECORD_CODE, mail_candidate, mail_details, website_sender

DOMAIN = 'dpd_enrichment'
CONFIG_SCHEMA = vol.Schema({vol.Optional(DOMAIN): vol.Schema({vol.Required('mail_username'): cv.string})}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    manager = Enrichment(hass, config[DOMAIN]['mail_username'])
    await manager.load()
    hass.data[DOMAIN] = manager
    await discovery.async_load_platform(hass, 'sensor', DOMAIN, {}, config)

    async def record(call):
        await manager.record(call.data['barcode'], call.data['sender'], call.data['source'])

    async def refresh(call):
        await manager.refresh()

    hass.services.async_register(DOMAIN, 'record', record, schema=vol.Schema({
        vol.Required('barcode'): vol.All(cv.string, vol.Match(RECORD_CODE)),
        vol.Required('sender'): vol.All(cv.string, vol.Length(min=2, max=150)),
        vol.Optional('source', default='manual'): vol.In(['manual', 'website']),
    }))
    hass.services.async_register(DOMAIN, 'refresh', refresh, schema=vol.Schema({}))
    hass.bus.async_listen('imap_content', manager.mail)
    async_track_time_interval(hass, manager.refresh, timedelta(minutes=45))
    async_track_state_change_event(hass, ['sensor.dpd_germany_eingehende_pakete'], manager.changed)
    async def started(event):
        await manager.refresh()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, started)
    return True

class Enrichment:
    def __init__(self, hass, username):
        self.hass = hass
        self.username = username
        self.store = Store(hass, 1, DOMAIN)
        self.records = {}
        self.checks = {}
        self.sensor = None
        self.lock = asyncio.Lock()

    async def load(self):
        data = await self.store.async_load() or {}
        self.records = data.get('records', {})
        self.checks = data.get('checks', {})

    async def save(self):
        cutoff = time.time() - 180 * 86400
        self.records = {k:v for k,v in self.records.items() if v.get('updated', 0) >= cutoff}
        self.checks = {k:v for k,v in self.checks.items() if v.get('checked', 0) >= cutoff}
        await self.store.async_save({'records': self.records, 'checks': self.checks})
        if self.sensor and self.sensor.hass is not None:
            self.sensor.async_write_ha_state()

    async def record(self, barcode, sender, source):
        sender = ' '.join(sender.split())
        if not RECORD_CODE.fullmatch(barcode) or not 2 <= len(sender) <= 150:
            raise HomeAssistantError('Ungültige DPD-Zusatzinformationen')
        old = self.records.get(barcode, {})
        # A mail must not overwrite an explicitly confirmed website/manual value.
        if source == 'mail' and old.get('source') in ('website', 'manual'):
            return
        self.records[barcode] = {'sender': sender, 'source': source, 'updated': time.time()}
        await self.save()

    async def mail(self, event):
        data = event.data
        if data.get('username') != self.username or not data.get('initial'):
            return
        subject = str(data.get('subject') or '')
        body = str(data.get('text') or '')
        sender = str(data.get('sender') or '')
        # Fetch candidate shipping mails locally, regardless of their merchant or subject.
        if not mail_candidate(subject, body, sender):
            return
        if data.get('entry_id') and data.get('uid') and self.hass.services.has_service('imap', 'fetch'):
            try:
                result = await self.hass.services.async_call('imap', 'fetch', {'entry': data['entry_id'], 'uid': data['uid']}, blocking=True, return_response=True)
                if isinstance(result, dict):
                    body = str(result.get('text') or body) + '\n' + str(result.get('html') or '')
            except (HomeAssistantError, TimeoutError):
                pass
        details = mail_details(subject, body, sender)
        if details:
            await self.record(**details)

    async def changed(self, event):
        await self.refresh()

    async def refresh(self, now=None):
        if self.lock.locked():
            return
        async with self.lock:
            state = self.hass.states.get('sensor.dpd_germany_eingehende_pakete')
            parcels = state.attributes.get('parcels', []) if state else []
            session = async_get_clientsession(self.hass)
            for parcel in parcels[:20]:
                barcode = str(parcel.get('barcode') or '')
                if not CODE.fullmatch(barcode) or parcel.get('sender') or self.records.get(barcode, {}).get('source') in ('website', 'manual'):
                    continue
                if time.time() - self.checks.get(barcode, {}).get('checked', 0) < 6 * 3600:
                    continue
                try:
                    # No browser cookies, account tokens, or CAPTCHA bypasses.
                    async with session.get('https://my.dpd.de/myParcel-tracking.aspx', params={'parcelno': barcode}, timeout=aiohttp.ClientTimeout(total=20)) as response:
                        if response.status != 200:
                            outcome = 'http_error'
                            name = None
                        else:
                            html = await response.text()
                            name, outcome = website_sender(html, barcode)
                except (aiohttp.ClientError, TimeoutError, UnicodeError):
                    name, outcome = None, 'connection_error'
                self.checks[barcode] = {'checked': time.time(), 'result': outcome}
                if name:
                    self.records[barcode] = {'sender': name, 'source': 'website', 'updated': time.time()}
            await self.save()
