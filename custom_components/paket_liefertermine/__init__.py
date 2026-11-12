"""Expose date-only parcel promises as a read-only calendar."""

from homeassistant.helpers import discovery


async def async_setup(hass, config):
    await discovery.async_load_platform(
        hass, "calendar", "paket_liefertermine", {}, config
    )
    return True
