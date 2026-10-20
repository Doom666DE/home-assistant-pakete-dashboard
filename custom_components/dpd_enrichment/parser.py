"""Conservative extraction: no status inference or browser credentials."""
import re
from html.parser import HTMLParser
from urllib.parse import unquote

CODE = re.compile(r"\d{14}\Z")

class DpdPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sender_parts = []
        self.depth = 0
        self.codes = set()
        self.verification = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        element = a.get('id', '')
        if element == 'ContentPlaceHolder1_labDeliveryDetailsFromAddress':
            self.depth = 1
        elif self.depth and tag not in ('br', 'img', 'input', 'hr', 'meta', 'link'):
            self.depth += 1
        if 'Captcha' in element or 'DataprotectionZipCode' in element:
            self.verification = True
        if element == 'ContentPlaceHolder1_hidParcelNo' and CODE.fullmatch(a.get('value', '')):
            self.codes.add(a['value'])
        if element == 'ContentPlaceHolder1_btnLink':
            self.codes.update(re.findall(r'[?&]pno=(\d{14})(?!\d)', unquote(a.get('href', ''))))

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth and data.strip():
            self.sender_parts.append(data.strip())

def website_sender(html, barcode):
    page = DpdPage()
    page.feed(html)
    if page.verification:
        return None, 'verification_required'
    if page.codes != {barcode}:
        return None, 'no_verified_details'
    sender = page.sender_parts[0] if page.sender_parts else None
    if not sender or sender in ('Deutschland', 'Germany') or len(sender) > 150:
        return None, 'no_sender'
    return sender, 'website'

def mail_details(subject, body, sender_header):
    """Only DPD-context mails, one barcode, explicit shipper phrase or merchant display name."""
    text = subject + '\n' + body
    if not re.search(r'\bdpd\b', text + '\n' + sender_header, re.I):
        return None
    codes = set(re.findall(r'(?:parcelno|parcelNumber|pno|paketnummer|sendungsnummer)\s*(?:=|:|%3D|\s)\s*(\d{14})(?!\d)', unquote(text), re.I))
    if len(codes) != 1:
        return None
    match = re.search(r'(?:Paket|Sendung)\s+von\s+([^\n<>]{2,150}?)(?=\s+(?:ist|wird|kommt|wurde)\b|[\n<>]|[.!?](?:\s|$)|$)', text, re.I)
    sender = match.group(1).strip() if match else None
    if not sender:
        # A merchant's display name is a weaker fallback; carrier notices are excluded.
        display = sender_header.split('<', 1)[0].strip(' \"') if '<' in sender_header else ''
        if display and '@' not in display and not re.search(r'\bdpd\b|no.?reply|notification', sender_header, re.I):
            sender = display
    if not sender or sender.lower() in ('uns', 'ihnen', 'dir'):
        return None
    return {'barcode': codes.pop(), 'sender': sender, 'source': 'mail'}


# Merchant mails are processed locally; no message content is sent to an AI.
from email.utils import parseaddr
from html import unescape

RECORD_CODE = re.compile(r'(?:\d{14}|1Z[A-Z0-9]{16}|[A-Z0-9]{8,14})\Z')
SHIP_WORDS = re.compile(r'\b(?:shipped|shipment|shipping|tracking|versandt|versendet|versand|sendung|paket|lieferung|zustellung)\b', re.I)
UPS_CODE = re.compile(r'(?<![A-Z0-9])1Z[A-Z0-9]{16}(?![A-Z0-9])', re.I)

def mail_candidate(subject, body, sender_header):
    text = unquote(unescape(subject + '\n' + body))
    return bool(SHIP_WORDS.search(text) or UPS_CODE.search(text) or re.search(r'\b(?:dpd|ups|gls)\b', sender_header, re.I))

class MailText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('br', 'p', 'div', 'li', 'tr'):
            self.parts.append('\n')
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))

_dpd_mail_details = mail_details

def mail_details(subject, body, sender_header):
    """One unambiguous shipment and merchant; no carrier-name guessing."""
    html = MailText()
    html.feed(unescape(body))
    text = unquote(unescape(subject + '\n' + '\n'.join(html.parts)))
    links = unquote(unescape('\n'.join(html.links)))
    if not SHIP_WORDS.search(text):
        return None
    codes = set(c.upper() for c in UPS_CODE.findall(text + '\n' + links))
    dpd = _dpd_mail_details(subject, text + '\n' + links, sender_header)
    if dpd:
        codes.add(dpd['barcode'])
    if re.search(r'\bgls\b', text + '\n' + links, re.I):
        codes.update(c.upper() for c in re.findall(r'(?:tracking(?:\s*(?:number|id|nummer))?|sendungsnummer|paketnummer|match|trackid|parcelnumber)\s*(?:[:=#]|\s)\s*([A-Z0-9]{8,14})(?![A-Z0-9])', text + '\n' + links, re.I))
    if len(codes) != 1:
        return None
    code = next(iter(codes))
    if dpd and code == dpd['barcode']:
        return dpd
    display, address = parseaddr(sender_header)
    domain = address.rsplit('@', 1)[-1].lower() if '@' in address else ''
    # Carrier/platform senders cannot be mistaken for the actual merchant.
    blocked = ('ups.com', 'dpd.de', 'dpd.com', 'gls-group.com', 'gls-germany.com', 'myhermes.de', 'dhl.de', 'dhl.com')
    if not domain or any(domain == d or domain.endswith('.' + d) for d in blocked):
        return None
    name = display.strip(' \"')
    if not name:
        if domain in {'gmail.com', 'gmx.de', 'gmx.net', 'web.de', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com'}:
            return None
        name = domain
    if re.search(r'@|no.?reply|notification|versandbenachrichtigung', name, re.I):
        return None
    name = ' '.join(name.split())
    if not 2 <= len(name) <= 150:
        return None
    return {'barcode': code, 'sender': name, 'source': 'mail'}
