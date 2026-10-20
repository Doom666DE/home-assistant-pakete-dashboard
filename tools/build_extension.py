from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parents[1]
out = root / 'www/pakete/dpd-helper.zip'
with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
    for p in sorted((root / 'browser-extension').glob('*')):
        if p.is_file(): archive.write(p, p.name)
print(out)
