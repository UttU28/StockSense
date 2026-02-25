import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse, JSONResponse
from pydantic import BaseModel
import httpx

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

STOCK_GITA_BASE = os.getenv("STOCK_GITA_BACKEND_URL", "https://rakeshent.info").rstrip("/")

# Firebase Admin (for auth + Firestore)
_firebase_app = None
_firestore = None

def _get_firebase():
    global _firebase_app, _firestore
    if _firebase_app is None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            config_path = os.getenv("FIREBASE_CONFIG_PATH") or str(Path(__file__).resolve().parent / "firebase-config.json")
            with open(config_path, "r") as f:
                config = json.load(f)
            cred = credentials.Certificate(config)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firestore = firestore.client()
        except Exception as e:
            log.warning("Firebase Admin init failed: %s", e)
            _firestore = None
    return _firebase_app, _firestore


class RegisterBody(BaseModel):
    idToken: str
    displayName: str = ""
    email: str = ""


class UpdateProfileBody(BaseModel):
    idToken: str
    displayName: str


class CreateChatBody(BaseModel):
    title: str = "New chat"


class AddMessageBody(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class UpdateChatBody(BaseModel):
    title: str | None = None


# Stripe: price in cents -> credits (server-authoritative)
STRIPE_PRICE_TO_CREDITS = {
    2000: 150_000,   # $20 -> Starter
    5000: 500_000,   # $50 -> Pro
    10_000: 1_400_000,  # $100 -> Growth
}
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://lucky-adjusted-possum.ngrok-free.app").rstrip("/")


class CreateCheckoutBody(BaseModel):
    priceCents: int  # 2000, 5000, 10000


# 1 token = 1 credit for chat usage
TOKENS_PER_CREDIT = int(os.getenv("TOKENS_PER_CREDIT", "1"))


class RecordUsageBody(BaseModel):
    chatId: str
    tokensUsed: int


async def get_uid_from_token(request: Request) -> str:
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        app_fb, _ = _get_firebase()
        if app_fb is None:
            raise HTTPException(status_code=503, detail="Auth not configured")
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(token)
        uid = decoded.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        return uid
    except HTTPException:
        raise
    except Exception as e:
        log.warning("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


app = FastAPI(
    title="StockSense Frontend Backend",
    description="Ticker via Yahoo Finance; other API proxied to rakeshent.info",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check for this proxy server."""
    return {"status": "ok", "proxy_target": STOCK_GITA_BASE, "ticker": "yfinance"}


# In-memory cache for ticker batch (5 min TTL)
_ticker_cache: dict[str, tuple[dict, float]] = {}
TICKER_CACHE_TTL_SEC = 300  # 5 minutes


@app.get("/api/ticker/batch/{symbols:path}")
async def ticker_batch(symbols: str):
    """Serve ticker data using free Yahoo Finance (yfinance) by default from this backend."""
    symbols_raw = unquote(symbols)
    cache_key = symbols_raw
    now = time.time()
    if cache_key in _ticker_cache:
        cached_data, cached_at = _ticker_cache[cache_key]
        if now - cached_at < TICKER_CACHE_TTL_SEC:
            return JSONResponse(content={"data": cached_data})
    try:
        import yfinance as yf
    except ImportError:
        log.warning("yfinance not installed; pip install yfinance")
        return JSONResponse(content={"data": {}}, status_code=503)
    symbol_list = [s.strip() for s in symbols_raw.split(",") if s.strip()]
    if not symbol_list:
        return JSONResponse(content={"data": {}})
    results = {}
    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("price", 0)
            previous_close = info.get("previousClose", current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            results[symbol] = {
                "currentPrice": current_price,
                "previousClose": previous_close,
                "change": change,
                "changePercent": change_percent,
            }
        except Exception as e:
            log.warning("Ticker error for %s: %s", symbol, e)
            results[symbol] = {"error": str(e), "currentPrice": 0, "change": 0, "changePercent": 0}
    _ticker_cache[cache_key] = (results, time.time())
    return JSONResponse(content={"data": results})


# New user signup bonus (credits)
NEW_USER_CREDITS = int(os.getenv("NEW_USER_CREDITS", "50000"))


@app.post("/auth/register")
async def auth_register(body: RegisterBody):
    """Verify Firebase ID token and upsert user in Firestore (name, email, uid). New users get 50K credits."""
    try:
        app_fb, db = _get_firebase()
        if app_fb is None or db is None:
            return JSONResponse(content={"ok": False, "error": "Firebase not configured"}, status_code=503)
        from firebase_admin import auth as fb_auth, firestore as _fstore
        decoded = fb_auth.verify_id_token(body.idToken)
        uid = decoded.get("uid")
        email = body.email or decoded.get("email") or ""
        display_name = body.displayName or decoded.get("name") or ""
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        users_ref = db.collection("users").document(uid)
        doc = users_ref.get()
        is_new = not doc.exists
        data: dict = {
            "uid": uid,
            "email": email,
            "displayName": display_name,
            "updatedAt": _fstore.SERVER_TIMESTAMP,
        }
        if is_new:
            data["credits"] = NEW_USER_CREDITS
        users_ref.set(data, merge=True)
        return JSONResponse(content={"ok": True, "uid": uid})
    except HTTPException:
        raise
    except Exception as e:
        log.exception("auth/register failed: %s", e)
        if "Firebase" in str(e) or "token" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/auth/profile")
async def update_profile(body: UpdateProfileBody):
    """Update user profile (displayName) in Firestore."""
    try:
        app_fb, db = _get_firebase()
        if app_fb is None or db is None:
            return JSONResponse(content={"ok": False, "error": "Firebase not configured"}, status_code=503)
        from firebase_admin import auth as fb_auth, firestore as _fstore
        decoded = fb_auth.verify_id_token(body.idToken)
        uid = decoded.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        display_name = (body.displayName or "").strip()
        if not display_name:
            raise HTTPException(status_code=400, detail="displayName is required")
        users_ref = db.collection("users").document(uid)
        users_ref.set({
            "displayName": display_name,
            "updatedAt": _fstore.SERVER_TIMESTAMP,
        }, merge=True)
        return {"ok": True, "uid": uid}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("auth/profile update failed: %s", e)
        if "Firebase" in str(e) or "token" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        raise HTTPException(status_code=500, detail=str(e))


# ----- Chat sessions API (Firestore) -----

@app.get("/api/chats")
async def list_chats(request: Request):
    """List all chats for the authenticated user."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    from google.cloud.firestore_v1 import FieldFilter
    chats_ref = db.collection("chats")
    query = chats_ref.where(filter=FieldFilter("userId", "==", uid)).limit(100)
    try:
        docs = list(query.stream())
    except Exception as e:
        log.warning("chats query failed: %s", e)
        docs = []
    out = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        out.append(d)
    out.sort(key=lambda x: x.get("updatedAt") or datetime.min, reverse=True)
    return {"chats": out}


@app.post("/api/chats")
async def create_chat(request: Request, body: CreateChatBody | None = None):
    """Create a new chat session."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    title = ((body.title if body else None) or "New chat").strip() or "New chat"
    ref = db.collection("chats").document()
    ref.set({
        "userId": uid,
        "title": title,
        "createdAt": _fstore.SERVER_TIMESTAMP,
        "updatedAt": _fstore.SERVER_TIMESTAMP,
    })
    return {"id": ref.id, "title": title}


@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str, request: Request):
    """Get a chat and its messages."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    chat_ref = db.collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    data = chat_doc.to_dict()
    if data.get("userId") != uid:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages_ref = chat_ref.collection("messages").order_by("createdAt", direction=_fstore.Query.ASCENDING)
    messages_docs = list(messages_ref.stream())
    messages = []
    for m in messages_docs:
        md = m.to_dict()
        messages.append({"role": md.get("role", "user"), "content": md.get("content", "")})
    return {
        "id": chat_id,
        "title": data.get("title", "New chat"),
        "createdAt": getattr(data.get("createdAt"), "isoformat", lambda: None)(),
        "updatedAt": getattr(data.get("updatedAt"), "isoformat", lambda: None)(),
        "messages": messages,
    }


@app.post("/api/chats/{chat_id}/messages")
async def add_chat_message(chat_id: str, request: Request, body: AddMessageBody):
    """Append a message to a chat. When role is assistant, backend calculates token usage and deducts credits."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    chat_ref = db.collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    data = chat_doc.to_dict()
    if data.get("userId") != uid:
        raise HTTPException(status_code=404, detail="Chat not found")
    role = (body.role or "user").strip().lower()
    if role not in ("user", "assistant", "system"):
        role = "user"
    msg_ref = chat_ref.collection("messages").document()
    msg_ref.set({
        "role": role,
        "content": body.content or "",
        "createdAt": _fstore.SERVER_TIMESTAMP,
    })
    chat_ref.update({"updatedAt": _fstore.SERVER_TIMESTAMP})
    if role == "assistant" and db is not None:
        try:
            last_msgs = list(
                chat_ref.collection("messages").order_by("createdAt", direction=_fstore.Query.DESCENDING).limit(2).stream()
            )
            assistant_content = body.content or ""
            user_content = ""
            for m in last_msgs:
                d = m.to_dict()
                if d.get("role") == "user":
                    user_content = d.get("content") or ""
                    break
            tokens_used = _estimate_tokens(assistant_content) + _estimate_tokens(user_content)
            if tokens_used > 0:
                _deduct_usage(db, uid, chat_id, tokens_used)
        except Exception as e:
            log.warning("Could not deduct usage on assistant message: %s", e)
    return {"id": msg_ref.id}


@app.patch("/api/chats/{chat_id}")
async def update_chat(chat_id: str, request: Request, body: UpdateChatBody):
    """Update chat title."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    chat_ref = db.collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat_doc.to_dict().get("userId") != uid:
        raise HTTPException(status_code=404, detail="Chat not found")
    if body.title is not None:
        from firebase_admin import firestore as _fstore
        chat_ref.update({"title": body.title.strip() or "New chat", "updatedAt": _fstore.SERVER_TIMESTAMP})
    return {"ok": True}


@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    """Delete a chat and all its messages."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    chat_ref = db.collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat_doc.to_dict().get("userId") != uid:
        raise HTTPException(status_code=404, detail="Chat not found")
    for msg_doc in chat_ref.collection("messages").stream():
        msg_doc.reference.delete()
    chat_ref.delete()
    return {"ok": True}


# ----- Credits & Stripe -----

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (OpenAI-style)."""
    if not text or not text.strip():
        return 0
    return max(1, (len(text) + 3) // 4)


def _deduct_usage(db, uid: str, chat_id: str, tokens_used: int):
    """Deduct credits for token usage, write to usage_log, and print. Caller must have _fstore imported."""
    from firebase_admin import firestore as _fstore
    if tokens_used <= 0:
        return
    credits_used = (tokens_used + TOKENS_PER_CREDIT - 1) // TOKENS_PER_CREDIT if TOKENS_PER_CREDIT > 0 else tokens_used
    if credits_used <= 0:
        return
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    current = int(doc.to_dict().get("credits", 0)) if doc.exists else 0
    new_credits = max(0, current - credits_used)
    user_ref.set({"credits": new_credits, "updatedAt": _fstore.SERVER_TIMESTAMP}, merge=True)
    usage_ref = db.collection("usage_log").document()
    usage_ref.set({
        "userId": uid,
        "chatId": chat_id,
        "tokensUsed": tokens_used,
        "creditsUsed": credits_used,
        "createdAt": _fstore.SERVER_TIMESTAMP,
    })
    log.info("Usage recorded: uid=%s chatId=%s credits=%s", uid, chat_id, credits_used)
    print(f"  [Credits] Chat {chat_id}: {credits_used} credits used (tokens: {tokens_used}) → {new_credits} remaining")


def _get_user_credits(db, uid: str) -> int:
    """Get current credits for user (default 0)."""
    try:
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return int(doc.to_dict().get("credits", 0))
    except Exception:
        pass
    return 0


@app.post("/api/checkout/session")
async def create_checkout_session(request: Request, body: CreateCheckoutBody):
    """Create Stripe Checkout session for credit purchase. Redirect user to session.url."""
    uid = await get_uid_from_token(request)
    if not STRIPE_SECRET:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    credits = STRIPE_PRICE_TO_CREDITS.get(body.priceCents)
    if credits is None:
        raise HTTPException(status_code=400, detail="Invalid price; use 2000, 5000, or 10000 cents")
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": body.priceCents,
                    "product_data": {
                        "name": f"Stock Sense — {credits:,} credits",
                        "description": "One-time credit recharge",
                    },
                },
                "quantity": 1,
            }],
            metadata={"userId": uid, "credits": str(credits), "priceCents": str(body.priceCents)},
            success_url=f"{FRONTEND_URL}/profile?success=1",
            cancel_url=f"{FRONTEND_URL}/pricing?canceled=1",
        )
        return {"url": session.url, "sessionId": session.id}
    except Exception as e:
        log.exception("Stripe checkout create failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not create checkout session")


async def _handle_stripe_webhook(request: Request):
    """Stripe webhook: on checkout.session.completed, add credits and log payment."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        log.warning("Stripe webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")
    if event["type"] != "checkout.session.completed":
        return JSONResponse(content={"received": True})
    session = event["data"]["object"]
    uid = session.get("metadata", {}).get("userId")
    if not uid:
        log.warning("Webhook: no userId in session metadata")
        return JSONResponse(content={"received": True})
    try:
        credits_str = session.get("metadata", {}).get("credits", "0")
        credits = int(credits_str)
    except Exception:
        credits = 0
    amount_total = session.get("amount_total") or 0
    session_id = session.get("id", "")
    _, db = _get_firebase()
    if db is None:
        log.warning("Webhook: Firestore not configured, skipping credit grant")
        return JSONResponse(content={"received": True})
    from firebase_admin import firestore as _fstore
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    current = int(doc.to_dict().get("credits", 0)) if doc.exists else 0
    user_ref.set({"credits": current + credits, "updatedAt": _fstore.SERVER_TIMESTAMP}, merge=True)
    db.collection("payments").document(session_id).set({
        "userId": uid,
        "amountCents": amount_total,
        "credits": credits,
        "stripeSessionId": session_id,
        "createdAt": _fstore.SERVER_TIMESTAMP,
    }, merge=True)
    log.info("Credits granted: uid=%s credits=%s", uid, credits)
    return JSONResponse(content={"received": True})


@app.post("/api/stripe/webhook")
async def stripe_webhook_api(request: Request):
    return await _handle_stripe_webhook(request)


@app.post("/webhook")
async def stripe_webhook_short(request: Request):
    """Stripe webhook at /webhook so ngrok URL https://xxx.ngrok-free.app/webhook works."""
    return await _handle_stripe_webhook(request)


@app.get("/api/me")
async def get_me(request: Request):
    """Return current user profile and credits."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    doc = db.collection("users").document(uid).get()
    data = doc.to_dict() if doc.exists else {}
    credits = int(data.get("credits", 0))
    return {
        "uid": uid,
        "email": data.get("email", ""),
        "displayName": data.get("displayName", ""),
        "credits": credits,
    }


@app.get("/api/me/transactions")
async def get_my_transactions(request: Request):
    """List past payments for the current user."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    from google.cloud.firestore_v1 import FieldFilter
    try:
        query = db.collection("payments").where(filter=FieldFilter("userId", "==", uid)).order_by("createdAt", direction=_fstore.Query.DESCENDING).limit(50)
        docs = list(query.stream())
    except Exception as e:
        log.warning("Payments query failed (index may be needed): %s", e)
        docs = []
    out = []
    for doc in docs:
        d = doc.to_dict()
        created = d.get("createdAt")
        out.append({
            "id": doc.id,
            "amountCents": d.get("amountCents", 0),
            "credits": d.get("credits", 0),
            "createdAt": getattr(created, "isoformat", lambda: str(created))() if created else None,
        })
    return {"transactions": out}


@app.post("/api/usage")
async def record_usage(request: Request, body: RecordUsageBody):
    """Record chat token usage, deduct credits from user, and log for usage graph."""
    log.info("POST /api/usage received: chatId=%s tokensUsed=%s", body.chatId, body.tokensUsed)
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    chat_ref = db.collection("chats").document(body.chatId)
    chat_doc = chat_ref.get()
    if not chat_doc.exists or chat_doc.to_dict().get("userId") != uid:
        raise HTTPException(status_code=404, detail="Chat not found")
    tokens_used = max(0, body.tokensUsed)
    credits_used = (tokens_used + TOKENS_PER_CREDIT - 1) // TOKENS_PER_CREDIT if TOKENS_PER_CREDIT > 0 else tokens_used
    if credits_used <= 0:
        remaining = _get_user_credits(db, uid)
        print(f"  [Credits] Chat {body.chatId}: 0 credits (no deduction) → {remaining} remaining")
        return {"ok": True, "creditsUsed": 0, "creditsRemaining": remaining}
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    current = int(doc.to_dict().get("credits", 0)) if doc.exists else 0
    if current < credits_used:
        return JSONResponse(
            content={"detail": "Insufficient credits", "credits": current, "required": credits_used},
            status_code=402,
        )
    new_credits = current - credits_used
    user_ref.set({"credits": new_credits, "updatedAt": _fstore.SERVER_TIMESTAMP}, merge=True)
    usage_ref = db.collection("usage_log").document()
    usage_ref.set({
        "userId": uid,
        "chatId": body.chatId,
        "tokensUsed": tokens_used,
        "creditsUsed": credits_used,
        "createdAt": _fstore.SERVER_TIMESTAMP,
    })
    chat_ref.update({"updatedAt": _fstore.SERVER_TIMESTAMP})
    log.info("Usage recorded: uid=%s chatId=%s credits=%s", uid, body.chatId, credits_used)
    print(f"  [Credits] Chat {body.chatId}: {credits_used} credits used (tokens: {tokens_used}) → {new_credits} remaining")
    return {"ok": True, "creditsUsed": credits_used, "creditsRemaining": new_credits}


@app.get("/api/me/usage")
async def get_my_usage(request: Request, period: str = "30d"):
    """Return credits used per day for the last 7 or 30 days (for graph)."""
    uid = await get_uid_from_token(request)
    _, db = _get_firebase()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    from firebase_admin import firestore as _fstore
    from google.cloud.firestore_v1 import FieldFilter
    days = 30 if period == "30d" else 7
    since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        query = (
            db.collection("usage_log")
            .where(filter=FieldFilter("userId", "==", uid))
            .where(filter=FieldFilter("createdAt", ">=", since))
            .limit(500)
        )
        docs = list(query.stream())
    except Exception as e:
        log.warning("Usage query failed (index may be needed): %s", e)
        docs = []
    by_day = {}
    for doc in docs:
        d = doc.to_dict()
        created = d.get("createdAt")
        if hasattr(created, "date"):
            day_key = created.date().isoformat()
        elif created:
            try:
                if hasattr(created, "isoformat"):
                    day_key = created.isoformat()[:10]
                else:
                    day_key = str(created)[:10]
            except Exception:
                day_key = "unknown"
        else:
            continue
        by_day[day_key] = by_day.get(day_key, 0) + int(d.get("creditsUsed", 0))
    dates = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        dates.append({"date": d.isoformat(), "creditsUsed": by_day.get(d.isoformat(), 0)})
    return {"usage": dates, "period": period}


# Minimum credits required to make a chat request (typical response ~500+ tokens)
MIN_CREDITS_TO_CHAT = int(os.getenv("MIN_CREDITS_TO_CHAT", "100"))


@app.post("/v1/chat/completions")
async def chat_completions_proxy(request: Request):
    """Proxy chat completions to rakeshent, but block if user has insufficient credits."""
    try:
        uid = await get_uid_from_token(request)
    except HTTPException:
        return JSONResponse(
            content={"detail": "Authentication required"},
            status_code=401,
        )
    _, db = _get_firebase()
    if db is None:
        return JSONResponse(content={"detail": "Database not configured"}, status_code=503)
    credits = _get_user_credits(db, uid)
    if credits < MIN_CREDITS_TO_CHAT:
        return JSONResponse(
            content={"detail": "Insufficient credits", "credits": credits, "required": MIN_CREDITS_TO_CHAT},
            status_code=402,
        )
    # Proxy to rakeshent
    path_norm = "v1/chat/completions"
    url = f"{STOCK_GITA_BASE}/{path_norm}"
    if request.url.query:
        url = f"{url}?{request.url.query}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "connection", "transfer-encoding")}
    body = await request.body()
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.request(request.method, url, headers=headers, content=body)
        except httpx.RequestError as e:
            log.exception("Proxy error to %s: %s", url, e)
            return Response(content=f"Proxy error: {str(e)}", status_code=502, media_type="text/plain")
    out_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in ("transfer-encoding", "content-encoding", "connection", "content-length")
    }
    if resp.headers.get("content-type", "").startswith("text/event-stream"):
        async def stream():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(stream(), status_code=resp.status_code, headers=out_headers, media_type=resp.headers.get("content-type"))
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=out_headers,
        media_type=resp.headers.get("content-type", "application/octet-stream"),
    )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_rakeshent(path: str, request: Request):
    """Forward all other requests to StockSense backend at rakeshent.info."""
    path_norm = path.strip("/")
    url = f"{STOCK_GITA_BASE}/{path_norm}" if path_norm else STOCK_GITA_BASE
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "connection", "transfer-encoding")}
    body = await request.body()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.request(request.method, url, headers=headers, content=body)
        except httpx.RequestError as e:
            log.exception("Proxy error to %s: %s", url, e)
            return Response(content=f"Proxy error: {str(e)}", status_code=502, media_type="text/plain")

    out_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in ("transfer-encoding", "content-encoding", "connection", "content-length")
    }

    if resp.headers.get("content-type", "").startswith("text/event-stream"):
        async def stream():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(stream(), status_code=resp.status_code, headers=out_headers, media_type=resp.headers.get("content-type"))

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=out_headers,
        media_type=resp.headers.get("content-type", "application/octet-stream"),
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
