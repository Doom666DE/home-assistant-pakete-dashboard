const captures = new Map();
let queue = Promise.resolve();
const persist = () => chrome.storage.session.set({captures: Object.fromEntries(captures)});
const send = (tabId, action, data = {}) => chrome.tabs.sendMessage(tabId, {channel: 'DPD_ASSIST_V1', action, data});
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message?.channel !== 'DPD_ASSIST_V1' || !sender.tab || new URL(sender.url).origin !== 'http://homeassistant.local:8123') return;
  const run = async () => {
    if (message.action === 'ping') return {ok: true, version: '1.0.0'};
    // MV3 workers can sleep while the HA model is answering. Keep short-lived
    // bindings in browser-session storage, not in durable disk settings.
    const stored = await chrome.storage.session.get('captures');
    captures.clear();
    for (const [key, value] of Object.entries(stored.captures || {})) {
      if (value.expires > Date.now()) captures.set(key, value);
    }
    const data = message.data || {};
    if (!/^\d{14}$/.test(data.barcode || '')) throw new Error('Bitte zuerst eine DPD-Paketnummer auswählen.');
    if (message.action === 'open') {
      const tabs = await chrome.tabs.query({url: 'https://my.dpd.de/*'});
      for (const tab of tabs) {
        try {
          const details = await send(tab.id, 'inspect', {barcode: data.barcode});
          if (details.verified) return {ok: true, tabId: tab.id};
          const existing = await send(tab.id, 'capture', {barcode: data.barcode});
          if (existing.ok) return {ok: true, tabId: tab.id};
        } catch {}
      }
      const tab = await chrome.tabs.create({url: 'https://tracking.dpd.de/status/de_DE/parcel/' + data.barcode, active: false});
      return {ok: true, tabId: tab.id};
    }
    if (message.action === 'prepare_page') {
      if (!Number.isInteger(data.tabId) || !/^\d{5}$/.test(data.postcode || '')) throw new Error('DPD-Tab oder PLZ fehlt.');
      const tab = await chrome.tabs.get(data.tabId);
      if (!tab.url || new URL(tab.url).hostname !== 'my.dpd.de') return {ok: true, ready: false};
      try {return await send(tab.id, 'prepare_page', data);}
      catch {return {ok: true, ready: false};}
    }
    if (message.action === 'capture') {
      const tabs = await chrome.tabs.query({url: 'https://my.dpd.de/*'});
      const matching = [];
      for (const tab of tabs) {
        try {
          const result = await send(tab.id, 'capture', {barcode: data.barcode});
          if (result.ok) matching.push({tab, result});
        } catch { /* A pre-install tab must be reloaded to get the content script. */ }
      }
      if (matching.length !== 1) throw new Error(matching.length ? 'Mehrere passende DPD-Tabs. Bitte nur einen geöffnet lassen.' :
        'Keine passende DPD-Prüfseite gefunden. DPD öffnen, PLZ eingeben und die Seite nach Installation einmal neu laden.');
      for (const [key, value] of captures) if (value.haTabId === sender.tab.id || value.expires <= Date.now()) captures.delete(key);
      const {tab, result} = matching[0];
      const captureId = crypto.randomUUID();
      captures.set(captureId, {tabId: tab.id, haTabId: sender.tab.id, barcode: data.barcode,
        digest: result.digest, expires: Date.now() + 120000});
      await persist();
      return {...result, captureId};
    }
    if (message.action === 'apply') {
      const saved = captures.get(data.captureId);
      if (!saved || saved.haTabId !== sender.tab.id || saved.barcode !== data.barcode || saved.digest !== data.digest || saved.expires <= Date.now())
        throw new Error('Diese Vorschau ist nicht mehr gültig. Bitte neu holen.');
      captures.delete(data.captureId); // No retry or second submission with the same image.
      await persist();
      const result = await send(saved.tabId, 'apply', {...data, digest: saved.digest});
      return {...result, tabId: saved.tabId};
    }
    if (message.action === 'close') {
      if (!Number.isInteger(data.tabId)) throw new Error('DPD-Tab fehlt.');
      const tab = await chrome.tabs.get(data.tabId);
      if (!tab.url || new URL(tab.url).hostname !== 'my.dpd.de') throw new Error('Der Tab ist keine DPD-Seite mehr.');
      const details = await send(tab.id, 'inspect', {barcode: data.barcode});
      if (!details.verified) throw new Error('Detailansicht nicht bestätigt.');
      await chrome.tabs.remove(tab.id);
      return {ok: true};
    }
    if (message.action === 'inspect') {
      if (!Number.isInteger(data.tabId)) throw new Error('DPD-Tab fehlt.');
      const tab = await chrome.tabs.get(data.tabId);
      if (new URL(tab.url).hostname !== 'my.dpd.de') throw new Error('Der Tab ist keine DPD-Seite mehr.');
      return await send(tab.id, 'inspect', data);
    }
    throw new Error('Unbekannte Anfrage');
  };
  const task = queue.then(run);
  queue = task.catch(() => {});
  task.then(respond).catch(err => respond({ok: false, error: err.message}));
  return true;
});
