"""Read marketplace sellers from signed-in Amazon order details."""

import re
from html.parser import HTMLParser

_PRODUCT = re.compile(r"/(?:dp|gp/product)/[A-Z0-9]{10}(?:[/?#]|$)", re.I)
_SELLER = re.compile(r"^(?:Verkauf durch|Verkauft von|Sold by)\s*:\s*(.*)$", re.I)
_VOID = set("area base br col embed hr img input link meta param source track wbr".split())


class OrderDetails(HTMLParser):
    """Collect visible text and links only inside the order details panel."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.link = None
        self.tokens = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "orderDetails" and not self.depth:
            self.depth = 1
        elif self.depth and tag not in _VOID:
            self.depth += 1
        if self.depth and tag == "a":
            self.link = (attrs.get("href", ""), [])

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "a" and self.link is not None:
            href, parts = self.link
            self.tokens.append((href, " ".join(" ".join(parts).split())))
            self.link = None
        if tag not in _VOID:
            self.depth -= 1

    def handle_data(self, data):
        text = " ".join(data.split())
        if self.depth and text:
            if self.link is None:
                self.tokens.append(("", text))
            else:
                self.link[1].append(text)


def sellers_for_items(page, items):
    """Resolve every shipment item by its exact title and explicit seller label."""
    details = OrderDetails()
    details.feed(page)
    sellers = {}
    title = None
    label = False
    for href, text in details.tokens:
        if _PRODUCT.search(href):
            if text:
                title = text.casefold()
                sellers.setdefault(title, set())
            label = False
            continue
        match = _SELLER.fullmatch(text)
        if match and title:
            value = match.group(1)
            if value:
                sellers[title].add(value)
            label = not value
        elif label:
            if title and text and (not href or "/gp/aag/" in href or "seller=" in href):
                sellers[title].add(text)
            label = False
    matched = set()
    for item in items:
        options = sellers.get(" ".join(item.split()).casefold(), set())
        if len(options) != 1:
            return None
        matched.update(options)
    return next(iter(matched)) if len(matched) == 1 else None
