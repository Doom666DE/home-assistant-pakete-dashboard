"""Apply the tested local transport patch to an installed ha-ups 1.1.3.

Default is a dry run. This never edits .storage and never restarts HA.
"""
import argparse
import ast
import datetime
import json
from pathlib import Path
import shutil

API_SOURCE = Path(__file__).resolve().parents[1] / 'upstream-snapshots/ups/api.py'
REQUIREMENT = 'curl_cffi==0.16.3'
IMPORT = 'from .api import UPSApiClient, UPSApiError\n'
ANCHOR = '        # What came off disk decides whether this start polls at all, so it is'
MIGRATION = '''        # A new, verified transport gets one retry using the existing budget.
        # Preserve backoff on every later restart, including new transport failures.
        if stored.get("transport_version") != TRANSPORT_VERSION:
            self._consecutive_failures = 0
            self._standdown_until_utc = 0.0
            self.update_interval = timedelta(seconds=MIN_CYCLE_GAP_SECONDS)
            self._persist_cache()
            _LOGGER.info("UPS direct transport migrated to %s; request budget preserved", TRANSPORT_VERSION)
'''


def prepare(config):
    root = config / 'custom_components/ups'
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('domain') != 'ups' or manifest.get('version') != '1.1.3':
        raise ValueError('Only ha-ups 1.1.3 is verified; refusing to overwrite another version.')
    api = API_SOURCE.read_text(encoding='utf-8')
    coordinator = (root / 'coordinator.py').read_text(encoding='utf-8')
    if 'TRANSPORT_VERSION' not in coordinator:
        if coordinator.count(IMPORT) != 1 or coordinator.count(ANCHOR) != 1:
            raise ValueError('Coordinator differs from the tested version; no files changed.')
        cache_key = '                "last_fetch_utc": self._last_fetch_utc,'
        if coordinator.count(cache_key) != 1:
            raise ValueError('Cache writer differs from the tested version; no files changed.')
        coordinator = coordinator.replace(IMPORT, IMPORT.rstrip() + ', TRANSPORT_VERSION\n')
        coordinator = coordinator.replace(ANCHOR, MIGRATION + ANCHOR)
        coordinator = coordinator.replace(cache_key, '                "transport_version": TRANSPORT_VERSION,\n' + cache_key)
    elif MIGRATION.strip() not in coordinator or '"transport_version": TRANSPORT_VERSION' not in coordinator:
        raise ValueError('An unfamiliar transport patch is installed; refusing to overwrite it.')
    ast.parse(api)
    ast.parse(coordinator)
    manifest['requirements'] = [r for r in manifest.get('requirements', [])
                                if not r.lower().replace('-', '_').startswith('curl_cffi')]
    manifest['requirements'].append(REQUIREMENT)
    return root, {'api.py': api, 'coordinator.py': coordinator,
                  'manifest.json': json.dumps(manifest, indent=2, ensure_ascii=False) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True, help='HA config directory, e.g. /config')
    parser.add_argument('--apply', action='store_true', help='Back up and write the validated files')
    args = parser.parse_args()
    config = args.config.resolve()
    root, files = prepare(config)
    changed = {name: content for name, content in files.items()
               if (root / name).read_text(encoding='utf-8') != content}
    if not changed:
        print('UPS transport patch already installed; no changes.')
        return
    print('Validated ha-ups 1.1.3:', ', '.join(changed))
    if not args.apply:
        print('Dry run only. Add --apply to back up and install.')
        return
    backup = config / 'codex_backups' / ('ups-transport-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    for name in files:
        shutil.copy2(root / name, backup / name)
    try:
        for name, content in changed.items():
            (root / name).write_text(content, encoding='utf-8')
    except Exception:
        for name in files:
            shutil.copy2(backup / name, root / name)
        raise
    print('Installed. Backup:', backup)
    print('Restart Home Assistant to load the pinned dependency and new transport.')


if __name__ == '__main__':
    main()
