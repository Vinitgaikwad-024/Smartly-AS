# Assignment 2 — Services, Contracts and Schema

## Business capabilities
1. Search/filter room availability.
2. Inspect room, building and equipment details.
3. Create a booking request.
4. Review, approve or reject a booking.
5. Cancel a pending booking.
6. Maintain room/resource inventory.
7. Authenticate users and apply roles.
8. Notify requesters of decisions and view booking history.

## Service boundaries and ownership
| Service | Owns | Main contract operations |
|---|---|---|
| Identity | users, institutional identity, roles | `authenticate`, `getRoles` |
| Resource Catalogue | buildings, rooms, equipment | `searchRooms`, `getRoom`, `createRoom`, `updateRoom` |
| Booking | booking request, status, time conflict rules | `createBooking`, `getBooking`, `listBookings`, `cancelBooking` |
| Approval | decision/audit record | `approveBooking`, `rejectBooking` |
| Notification | notification preferences, delivery attempts | `sendDecisionNotice` |

A service owns its own data. The diagram's labelled arrows represent contract calls, not shared-table access. The submitted Flask implementation is a coursework-sized API prototype with in-memory room/booking storage; the service map is the proposed logical architecture, not a claim that five separately deployed services exist.

## Contract table
| Operation | Inputs | Success output | Stable errors |
|---|---|---|---|
| `searchRooms` | building, type, minCapacity, page, limit | paginated room list | `invalid-request` |
| `getRoom` | roomId | room details + ETag | `room-not-found` |
| `createBooking` | roomId, date, startTime, endTime, purpose | pending booking, 201 + Location | `validation-error`, `room-not-found`, `room-unavailable`, `unauthorized` |
| `getBooking` | bookingId | booking details + ETag | `booking-not-found`, `unauthorized` |
| `cancelBooking` | bookingId, authenticated requester | cancelled booking | `booking-not-found`, `illegal-transition` |
| `approveBooking` / `rejectBooking` | bookingId, approver | updated booking | `booking-not-found`, `illegal-transition` |
| `sendDecisionNotice` | booking reference, recipient, decision | delivery receipt | `notification-delivery-failed` |

## Central operation: createBooking
Validate the JSON contract and time interval; confirm the room exists; reject overlapping pending/approved bookings; create a pending booking; return a stable booking resource and `Location`. Storage and partner implementation details are not exposed in the contract.

## Service quality checks
- **Reachable:** each proposed service has an address/endpoint and health/availability strategy.
- **Self-contained:** one service owns each table/entity set.
- **Contract-defined:** operations, fields and stable errors are documented above.
- **Independent:** deployable/versionable separately in the proposed architecture.
- **Loosely coupled:** calls use contracts, not cross-service database reads.

## Diagram and schema artifacts
See `services.drawio`, `services.svg`, `schema.drawio`, `schema.svg`, and `design.pdf` in this assignment folder. `../../database/schema.sql` contains the relational schema for the prototype. These files show proposed service ownership and the normalized data model.
