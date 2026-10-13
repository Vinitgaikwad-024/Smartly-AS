# Assignment 3 — SOAP Partner Integration (Design-Time)

## Partner and rationale
Smartly integrates with a fictional campus notification partner. SOAP is selected for this example because the contract is described by WSDL, message structure is explicit XML, and partner faults have a standard SOAP Fault representation. This is design-time coursework; the `.example.edu` endpoint is reserved/example-only and no real external system is contacted.

## HTTP binding
- Method: `POST`
- Endpoint: `https://partner.example.edu/soap/NotificationService`
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `urn:smartly:notification:SendDecisionNotice`
- Discovery: direct WSDL URL, with a single catalogue record documented below. No live UDDI registry is claimed.

## Discovery catalogue record
| Field | Value |
|---|---|
| Service name | Campus Notification Service |
| Owner | Fictional Campus Partner |
| WSDL | `https://partner.example.edu/soap/NotificationService?wsdl` |
| Endpoint | `https://partner.example.edu/soap/NotificationService` |
| Binding | SOAP 1.1 over HTTP POST |
| Operation | `SendDecisionNotice` |
| Version | `1.0` |
| Status | Design-time example; endpoint not verified/live |

## Message and fault mapping
- `soap-request.xml`: includes a SOAP Header with demo credentials and a `SendDecisionNotice` body.
- `soap-response.xml`: successful partner receipt.
- `soap-fault.xml`: sample partner fault.
- Partner-specific `RecipientUnavailable` is mapped internally to Smartly's stable `notification-delivery-failed`; partner fault names and raw payloads are not leaked to REST clients.

The companion `integration.pdf` summarizes the contract, HTTP binding, discovery record and mapping.
