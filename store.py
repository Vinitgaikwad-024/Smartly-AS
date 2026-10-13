"""In-memory repository for the Smartly coursework prototype.

This adapter is intentionally process-local and resets on restart. Replace it with
SQL-backed repositories before any real deployment.
"""
ROOMS = {
    1: {"id": 1, "name": "Lab A", "building": "Academic Block", "type": "lab", "capacity": 30, "equipment": ["computers", "projector"], "available": True, "version": 1},
    2: {"id": 2, "name": "Classroom 204", "building": "Academic Block", "type": "classroom", "capacity": 60, "equipment": ["projector", "whiteboard"], "available": True, "version": 1},
}
BOOKINGS = {}
IDEMPOTENCY = {}
RATE_EVENTS = {}
NEXT_BOOKING_ID = 1
