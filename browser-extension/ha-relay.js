// No HA token, browser cookie, or whole-page screenshot is read or forwarded.
window.addEventListener('message', async event => {
  const message = event.data;
  if (event.source !== window || event.origin !== location.origin || location.origin !== 'http://homeassistant.local:8123' ||
      message?.channel !== 'DPD_ASSIST_V1' || message.direction !== 'request' ||
      typeof message.requestId !== 'string' || !['ping', 'capture', 'apply', 'inspect', 'open', 'prepare_page', 'close'].includes(message.action)) return;
  try {
    const result = await chrome.runtime.sendMessage({channel: 'DPD_ASSIST_V1', action: message.action, data: message.data});
    window.postMessage({channel: 'DPD_ASSIST_V1', direction: 'response', requestId: message.requestId, result}, location.origin);
  } catch {
    window.postMessage({channel: 'DPD_ASSIST_V1', direction: 'response', requestId: message.requestId,
      result: {ok: false, error: 'Browser-Helfer ist nicht verbunden. Dashboard und DPD-Seite bitte neu laden.'}}, location.origin);
  }
});
