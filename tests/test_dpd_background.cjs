const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
let handler, applied = 0, matching = 1;
let storage = {};
const picture = {ok: true, barcode: '01999999999991', digest: 'abc', image: 'data:image/png;base64,abcd'};
const context = vm.createContext({URL, Map, Date, crypto: webcrypto, chrome: {
  runtime: {onMessage: {addListener: fn => {handler = fn;}}},
  storage: {session: {get: async () => storage, set: async value => {storage = structuredClone(value);}}},
  tabs: {query: async () => Array.from({length: matching}, (_, i) => ({id: 100 + i})),
    sendMessage: async (_, msg) => {if (msg.action === 'capture') return picture;if (msg.action === 'apply') {applied++;return {ok:true,submitted:true};}},
    get: async () => ({url: 'https://my.dpd.de/myparcels/test'})}
}});
vm.runInContext(fs.readFileSync('browser-extension/background.js', 'utf8'), context);
const call = (action, data, tabId = 1) => new Promise(resolve => handler({channel: 'DPD_ASSIST_V1', action, data},
  {tab: {id: tabId}, url: 'http://homeassistant.local:8123/dashboard-computer/pakete'}, resolve));
(async () => {
  const barcode = picture.barcode;
  const capture = await call('capture', {barcode});assert.equal(capture.ok,true);
  const denied = await call('apply', {...capture}, 2);assert.equal(denied.ok,false);assert.equal(applied,0);
  const mismatch = await call('apply', {...capture, digest:'changed'});assert.equal(mismatch.ok,false);assert.equal(applied,0);
  const success = await call('apply', {...capture});assert.equal(success.submitted,true);assert.equal(applied,1);
  const replay = await call('apply', {...capture});assert.equal(replay.ok,false);assert.equal(applied,1);
  matching = 2;const ambiguous = await call('capture', {barcode});assert.equal(ambiguous.ok,false);
  matching = 0;const missing = await call('capture', {barcode});assert.equal(missing.ok,false);
  console.log('Passed: bound HA tab, digest mismatch, single-use, ambiguous tabs, missing tab.');
})().catch(err => {console.error(err);process.exitCode=1;});
