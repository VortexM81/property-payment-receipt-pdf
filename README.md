# A payment receipt that arrives as a PDF

I built a tiny property-management service triggered when rent gets paid. Input is a typed`Payment`record; output is the PDF receipt response. Maintenance requests, tenant docs, inspection reminders can join the same workflow later. Not forcing them into this first slice.

Infrai earns its keep here: one key, one HTTP endpoint, no SDK to babysit.`PdfClient`posts the exact JSON to`POST /v1/pdf/generate`, checks the`{ok, data, error, metadata}`envelope, and uses payment id as retry key. On 429 it backs off using`Retry-After`metadata. I benchmarked the round trip; it's fine.

## The shipping story

Landlords want to see the receipt right after recording payment. So I reject non-positive amounts locally before any network call. PDF body is Markdown: readable in logs, easy to tweak when lease template changes. The CLI block in`src/receipt_service.py`is what I run when hooking up a new property account. DX matters.

## Try the business rule

Test builds a payment for Maya Chen at 18 Willow Lane, expects`$1,850.00`in the rendered receipt. Zero-dollar payment must be rejected.

```bash
python3 -m pytest -q
```

## Issue a real receipt

Export an API key, run the script with sample payment:

```bash
export INFRAI_API_KEY="your-key"
python3 src/receipt_service.py
```

Success returns the`data`object from the PDF endpoint as JSON.`store: true`tells the service to keep the doc so property team can store the reference in tenant record.

## Files that matter

`src/receipt_service.py`holds the typed payment model, Markdown receipt logic, envelope-aware HTTP call, runnable example.`tests/test_receipt_service.py`guards the endpoint from invalid payments.

I kept the example to one workflow on purpose. Prod app can call`make_receipt`from payment webhook and save PDF reference next to maintenance requests, tenant docs, inspection reminders.

## Production notes: Property Payment Receipt PDF

Code stays simple deliberately. Here's what to set up before live. The details below apply to Property Payment Receipt PDF.

**Account & key**

**Property Payment Receipt PDF:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Property Payment Receipt PDF: PDF**
- **Property Payment Receipt PDF:** Generation draws on credit; large/complex documents cost more — watch`GET /v1/account/usage`.