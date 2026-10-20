from homeassistant.components.sensor import SensorEntity
from . import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    manager = hass.data[DOMAIN]
    sensor = DpdDetails(manager)
    manager.sensor = sensor
    async_add_entities([sensor])

class DpdDetails(SensorEntity):
    _attr_name = 'DPD Zusatzinformationen'
    _attr_unique_id = 'dpd_enrichment_records'
    _attr_icon = 'mdi:package-variant-plus'
    _attr_should_poll = False

    def __init__(self, manager):
        self.manager = manager

    @property
    def native_value(self):
        return len(self.manager.records)

    @property
    def extra_state_attributes(self):
        return {'records': self.manager.records, 'website_checks': self.manager.checks}
