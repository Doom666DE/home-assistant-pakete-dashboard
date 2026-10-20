function displayedBarcode() {
  const panel = document.getElementById('ContentPlaceHolder1_panDataprotection');
  const numbers = new Set((panel?.innerText || '').match(/\b\d{14}\b/g) || []);
  return numbers.size === 1 ? [...numbers][0] : null;
}
async function currentPicture(barcode) {
  if (location.pathname.toLowerCase() !== '/myparcels/dataprotection.aspx' || displayedBarcode() !== barcode)
    throw new Error('Die DPD-Seite gehört nicht zur ausgewählten Paketnummer.');
  const image = document.getElementById('ContentPlaceHolder1_imgCaptcha');
  const input = document.getElementById('ContentPlaceHolder1_txtCaptchaCode');
  if (!image?.complete || image.naturalWidth < 30 || !input || !image.getClientRects().length)
    throw new Error('Kein vollständig geladenes CAPTCHA vorhanden.');
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
  canvas.getContext('2d').drawImage(image, 0, 0);
  const picture = canvas.toDataURL('image/png');
  const bytes = Uint8Array.from(atob(picture.split(',')[1]), char => char.charCodeAt(0));
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b => b.toString(16).padStart(2, '0')).join('');
  return {ok: true, image: picture, digest, barcode, url: location.href};
}
function setInput(element, value) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(element, value);
  element.dispatchEvent(new Event('input', {bubbles: true}));
  element.dispatchEvent(new Event('change', {bubbles: true}));
}
function inspect(barcode) {
  if (document.getElementById('ContentPlaceHolder1_panCaptchaCode')?.getClientRects().length)
    return {ok: true, verified: false, error: 'DPD zeigt weiterhin die Prüfung. Bitte neue Vorschau holen oder manuell bearbeiten.'};
  if (!document.getElementById('ContentPlaceHolder1_panWithAuthorization')?.getClientRects().length)
    return {ok: true, verified: false, error: 'DPD-Detailansicht noch nicht freigegeben.'};
  const share = document.getElementById('ContentPlaceHolder1_btnLink');
  const hidden = document.getElementById('ContentPlaceHolder1_hidParcelNo');
  const numbers = new Set([...(decodeURIComponent(share?.getAttribute('href') || '').matchAll(/[?&]pno=(\d{14})(?!\d)/g))].map(x => x[1]));
  if (/^\d{14}$/.test(hidden?.value || '')) numbers.add(hidden.value);
  if (numbers.size !== 1 || !numbers.has(barcode)) return {ok: true, verified: false,
    error: 'Die Detailansicht ist noch nicht eindeutig bestätigt. Bitte den DPD-Tab prüfen.'};
  const senderElement = document.getElementById('ContentPlaceHolder1_labDeliveryDetailsFromAddress');
  const firstLine = senderElement?.innerText?.split('\n').map(x => x.trim()).find(Boolean);
  const sender = firstLine && firstLine.length >= 2 && firstLine.length <= 150 && !['Deutschland', 'Germany'].includes(firstLine) ? firstLine : '';
  return {ok: true, verified: true, barcode, sender};
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message?.channel !== 'DPD_ASSIST_V1' || sender.id !== chrome.runtime.id) return;
  (async () => {
    const data = message.data || {};
    if (!/^\d{14}$/.test(data.barcode || '')) throw new Error('Ungültige Paketnummer');
    if (message.action === 'prepare_page') {
      if (location.pathname.toLowerCase() === '/myparcels/dataprotection.aspx') {
        if (displayedBarcode() !== data.barcode) throw new Error('Die Prüfseite gehört zu einem anderen Paket.');
        const image = document.getElementById('ContentPlaceHolder1_imgCaptcha');
        return {ok: true, ready: Boolean(image?.complete && image.naturalWidth >= 30)};
      }
      const details = inspect(data.barcode);
      if (details.verified) return {...details, ready: false};
      const panel = document.getElementById('ContentPlaceHolder1_panParcelList');
      const numbers = new Set((panel?.innerText || '').match(/\b\d{14}\b/g) || []);
      if (numbers.size !== 1 || !numbers.has(data.barcode)) return {ok: true, ready: false};
      const postcode = document.getElementById('ContentPlaceHolder1_txtPostcode');
      const submit = document.getElementById('ContentPlaceHolder1_btnAuthorizeParcel');
      const form = submit?.closest('form');
      const target = document.getElementById('__EVENTTARGET');
      const argument = document.getElementById('__EVENTARGUMENT');
      if (!/^\d{5}$/.test(data.postcode || '') || !postcode || !form || !target || !argument ||
          postcode.form !== form || target.form !== form || argument.form !== form ||
          submit.getAttribute('href') !== "javascript:__doPostBack('ctl00$ContentPlaceHolder1$btnAuthorizeParcel','')" ||
          new URL(form.action, location.href).origin !== 'https://my.dpd.de' || form.method.toLowerCase() !== 'post')
        throw new Error('DPD-PLZ-Formular hat sich geändert. Bitte DPD-Tab prüfen.');
      if (postcode.dataset.dpdAssistSubmitted) return {ok: true, ready: false};
      postcode.dataset.dpdAssistSubmitted = 'true';
      setInput(postcode, data.postcode);setInput(target, 'ctl00$ContentPlaceHolder1$btnAuthorizeParcel');setInput(argument, '');
      setTimeout(() => HTMLFormElement.prototype.submit.call(form), 80);
      return {ok: true, ready: false};
    }
    if (message.action === 'capture') return await currentPicture(data.barcode);
    if (message.action === 'inspect') return inspect(data.barcode);
    if (message.action !== 'apply') throw new Error('Unbekannte Anfrage');
    const current = await currentPicture(data.barcode);
    if (current.digest !== data.digest) throw new Error('Das CAPTCHA hat sich geändert. Bitte neue Vorschau holen.');
    if (!/^[A-Za-z0-9]{4,6}$/.test(data.code || '') || !/^\d{5}$/.test(data.postcode || '')) throw new Error('Ungültiger Code oder PLZ');
    const postcode = document.getElementById('ContentPlaceHolder1_txtDataprotectionZipCode');
    const input = document.getElementById('ContentPlaceHolder1_txtCaptchaCode');
    const submit = document.getElementById('ContentPlaceHolder1_btnSendZipCode');
    if (!postcode || !input || !submit || (postcode.value && postcode.value !== data.postcode))
      throw new Error('DPD-Eingabefelder oder PLZ haben sich geändert. Bitte den Tab prüfen.');
    // ASP.NET's javascript: link cannot reliably execute from an isolated
    // extension world. Submit its existing form with the exact event target.
    const form = submit.closest('form');
    const target = document.getElementById('__EVENTTARGET');
    const argument = document.getElementById('__EVENTARGUMENT');
    const href = submit.getAttribute('href');
    if (!form || postcode.form !== form || input.form !== form || !target || !argument ||
        target.form !== form || argument.form !== form ||
        href !== "javascript:__doPostBack('ctl00$ContentPlaceHolder1$btnSendZipCode','')" ||
        new URL(form.action, location.href).origin !== 'https://my.dpd.de' ||
        form.method.toLowerCase() !== 'post')
      throw new Error('Das DPD-Bestätigungsformular hat sich geändert. Bitte manuell bestätigen.');
    setInput(postcode, data.postcode); setInput(input, data.code);
    setInput(target, 'ctl00$ContentPlaceHolder1$btnSendZipCode'); setInput(argument, '');
    // Send acknowledgment before the ASP.NET navigation destroys this content script.
    setTimeout(() => HTMLFormElement.prototype.submit.call(form), 80);
    return {ok: true, submitted: true};
  })().then(respond).catch(err => respond({ok: false, error: err.message}));
  return true;
});
