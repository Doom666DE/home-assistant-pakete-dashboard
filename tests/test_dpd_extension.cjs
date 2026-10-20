// Offline fixture tests only. Does not connect to Chrome or a live DPD page.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
let handler, clicks = 0;
class Input {constructor(value = '') {this._value = value;} get value() {return this._value;} set value(v) {this._value = v;} dispatchEvent() {}}
const form = {action: 'https://my.dpd.de/myparcels/dataprotection.aspx?zip=00000', method: 'post'};
class Form {submit() {assert.equal(this, form); clicks++;}}
const elements = {
  ContentPlaceHolder1_panDataprotection: {innerText: 'Paketnummer 01999999999991 Datenschutz'},
  ContentPlaceHolder1_imgCaptcha: {complete: true, naturalWidth: 150, naturalHeight: 40, getClientRects: () => [1]},
  ContentPlaceHolder1_txtCaptchaCode: new Input(),
  ContentPlaceHolder1_txtDataprotectionZipCode: new Input('00000'),
  ContentPlaceHolder1_btnSendZipCode: {closest: () => form, getAttribute: () => "javascript:__doPostBack('ctl00$ContentPlaceHolder1$btnSendZipCode','')"},
  __EVENTTARGET: new Input(), __EVENTARGUMENT: new Input(),
  ContentPlaceHolder1_panCaptchaCode: {getClientRects: () => [1]},
};
for (const element of Object.values(elements)) if (element instanceof Input) element.form = form;
let png = 'data:image/png;base64,aGVsbG8=';
const context = vm.createContext({chrome: {runtime: {id: 'test', onMessage: {addListener: fn => {handler = fn;}}}},
  location: {pathname: '/myparcels/dataprotection.aspx', href: 'https://my.dpd.de/myparcels/dataprotection.aspx?zip=00000'},
  document: {getElementById: id => elements[id] || null, createElement: () => ({getContext: () => ({drawImage(){}}), toDataURL: () => png})},
  crypto: webcrypto, Uint8Array, Set, URL, Event: class {}, HTMLInputElement: Input, HTMLFormElement: Form, setTimeout: fn => fn(),
  atob: x => Buffer.from(x, 'base64').toString('binary')});
vm.runInContext(fs.readFileSync('browser-extension/dpd.js', 'utf8'), context);
const call = (action, data) => new Promise(resolve => handler({channel: 'DPD_ASSIST_V1', action, data}, {id: 'test'}, resolve));
(async () => {
  const barcode = '01999999999991';
  const capture = await call('capture', {barcode}); assert.equal(capture.ok, true);
  const wrongParcel = await call('capture', {barcode: '99999999999999'}); assert.equal(wrongParcel.ok, false);
  png = 'data:image/png;base64,d29ybGQ=';
  const stale = await call('apply', {...capture, code: 'abc123', postcode: '00000'}); assert.equal(stale.ok, false); assert.equal(clicks, 0);
  png = capture.image;
  elements.ContentPlaceHolder1_txtDataprotectionZipCode.value = '12345';
  const wrongPostcode = await call('apply', {...capture, code: 'abc123', postcode: '00000'}); assert.equal(wrongPostcode.ok, false); assert.equal(clicks, 0);
  elements.ContentPlaceHolder1_txtDataprotectionZipCode.value = '00000';
  form.action = 'https://example.com/';
  assert.equal((await call('apply', {...capture, code: 'abc123', postcode: '00000'})).ok, false); assert.equal(clicks, 0);
  form.action = 'https://my.dpd.de/myparcels/dataprotection.aspx?zip=00000';
  const good = await call('apply', {...capture, code: 'abc123', postcode: '00000'}); assert.equal(good.submitted, true); assert.equal(clicks, 1);
  assert.equal(elements.ContentPlaceHolder1_txtCaptchaCode.value, 'abc123');
  assert.equal(elements.__EVENTTARGET.value, 'ctl00$ContentPlaceHolder1$btnSendZipCode');
  assert.equal(elements.__EVENTARGUMENT.value, '');
  const unverified = await call('inspect', {barcode}); assert.equal(unverified.verified, false);
  delete elements.ContentPlaceHolder1_panCaptchaCode;
  elements.ContentPlaceHolder1_panWithAuthorization = {getClientRects: () => [1]};
  elements.ContentPlaceHolder1_btnLink = {getAttribute: () => 'https://my.dpd.de/share?pno=01999999999991'};
  elements.ContentPlaceHolder1_labDeliveryDetailsFromAddress = {innerText: 'Beispiel Shop\nStraße\nDeutschland'};
  const verified = await call('inspect', {barcode}); assert.equal(verified.verified, true); assert.equal(verified.sender, 'Beispiel Shop');
  const mismatch = await call('inspect', {barcode: '99999999999999'}); assert.equal(mismatch.verified, false);
  console.log('Passed: parcel matching, changed image, changed postcode, exact entry, verified sender only.');
})().catch(err => {console.error(err); process.exitCode = 1;});
