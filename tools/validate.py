"""Validate exported sources without importing Home Assistant or making requests."""
from pathlib import Path
import ast,json,yaml,re
from jinja2 import Environment
root=Path(__file__).resolve().parents[1]
class HALoader(yaml.SafeLoader): pass
HALoader.add_multi_constructor('!',lambda loader,tag,node: loader.construct_scalar(node))
counts={}
for p in root.rglob('*'):
    if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
    suffix=p.suffix.lower()
    if suffix=='.py':ast.parse(p.read_text('utf8'),filename=str(p))
    elif suffix=='.json':json.loads(p.read_text('utf8'))
    elif suffix in ['.yaml','.yml']:yaml.load(p.read_text('utf8'),Loader=HALoader)
    elif suffix=='.jinja':Environment().parse(p.read_text('utf8'))
    else:continue
    counts[suffix]=counts.get(suffix,0)+1
dashboard=yaml.safe_load((root/'dashboards/pakete.yaml').read_text('utf8'))
assert [v['path'] for v in dashboard['views']]==['pakete']
assert (root/'custom_components/dpd_enrichment/parser.py').exists()
assert 'dpd_assist_solve_requested' in (root/'packages/dpd_assist.yaml').read_text('utf8')
manifest=json.loads((root/'browser-extension/manifest.json').read_text('utf8'))
background=(root/'browser-extension/background.js').read_text('utf8')
assert 'http://homeassistant.local:8123/*' in manifest['host_permissions']
assert "'http://homeassistant.local:8123'" in background
print('PASS: source syntax, config parsing, parcel-only dashboard and browser origin consistency',counts)
