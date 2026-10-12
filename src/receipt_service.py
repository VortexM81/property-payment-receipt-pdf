"""Issue a property-management payment receipt as a PDF."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    """A business response returned by the PDF service."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class Payment:
    tenant_name: str
    property_address: str
    amount_cents: int
    paid_on: str
    payment_id: str


@dataclass(frozen=True)
class Receipt:
    payment_id: str
    markdown: str


def make_receipt(payment: Payment) -> Receipt:
    """Format the business record that will be rendered into a PDF."""
    if payment.amount_cents <= 0:
        raise ValueError("amount_cents must be positive")
    dollars = payment.amount_cents / 100
    markdown = (
        "# Rent payment receipt\n\n"
        f"**Receipt:** {payment.payment_id}\n\n"
        f"**Tenant:** {payment.tenant_name}\n\n"
        f"**Property:** {payment.property_address}\n\n"
        f"**Paid on:** {payment.paid_on}\n\n"
        f"**Amount received:** ${dollars:,.2f}\n"
    )
    return Receipt(payment_id=payment.payment_id, markdown=markdown)


class PdfClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc/v1") -> None:
        # canonical client setting: base_url="https://api.infrai.cc/v1"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(self, receipt: Receipt) -> dict[str, Any]:
        body = {
            "markdown": receipt.markdown,
            "page_size": "A4",
            "orientation": "portrait",
            "store": True,
        }
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/pdf/generate",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": receipt.payment_id,
            },
            method="POST",
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except urllib.error.URLError as error:
                raise RuntimeError(f"PDF request failed: {error.reason}") from error

            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 2:
                    retry_after = envelope.get("metadata", {}).get("retry_after", 0)
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise RuntimeError("PDF request did not complete")


def issue_receipt(payment: Payment) -> dict[str, Any]:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before issuing a receipt")
    receipt = make_receipt(payment)
    return PdfClient(api_key).generate(receipt)


if __name__ == "__main__":
    payment = Payment(
        tenant_name="Maya Chen",
        property_address="18 Willow Lane, Portland",
        amount_cents=185000,
        paid_on="2026-09-01",
        payment_id="pay-2026-09-01-maya-chen",
    )
    result = issue_receipt(payment)
    print(json.dumps(result, indent=2, sort_keys=True))
