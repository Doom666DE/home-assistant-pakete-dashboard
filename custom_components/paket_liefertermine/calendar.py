"""Calendar events from the parcel dashboard's date-only fallback."""

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

SOURCE = "sensor.paket_liefertermine_zusatz"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([ParcelPromiseCalendar()])


class ParcelPromiseCalendar(CalendarEntity):
    """Publish confirmed dates without inventing delivery times."""

    _attr_name = "Paket-Liefertermine Zusatz"
    _attr_unique_id = "paket_liefertermine_zusatz"
    _attr_should_poll = False

    async def async_added_to_hass(self):
        @callback
        def source_changed(event):
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(self.hass, SOURCE, source_changed)
        )

    def _events(self):
        source = self.hass.states.get(SOURCE)
        events = []
        for parcel in source.attributes.get("termine", []) if source else []:
            try:
                day = date.fromisoformat(parcel["planned_from"])
                last_day = date.fromisoformat(parcel.get("planned_to") or parcel["planned_from"])
            except (KeyError, TypeError, ValueError):
                continue
            code = parcel["barcode"]
            events.append(CalendarEvent(
                start=day,
                end=last_day + timedelta(days=1),
                summary=f"{parcel['carrier']}: {code}",
                uid=code,
            ))
        return events

    @property
    def event(self):
        today = dt_util.now().date()
        return min(
            (event for event in self._events() if event.end > today),
            key=lambda event: event.start,
            default=None,
        )

    async def async_get_events(self, hass, start_date, end_date):
        start = dt_util.as_local(start_date)
        end = dt_util.as_local(end_date)
        return [
            event for event in self._events()
            if datetime.combine(event.start, datetime.min.time(), start.tzinfo) < end
            and datetime.combine(event.end, datetime.min.time(), start.tzinfo) > start
        ]
