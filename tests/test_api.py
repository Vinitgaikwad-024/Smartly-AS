import pytest
from app import app, BOOKINGS, IDEMPOTENCY, RATE_EVENTS
AUTH={"Authorization":"Bearer local-demo"}
BODY={"roomId":1,"date":"2026-11-01","startTime":"10:00","endTime":"11:00","purpose":"Study group"}
@pytest.fixture
def c():
    app.config["TESTING"]=True; BOOKINGS.clear(); IDEMPOTENCY.clear(); RATE_EVENTS.clear()
    with app.test_client() as client: yield client
def test_health(c): assert c.get("/health").status_code==200
def test_etag_304(c):
    r=c.get("/rooms/1"); assert r.status_code==200
    assert c.get("/rooms/1",headers={"If-None-Match":r.headers["ETag"]}).status_code==304
def test_auth(c): assert c.post("/bookings",json=BODY).status_code==401
def test_validation(c):
    r=c.post("/bookings",json={"roomId":"bad"},headers=AUTH)
    assert r.status_code==422 and r.json["errors"]
def test_idempotency(c):
    h={**AUTH,"Idempotency-Key":"same"}
    a=c.post("/bookings",json=BODY,headers=h); b=c.post("/bookings",json=BODY,headers=h)
    assert a.status_code==b.status_code==201 and a.json["id"]==b.json["id"] and len(BOOKINGS)==1
def test_room_not_found(c): assert c.get("/rooms/999").status_code==404
def test_xml(c): assert c.get("/health",headers={"Accept":"application/xml"}).headers["Content-Type"].startswith("application/xml")
def test_cancel_transition(c):
    a=c.post("/bookings",json=BODY,headers={**AUTH,"Idempotency-Key":"b1"})
    bid=a.json["id"]; assert c.post(f"/bookings/{bid}/cancel",headers=AUTH).status_code==200
    assert c.post(f"/bookings/{bid}/cancel",headers=AUTH).status_code==409


def test_malformed_json_is_400(c):
    r = c.post("/bookings", data='{"roomId":', content_type="application/json", headers=AUTH)
    assert r.status_code == 400
    assert r.headers["Content-Type"].startswith("application/problem+json")


def test_unknown_route_has_generic_problem_type(c):
    r = c.get("/not-a-real-route")
    assert r.status_code == 404
    assert r.json["code"] == "resource-not-found"


def test_rate_limit_returns_retry_after(c, monkeypatch):
    monkeypatch.setenv("SMARTLY_RATE_LIMIT", "1")
    # Runtime limit is read at module import, so patch the module constant for this test.
    import app as app_module
    monkeypatch.setattr(app_module, "RATE_LIMIT", 1)
    assert c.get("/bookings", headers=AUTH).status_code == 200
    r = c.get("/bookings", headers=AUTH)
    assert r.status_code == 429
    assert "Retry-After" in r.headers
