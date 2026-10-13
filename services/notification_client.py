"""Resilient outbound HTTP adapter for Smartly decision notifications.

Uses a finite timeout, retries only transient transport/5xx failures, exponential
backoff with jitter, and never retries a partner 4xx response. Inject session and
sleep/random functions in tests so no real partner is contacted.
"""
import random
import time
import requests

class NotificationUnavailable(RuntimeError):
    """The notification partner could not be reached after bounded retries."""

class NotificationRejected(RuntimeError):
    """The partner rejected a request; retrying unchanged input is not useful."""

def send_decision_notice(base_url, payload, *, session=None, timeout=2.0,
                         max_attempts=3, base_delay=0.15,
                         sleep=time.sleep, jitter=random.uniform):
    session = session or requests
    url = base_url.rstrip("/") + "/notifications/decision"
    last_error = None
    for attempt in range(max_attempts):
        try:
            response = session.post(url, json=payload, timeout=timeout)
            if 200 <= response.status_code < 300:
                return response
            if 400 <= response.status_code < 500:
                raise NotificationRejected(
                    f"Notification partner rejected request (HTTP {response.status_code})"
                )
            last_error = NotificationUnavailable(
                f"Notification partner returned HTTP {response.status_code}"
            )
        except NotificationRejected:
            raise
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = NotificationUnavailable("Notification partner unavailable")
            last_error.__cause__ = exc
        if attempt < max_attempts - 1:
            delay = base_delay * (2 ** attempt) + jitter(0, base_delay)
            sleep(delay)
    raise NotificationUnavailable("Notification partner unavailable after bounded retries") from last_error
