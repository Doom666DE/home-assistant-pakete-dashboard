class DpdAssistCard extends HTMLElement {
  setConfig(config) {
    this.config = {postcode: '00000', ...config};
    if (!/^\d{5}$/.test(this.config.postcode)) throw new Error('Gültige PLZ erforderlich');
    if (!this.shadowRoot) this.attachShadow({mode: 'open'});
    this.pending = new Map(); this.busy = false; this.extensionReady = false;
    this.shadowRoot.innerHTML = `<style>
      ha-card{padding:16px;background:linear-gradient(135deg,rgba(220,0,90,.14),var(--ha-card-background,var(--card-background-color)));}
      .heading{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:650}ha-icon{color:#ff0063}.badge{margin-left:auto;font-size:11px;color:var(--secondary-text-color)}
      p{font-size:12px;line-height:1.5;color:var(--secondary-text-color);margin:10px 0}.actions{display:flex;flex-wrap:wrap;gap:8px}button,select{font:inherit;min-height:42px;border-radius:12px;border:1px solid var(--divider-color);padding:8px 12px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer}
      select{width:100%;margin:10px 0;font-size:12px}button:disabled{opacity:.45;cursor:default}.primary{background:#df0059;color:white;border-color:transparent;flex:1}.preview{display:none;padding:10px;border:1px solid var(--divider-color);border-radius:12px;margin:12px 0;background:var(--secondary-background-color)}
      img{display:block;background:white;border-radius:6px;max-width:100%;width:300px;image-rendering:auto;margin:0 auto 8px}.status{font-size:12px;line-height:1.45;min-height:18px;margin-top:10px}.warning{color:var(--warning-color,#ffca28)}.confirm{font-size:12px;line-height:1.45;margin:8px 0}.setup{font-size:12px;color:var(--primary-color)}
      </style><ha-card><div class="heading"><ha-icon icon="mdi:shield-check-outline"></ha-icon>DPD Browser-Hilfe<span class="badge">Verbinde …</span></div>
      <p>Alle aktualisieren holt nach 1,5 Sekunden die aktuelle CAPTCHA-Vorschau. DPD muss auf der Prüfseite geöffnet sein. Der Helfer übernimmt deine PLZ ${this.config.postcode}.</p><select aria-label="DPD-Paket auswählen"></select>
      <div class="actions"><button class="open">DPD öffnen</button><button class="capture">Vorschau holen</button><button class="check" title="Browser-Verbindung erneut prüfen">↻</button></div>
      <div class="preview"><img alt="Aktuelles DPD-CAPTCHA"><div class="confirm">Mit dem nächsten Klick wird <b>dieses Bild</b> an deine OpenAI-KI gesendet. Der Helfer trägt das Ergebnis und deine PLZ bei DPD ein und bestätigt einmal.</div><button class="primary solve">Dieses CAPTCHA bearbeiten</button></div>
      <div class="status" role="status" aria-live="polite"></div><a class="setup" href="/local/pakete/dpd-helper.zip" download>Browser-Helfer herunterladen</a></ha-card>`;
    this.$ = selector => this.shadowRoot.querySelector(selector);
    this.$('.open').onclick = () => {const barcode = this.barcode(); if (barcode) window.open('https://tracking.dpd.de/status/de_DE/parcel/' + barcode, '_blank', 'noopener');};
    this.$('.capture').onclick = () => this.capture();
    this.$('.solve').onclick = () => this.solve();
    this.$('.check').onclick = () => this.check();
    this.$('select').onchange = () => this.clearPreview();
    this.listener = event => {
      const m = event.data;
      if (event.source !== window || event.origin !== location.origin || m?.channel !== 'DPD_ASSIST_V1' || m.direction !== 'response') return;
      const callback = this.pending.get(m.requestId);
      if (callback) {this.pending.delete(m.requestId); callback(m.result);}
    };
    this.refreshListener = event => {
      const card = event.composedPath().find(node => node.tagName === 'MUSHROOM-TEMPLATE-CARD');
      if (card?.shadowRoot?.querySelector('[slot="primary"]')?.textContent.trim() !== 'Alle aktualisieren') return;
      if (this.busy || this.refreshTimer || !this.extensionReady || !this.barcode()) return;
      this.notify('Pakete werden aktualisiert. DPD-Vorschau wird gleich geholt …');
      this.refreshTimer = setTimeout(() => {
        this.refreshTimer = null;
        if (this.isConnected && !this.busy) {
          this._hass.callService('script', 'dpd_captcha_vorschau_holen').catch(err => this.notify('Vorschau-Skript konnte nicht gestartet werden: ' + err.message, true));
        }
      }, 1500);
    };
    this.updateButtons();
  }
  connectedCallback() {
    if (this.listener) window.addEventListener('message', this.listener);
    if (this.refreshListener) window.addEventListener('click', this.refreshListener, true);
    this.check();
    this.subscribePreview();
  }
  disconnectedCallback() {window.removeEventListener('message', this.listener);window.removeEventListener('click', this.refreshListener, true);clearTimeout(this.refreshTimer);this.refreshTimer = null;clearTimeout(this.expiryTimer);this.unsubscribePreview?.();this.unsubscribePreview = null;this.subscriptionGeneration = (this.subscriptionGeneration || 0) + 1;}
  async subscribePreview() {
    if (!this._hass || !this.isConnected || this.unsubscribePreview || this.subscribingPreview) return;
    this.subscribingPreview = true;
    const generation = this.subscriptionGeneration || 0;
    try {
      const unsubscribeCapture = await this._hass.connection.subscribeEvents(() => {
        if (this.isConnected && this.extensionReady && this.barcode() && !this.busy) this.openAndCapture();
      }, 'dpd_assist_preview_requested');
      let unsubscribeSolve;
      try {
        unsubscribeSolve = await this._hass.connection.subscribeEvents(() => {
          if (!this.isConnected || this.busy) return;
          const selected = this.preview;
          if (!selected || selected.expires <= Date.now()) {
            this.notify('Bitte zuerst eine aktuelle CAPTCHA-Vorschau holen.', true);return;
          }
          if (window.confirm(`Dieses angezeigte CAPTCHA für Paket ${selected.barcode} jetzt von deiner OpenAI-KI lesen lassen und mit PLZ ${this.config.postcode} einmal bei DPD bestätigen?`)) {
            if (this.preview === selected && selected.expires > Date.now()) this.solve();
            else this.notify('Vorschau inzwischen abgelaufen. Bitte neu holen.', true);
          }
        }, 'dpd_assist_solve_requested');
      } catch(err) {unsubscribeCapture();throw err;}
      const unsubscribe = () => {unsubscribeCapture();unsubscribeSolve();};
      if (!this.isConnected || generation !== (this.subscriptionGeneration || 0)) unsubscribe();
      else this.unsubscribePreview = unsubscribe;
    } catch {this.notify('Vorschau-Skript konnte nicht verbunden werden. Dashboard neu laden.', true);}
    finally {this.subscribingPreview = false;}
  }
  set hass(hass) {
    this._hass = hass;
    this.subscribePreview();
    if (!this.shadowRoot) return;
    const parcels = hass.states['sensor.dpd_germany_eingehende_pakete']?.attributes?.parcels || [];
    const ids = [...new Set(parcels.map(p => String(p.barcode || '')).filter(x => /^\d{14}$/.test(x)))];
    const signature = ids.join(',');
    if (signature !== this.parcelSignature) {
      const selected = this.$('select').value;
      this.$('select').replaceChildren();
      for (const barcode of ids) {const option = document.createElement('option'); option.value = barcode; option.textContent = barcode; this.$('select').append(option);}
      if (!ids.length) {const option = document.createElement('option');option.textContent = 'Keine eingehenden DPD-Pakete'; option.value = '';this.$('select').append(option);}
      if (ids.includes(selected)) this.$('select').value = selected;
      if (this.preview && this.preview.barcode !== this.barcode()) this.clearPreview();
      this.parcelSignature = signature;
      if (!ids.length) this.notify('Keine eingehenden DPD-Pakete vorhanden. Vorschau wird übersprungen.');
    }
    this.updateButtons();
    if (this.isConnected && !this.startedCheck) this.check();
  }
  barcode() {return this.$('select').value;}
  notify(message, error = false) {this.$('.status').textContent = message;this.$('.status').classList.toggle('warning', error);}
  updateButtons() {
    const available = Boolean(this.barcode());
    this.$('.open').disabled = this.busy || !available;
    this.$('.capture').disabled = this.busy || !available || !this.extensionReady;
    this.$('.solve').disabled = this.busy || !this.preview || this.preview.expires <= Date.now();
    this.$('select').disabled = this.busy;
    this.$('.check').disabled = this.busy;
  }
  request(action, data = {}) {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
      const timer = setTimeout(() => {this.pending.delete(requestId);reject(new Error('Browser-Helfer antwortet nicht. Erweiterung laden und Dashboard/DPD-Seite neu laden.'));}, 12000);
      this.pending.set(requestId, result => {clearTimeout(timer);if (result?.ok) resolve(result);else reject(new Error(result?.error || 'Browser-Helfer meldet einen Fehler'));});
      window.postMessage({channel: 'DPD_ASSIST_V1', direction: 'request', requestId, action, data}, location.origin);
    });
  }
  async check() {
    if (!this.shadowRoot || !this.isConnected) return;
    if (!this._hass) return;
    this.startedCheck = true;
    try {
      const status = await this._hass.callWS({type: 'dpd_assist/status'});
      if (!status.ready) throw new Error('Deine HA-KI ist gerade nicht verfügbar.');
    } catch(err) {
      this.extensionReady = false;this.$('.badge').textContent = 'HA prüfen';
      this.notify('HA-Verbindung fehlt: ' + (err.message || 'Integration noch nicht geladen'), true);
      this.updateButtons();return;
    }
    try {await this.request('ping'); this.extensionReady = true;this.$('.badge').textContent = 'Verbunden';this.notify('Browser-Helfer verbunden.');}
    catch {this.extensionReady = false;this.$('.badge').textContent = 'HA bereit · Helfer fehlt';this.notify('Browser-Erweiterung einmal installieren, dann diese Seite neu laden.', true);}
    this.updateButtons();
  }
  clearPreview() {clearTimeout(this.expiryTimer);this.preview = null;this.$('.preview').style.display = 'none';this.$('img').removeAttribute('src');this.updateButtons();}
  async openAndCapture() {
    if (this.busy || !this.barcode() || !this.extensionReady) return;
    const barcode = this.barcode();
    this.clearPreview();this.busy = true;this.updateButtons();this.notify('DPD wird geöffnet und PLZ übergeben …');
    try {
      const opened = await this.request('open', {barcode});
      await new Promise(resolve => setTimeout(resolve, 1500));
      for (let attempt = 0; attempt < 20; attempt++) {
        if (!this.isConnected) return;
        const page = await this.request('prepare_page', {tabId: opened.tabId, barcode, postcode: this.config.postcode});
        if (page.verified) {
          if (!page.sender) throw new Error('Detailansicht geöffnet, aber Absender noch nicht verfügbar. Tab bleibt offen.');
          await this._hass.callWS({type: 'dpd_assist/record_sender', barcode, sender: page.sender});
          this.notify('Daten gespeichert. DPD-Tab schließt in 5 Sekunden …');
          await new Promise(resolve => setTimeout(resolve, 5000));
          await this.request('close', {tabId: opened.tabId, barcode});
          this.notify('Daten gespeichert. DPD-Tab geschlossen.');
          return;
        }
        if (page.ready) {this.busy = false;await this.capture();return;}
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      throw new Error('DPD-Prüfseite noch nicht bereit. Bitte den DPD-Tab prüfen und Vorschau holen.');
    } catch(err) {this.notify(err.message, true);}
    finally {this.busy = false;this.updateButtons();}
  }
  async capture() {
    if (this.busy) return;
    this.clearPreview();this.busy = true;this.updateButtons();this.notify('Aktuelles DPD-Bild wird geholt …');
    try {
      const picture = await this.request('capture', {barcode: this.barcode()});
      if (picture.barcode !== this.barcode() || !picture.image?.startsWith('data:image/png;base64,')) throw new Error('Ungültige Bildantwort');
      const prepared = await this._hass.callWS({type: 'dpd_assist/prepare', image: picture.image, barcode: picture.barcode, url: picture.url});
      if (prepared.digest !== picture.digest) throw new Error('Bildprüfsumme stimmt nicht überein');
      this.preview = {...picture, ...prepared, expires: Date.now() + prepared.expires_in * 1000};
      this.$('img').src = picture.image;this.$('.preview').style.display = 'block';
      this.notify('Vorschau bereit. Bearbeitung gilt einmal für dieses Bild.');
      this.expiryTimer = setTimeout(() => {if (!this.busy) {this.clearPreview();this.notify('Vorschau abgelaufen. Bitte neu holen.', true);}}, prepared.expires_in * 1000);
    } catch(err) {this.notify(err.message, true);}
    finally {this.busy = false;this.updateButtons();}
  }
  async solve() {
    const selected = this.preview;
    if (this.busy || !selected || selected.expires <= Date.now()) return;
    this.busy = true;this.updateButtons();this.notify('Deine HA-KI liest dieses Bild …');
    try {
      const answer = await this._hass.callWS({type: 'dpd_assist/solve', challenge_id: selected.challenge_id});
      if (answer.digest !== selected.digest || answer.barcode !== selected.barcode) throw new Error('Die Aufgabe hat sich geändert');
      this.notify('Ergebnis wird einmal bei DPD eingetragen …');
      const applied = await this.request('apply', {captureId: selected.captureId, barcode: selected.barcode,
        digest: selected.digest, code: answer.code, postcode: this.config.postcode});
      this.clearPreview();this.notify('Bei DPD eingetragen. Detailansicht wird geprüft …');
      let details;
      for (let attempt = 0; attempt < 15; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        try {
          details = await this.request('inspect', {tabId: applied.tabId, barcode: selected.barcode});
          if (details.verified && details.sender) break;
        } catch (err) {
          if (attempt === 14) throw err;
        }
      }
      if (!details.verified) throw new Error(details.error || 'Bitte DPD-Tab prüfen');
      if (details.sender) await this._hass.callWS({type: 'dpd_assist/record_sender', barcode: selected.barcode, sender: details.sender});
      this.notify(details.sender ? `DPD-Detailansicht bestätigt. Absender „${details.sender}“ gespeichert.` : 'DPD-Detailansicht bestätigt.');
      if (details.sender) {
        await new Promise(resolve => setTimeout(resolve, 5000));
        try {
          await this.request('close', {tabId: applied.tabId, barcode: selected.barcode});
          this.notify('Daten gespeichert. DPD-Tab geschlossen.');
        } catch (err) {
          this.notify('Daten gespeichert. Tab bleibt offen: ' + err.message, true);
        }
      }
    } catch(err) {this.clearPreview();this.notify(err.message, true);}
    finally {this.busy = false;this.updateButtons();}
  }
  getCardSize() {return 4;}
  getGridOptions() {return {columns: 12, rows: 'auto'};}
}
if (!customElements.get('dpd-assist-card')) customElements.define('dpd-assist-card', DpdAssistCard);
window.customCards = window.customCards || [];
window.customCards.push({type: 'dpd-assist-card', name: 'DPD Browser-Hilfe', description: 'Aktuelle DPD-Prüfung mit einzeln angeforderter Bildhilfe'});
