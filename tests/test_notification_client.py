from services.notification_client import (
    send_decision_notice, NotificationUnavailable, NotificationRejected
)
import requests

class Response:
    def __init__(self, status): self.status_code = status

class FakeSession:
    def __init__(self, results): self.results=list(results); self.calls=0; self.timeouts=[]
    def post(self, url, json, timeout):
        self.calls += 1; self.timeouts.append(timeout)
        result=self.results.pop(0)
        if isinstance(result, Exception): raise result
        return Response(result)

def test_retry_transient_503_then_success():
    s=FakeSession([503, 200]); sleeps=[]
    r=send_decision_notice("https://partner.example.edu", {"bookingId":7},
        session=s, sleep=sleeps.append, jitter=lambda a,b:0)
    assert r.status_code==200 and s.calls==2
    assert s.timeouts==[2.0,2.0] and sleeps==[0.15]

def test_does_not_retry_partner_4xx():
    s=FakeSession([400])
    try:
        send_decision_notice("https://partner.example.edu", {}, session=s, sleep=lambda _:None)
        assert False, "expected NotificationRejected"
    except NotificationRejected:
        assert s.calls==1

def test_bounded_timeout_retries():
    s=FakeSession([requests.Timeout(), requests.Timeout(), requests.Timeout()])
    try:
        send_decision_notice("https://partner.example.edu", {}, session=s,
            max_attempts=3, sleep=lambda _:None, jitter=lambda a,b:0)
        assert False, "expected NotificationUnavailable"
    except NotificationUnavailable:
        assert s.calls==3
