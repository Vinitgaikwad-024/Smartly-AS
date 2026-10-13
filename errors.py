"""Stable Smartly error identifiers used by the Problem Details API."""
PROBLEM_TYPES = {
    code: f"https://smartly.example.edu/problems/{code}"
    for code in (
        "validation-error", "room-not-found", "booking-not-found", "resource-not-found",
        "room-unavailable", "illegal-transition", "unauthorized", "not-acceptable",
        "unsupported-media-type", "rate-limit-exceeded", "invalid-request",
        "internal-error", "notification-delivery-failed",
    )
}

STATUS_TITLES = {
    400: "Bad Request", 401: "Unauthorized", 404: "Not Found", 406: "Not Acceptable",
    409: "Conflict", 412: "Precondition Failed", 415: "Unsupported Media Type",
    422: "Validation Failed", 429: "Too Many Requests", 500: "Internal Server Error",
    503: "Service Unavailable",
}
