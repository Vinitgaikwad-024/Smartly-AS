from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, make_response, url_for
from functools import wraps
from collections import defaultdict, deque
import os
from models import validate_booking_payload
from errors import PROBLEM_TYPES
import time

app = Flask(__name__)
ROOMS = {
  1: {"id":1,"name":"Lab A","building":"Academic Block","type":"lab","capacity":30,"equipment":["computers","projector"],"available":True,"version":1},
  2: {"id":2,"name":"Classroom 204","building":"Academic Block","type":"classroom","capacity":60,"equipment":["projector","whiteboard"],"available":True,"version":1}
}
BOOKINGS, IDEMPOTENCY = {}, {}
next_booking = 1
# In-memory sliding-window limiter for coursework/demo use.
RATE_WINDOW_SECONDS = 60
RATE_LIMIT = int(os.getenv("SMARTLY_RATE_LIMIT", "60"))
RATE_EVENTS = defaultdict(deque)
def problem(status, code, title, detail, errors=None, headers=None):
    body={"type":PROBLEM_TYPES.get(code, PROBLEM_TYPES["internal-error"]),"title":title,"status":status,"detail":detail,"instance":request.path,"code":code}
    if errors: body["errors"]=errors
    r=make_response(jsonify(body),status); r.headers["Content-Type"]="application/problem+json; charset=utf-8"; r.headers["Cache-Control"]="no-store"
    if headers: r.headers.update(headers)
    return r
def output(data,status=200,headers=None):
    accept=request.headers.get("Accept","application/json").lower()
    if "application/xml" in accept and "application/json" not in accept:
        def xml(v):
            if isinstance(v,dict): return "".join(f"<{k}>{xml(x)}</{k}>" for k,x in v.items())
            if isinstance(v,list): return "".join(f"<item>{xml(x)}</item>" for x in v)
            return str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        r=make_response(f'<?xml version="1.0" encoding="UTF-8"?><response>{xml(data)}</response>',status); r.headers["Content-Type"]="application/xml; charset=utf-8"
    elif "application/json" in accept or "*/*" in accept:
        r=make_response(jsonify(data),status); r.headers["Content-Type"]="application/json; charset=utf-8"
    else: return problem(406,"not-acceptable","Not Acceptable","Use application/json or application/xml.")
    r.headers["Cache-Control"]="no-cache"
    if headers: r.headers.update(headers)
    return r
@app.after_request
def headers(r):
    r.headers.setdefault("X-Content-Type-Options","nosniff")
    r.headers.setdefault("Access-Control-Allow-Origin","*")
    r.headers.setdefault("Access-Control-Allow-Methods","GET, POST, PATCH, PUT, DELETE, OPTIONS")
    r.headers.setdefault("Access-Control-Allow-Headers","Authorization, Content-Type, Accept, If-Match, If-None-Match, Idempotency-Key")
    r.headers.setdefault("Access-Control-Expose-Headers","ETag, Location, Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining")
    # HSTS is emitted only when explicitly enabled for an HTTPS deployment.
    if os.getenv("SMARTLY_HTTPS_DEPLOYMENT", "").lower() == "true":
        r.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    key = request.remote_addr or "unknown"
    now = time.monotonic(); events = RATE_EVENTS[key]
    while events and now - events[0] >= RATE_WINDOW_SECONDS: events.popleft()
    remaining = max(0, RATE_LIMIT - len(events))
    r.headers.setdefault("X-RateLimit-Limit", str(RATE_LIMIT))
    r.headers.setdefault("X-RateLimit-Remaining", str(remaining))
    r.headers.setdefault("Allow","GET, POST, PATCH, PUT, DELETE, OPTIONS")
    return r
#@app.route("/<path:p>",methods=["OPTIONS"])
#@app.route("/",methods=["OPTIONS"])
def options(p=""): return make_response("",204,{"Allow":"GET, POST, PATCH, PUT, DELETE, OPTIONS"})
def auth(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        key = request.remote_addr or "unknown"
        now = time.monotonic(); events = RATE_EVENTS[key]
        while events and now - events[0] >= RATE_WINDOW_SECONDS: events.popleft()
        if len(events) >= RATE_LIMIT:
            retry = max(1, int(RATE_WINDOW_SECONDS - (now - events[0])))
            return problem(429, "rate-limit-exceeded", "Too Many Requests", "Request limit exceeded; retry after the indicated delay.", headers={"Retry-After": str(retry)})
        events.append(now)
        h=request.headers.get("Authorization","")
        if not h.startswith("Bearer ") or not h[7:].strip():
            return problem(401,"unauthorized","Unauthorized","A non-empty Bearer token is required.",headers={"WWW-Authenticate":"Bearer"})
        return fn(*a,**kw)
    return wrapped
def validate(d):
    return validate_booking_payload(d, ROOMS)
@app.get("/health")
def health(): return output({"status":"ok","service":"smartly-access-flow"})
@app.get("/rooms")
def rooms():
    items=list(ROOMS.values())
    b=request.args.get("building"); t=request.args.get("type"); cap=request.args.get("minCapacity",type=int)
    if b: items=[x for x in items if x["building"].lower()==b.lower()]
    if t: items=[x for x in items if x["type"]==t]
    if cap is not None: items=[x for x in items if x["capacity"]>=cap]
    page=max(1,request.args.get("page",1,type=int)); limit=min(50,max(1,request.args.get("limit",20,type=int)))
    return output({"items":items[(page-1)*limit:page*limit],"page":page,"limit":limit,"total":len(items)})
@app.get("/rooms/<int:rid>")
def room(rid):
    x=ROOMS.get(rid)
    if not x: return problem(404,"room-not-found","Room not found",f"No room exists with id {rid}.")
    tag=f'"room-{rid}-v{x["version"]}"'
    if request.headers.get("If-None-Match")==tag: return make_response("",304,{"ETag":tag})
    return output(x,headers={"ETag":tag,"Cache-Control":"private, max-age=0, must-revalidate"})
@app.post("/bookings")
@auth
def create():
    global next_booking
    if not request.is_json: return problem(415,"unsupported-media-type","Unsupported Media Type","Send application/json.")
    try:
        d=request.get_json(silent=False)
    except Exception:
        return problem(400,"invalid-request","Bad Request","Malformed JSON request body.")
    errors=validate(d)
    if errors: return problem(422,"validation-error","Validation failed","One or more fields are invalid.",errors)
    key=request.headers.get("Idempotency-Key")
    if key and key in IDEMPOTENCY:
        saved=IDEMPOTENCY[key]; return output(saved["body"],201,{"Location":saved["location"],"Idempotency-Replayed":"true"})
    for x in BOOKINGS.values():
        if x["roomId"]==d["roomId"] and x["date"]==d["date"] and x["status"] in ("pending","approved") and d["startTime"]<x["endTime"] and d["endTime"]>x["startTime"]:
            return problem(409,"room-unavailable","Room unavailable","This room already has a booking during that time.")
    x={"id":next_booking,"roomId":d["roomId"],"date":d["date"],"startTime":d["startTime"],"endTime":d["endTime"],"purpose":d["purpose"].strip(),"status":"pending","studentId":d.get("studentId","demo-student"),"createdAt":datetime.now(timezone.utc).isoformat(),"version":1}
    next_booking+=1; BOOKINGS[x["id"]]=x; loc=f"/bookings/{x['id']}"
    if key: IDEMPOTENCY[key]={"body":x,"location":loc}
    return output(x,201,{"Location":loc,"ETag":f'"booking-{x["id"]}-v1"'})
@app.get("/bookings")
@auth
def booking_list():
    xs=list(BOOKINGS.values()); s=request.args.get("status")
    if s: xs=[x for x in xs if x["status"]==s]
    return output({"items":xs,"total":len(xs)})
@app.get("/bookings/<int:bid>")
@auth
def get_booking(bid):
    x=BOOKINGS.get(bid)
    if not x: return problem(404,"booking-not-found","Booking not found",f"No booking exists with id {bid}.")
    tag=f'"booking-{bid}-v{x["version"]}"'
    if request.headers.get("If-None-Match")==tag: return make_response("",304,{"ETag":tag})
    return output(x,headers={"ETag":tag,"Cache-Control":"private, no-cache"})
def decide(bid,status):
    x=BOOKINGS.get(bid)
    if not x: return problem(404,"booking-not-found","Booking not found",f"No booking exists with id {bid}.")
    if x["status"]!="pending": return problem(409,"illegal-transition","Illegal transition","Only pending bookings can be changed.")
    x["status"]=status; x["version"]+=1
    return output(x)
@app.post("/bookings/<int:bid>/cancel")
@auth
def cancel(bid): return decide(bid,"cancelled")
@app.post("/bookings/<int:bid>/approve")
@auth
def approve(bid): return decide(bid,"approved")
@app.post("/bookings/<int:bid>/reject")
@auth
def reject(bid): return decide(bid,"rejected")
@app.get("/admin/rooms")
@auth
def admin_rooms(): return output({"items":list(ROOMS.values()),"total":len(ROOMS)})
@app.post("/admin/rooms")
@auth
def add_room():
    if not request.is_json: return problem(415,"unsupported-media-type","Unsupported Media Type","Send JSON.")
    try: d=request.get_json(silent=False)
    except Exception: return problem(400,"invalid-request","Bad Request","Malformed JSON request body.")
    d=d or {}; errs=[]
    for f in ("name","building","type"):
        if not isinstance(d.get(f),str) or not d[f].strip(): errs.append({"field":f,"reason":"is required"})
    if not isinstance(d.get("capacity"),int) or d.get("capacity",0)<1: errs.append({"field":"capacity","reason":"must be a positive integer"})
    if errs: return problem(422,"validation-error","Validation failed","Invalid room fields.",errs)
    rid=max(ROOMS)+1; x={"id":rid,"name":d["name"],"building":d["building"],"type":d["type"],"capacity":d["capacity"],"equipment":d.get("equipment",[]),"available":True,"version":1}; ROOMS[rid]=x
    return output(x,201,{"Location":f"/rooms/{rid}","ETag":f'"room-{rid}-v1"'})
@app.patch("/admin/rooms/<int:rid>")
@auth
def update_room(rid):
    x=ROOMS.get(rid)
    if not x: return problem(404,"room-not-found","Room not found",f"No room exists with id {rid}.")
    if not request.is_json: return problem(415,"unsupported-media-type","Unsupported Media Type","Send JSON.")
    try: d=request.get_json(silent=False)
    except Exception: return problem(400,"invalid-request","Bad Request","Malformed JSON request body.")
    d=d or {}
    if not d: return problem(422,"validation-error","Validation failed","Provide at least one field.")
    current=f'"room-{rid}-v{x["version"]}"'
    if "If-Match" in request.headers and request.headers["If-Match"]!=current: return problem(412,"invalid-request","Precondition Failed","Room changed; fetch the latest ETag.")
    for k,v in d.items():
        if k in ("name","building","type","capacity","equipment","available"): x[k]=v
    x["version"]+=1
    return output(x,headers={"ETag":f'"room-{rid}-v{x["version"]}"'})
@app.delete("/admin/rooms/<int:rid>")
@auth
def delete_room(rid):
    if rid not in ROOMS: return problem(404,"room-not-found","Room not found",f"No room exists with id {rid}.")
    del ROOMS[rid]; return make_response("",204)
@app.errorhandler(405)
def handle_method_not_allowed(error):
    return problem(
        405,
        "method-not-allowed",
        "Method Not Allowed",
        "This HTTP method is not supported for the requested resource."
    )
@app.errorhandler(404)
def missing(_): return problem(404,"resource-not-found","Not Found","The requested route or resource was not found.")
@app.errorhandler(400)
def malformed(_): return problem(400,"invalid-request","Bad Request","Request syntax or JSON is malformed.")
if __name__=="__main__": app.run(port=5000,debug=True)
