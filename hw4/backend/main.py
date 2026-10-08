"""Campus Customs API: products, authentication, sessions, chat history and the chat endpoint.

Run from this folder:  uvicorn main:app --reload --port 8000

Besides the endpoints, this file holds the database helpers the API needs:
the schema it adds (`sessions`), the corrections to three catalogue rows, the session tokens and
the saved chat history of logged-in customers.
"""

import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
from contextlib import asynccontextmanager, closing

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import (
    AgentUnavailableError,
    ChatDeps,
    ContentFilteredError,
    record_audit_event,
    run_chat,
    screen_message,
)
from models import (
    MAX_HISTORY_TURNS,
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    ChatTurn,
    ComparedProduct,
    CustomerInfo,
    LoginRequest,
    Product,
    RegisterRequest,
    UserOut,
)
from tools import (
    CATEGORIES,
    PRODUCTS_DIR,
    clean_size,
    comparison_for,
    get_connection,
    load_products,
    product_cards,
    to_card,
    viewed_product,
)

logger = logging.getLogger("campus_customs")


# --- Database: corrections to the seed catalogue -----------------------------
# Three products in the original `catalogue` table were left with placeholder data from a failed
# image analysis: the description reads "Vision blocked; filename-based stub.", `colors` is an
# empty list, `search_tags` are words split from the file name and `garment_type` is a bare word
# from the file name. The values below are the real ones, written from the product photos.
#
# `apply_catalogue_fixes()` runs when the API starts (see `init_db`). It only touches a row that
# still has the placeholder description, so it changes nothing in a database that is already
# fixed, and running it again is harmless. Nothing else in the catalogue is touched.

STUB_MARKER = "Vision blocked"

CATALOGUE_FIXES: dict[str, dict[str, object]] = {
    "benjamin-franklin-t-shirt": {
        "garment_type": "short-sleeve T-shirt",
        "description": "Heather gray short-sleeve crew-neck T-shirt featuring a large centered Benjamin Franklin College crest, a blue and red quartered shield with white lightning-bolt stripes and fleur-de-lis, above BENJAMIN FRANKLIN COLLEGE in black serif capitals.",
        "colors": ["heather gray", "blue", "red", "white", "black"],
        "search_tags": ["Benjamin Franklin College", "Yale", "T-shirt", "short sleeve", "gray T-shirt", "heather gray", "college crest", "shield logo", "center chest graphic", "college merch", "Campus Customs"],
    },
    "berkeley-sweater-fleece-jacket": {
        "garment_type": "full-zip fleece jacket",
        "description": "Light heather gray sweater-fleece jacket with a full-length dark gray zipper, stand collar, zippered hand pockets, dark gray trim, and a small red Berkeley shield crest with BERKELEY text on the left chest.",
        "colors": ["heather gray", "dark gray", "red"],
        "search_tags": ["Berkeley", "Berkeley College", "Yale", "fleece jacket", "sweater fleece", "full zip", "gray jacket", "heather gray", "stand collar", "zippered pockets", "red crest", "left chest logo", "Campus Customs"],
    },
    "timothy-dwight-college-crewneck": {
        "garment_type": "crewneck sweatshirt",
        "description": "Heather gray long-sleeve crewneck sweatshirt with ribbed collar, cuffs, and waistband. Features a small Timothy Dwight College crest, a red shield with a lion and crescent, and TIMOTHY DWIGHT text on the left chest.",
        "colors": ["heather gray", "red", "black", "white"],
        "search_tags": ["Timothy Dwight College", "Yale", "crewneck", "sweatshirt", "gray sweatshirt", "heather gray", "college crest", "left chest logo", "college merch", "campus apparel", "long sleeve", "Campus Customs"],
    },
}


def apply_catalogue_fixes(conn: sqlite3.Connection) -> int:
    """Replace the placeholder data of the three products; returns how many rows were changed."""
    changed = 0
    with conn:
        for product_id, fix in CATALOGUE_FIXES.items():
            cursor = conn.execute(
                "UPDATE catalogue SET garment_type = ?, description = ?, colors = ?, search_tags = ? "
                "WHERE product_id = ? AND description LIKE ?",
                (
                    fix["garment_type"],
                    fix["description"],
                    json.dumps(fix["colors"]),
                    json.dumps(fix["search_tags"]),
                    product_id,
                    f"%{STUB_MARKER}%",
                ),
            )
            changed += cursor.rowcount
    return changed


# --- Database: session settings and the tables the API adds ------------------

SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
MAX_DISPLAY_MESSAGES = 50  # most past messages shown when the chat widget loads

# `chat_messages` already exists in the seed database with exactly this schema; creating it
# only matters for a fresh database. `sessions` is new.
SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    products_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def init_db() -> None:
    with closing(get_connection(write=True)) as conn:
        conn.executescript(SCHEMA)
        apply_catalogue_fixes(conn)  # only rows that still hold the seed's placeholder text


# --- Session tokens (database helpers) ------------------------------------


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: int) -> str:
    """Start a session and return its token. Only a hash of the token is stored."""
    token = secrets.token_urlsafe(32)
    with closing(get_connection(write=True)) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at)"
            " VALUES (?, ?, datetime('now', ?))",
            (_hash_token(token), user_id, f"+{SESSION_DAYS} days"),
        )
    return token


def user_for_token(token: str | None) -> UserOut | None:
    """The user a valid, unexpired session token belongs to, or None."""
    if not token:
        return None
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT u.id, u.name, u.email, u.first_name, u.last_name"
            " FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token_hash = ? AND s.expires_at > datetime('now')",
            (_hash_token(token),),
        ).fetchone()
    if row is None:
        return None
    first, last = row["first_name"], row["last_name"]
    if not first and not last:  # older accounts without split names: fall back to `name`
        first, _, last = (row["name"] or "").partition(" ")
    return UserOut(id=row["id"], first_name=first or None, last_name=last or None, email=row["email"])


def delete_session(token: str | None) -> None:
    if not token:
        return
    with closing(get_connection(write=True)) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


# --- Saved chat history (database helpers) --------------------------------
# Logged-in customers' messages are saved to the `chat_messages` table (one row per message).
# Guests have no session and nothing about a guest conversation is written to the database.


def save_exchange(
    user_id: int,
    user_text: str,
    reply: str,
    product_ids: list[str],
    compare_ids: list[str] | None = None,
    size: str | None = None,
) -> None:
    """Save one question and its answer for a logged-in customer, in a single transaction.

    products_json is a list of {"product_id": ...}. Products that were shown in a comparison
    table also carry "compare": true, so the table can be restored, and when the shopper asked
    about a size every entry carries "size", so the badges can be rebuilt for that size. Readers
    that only look at product_id (and older rows) are unaffected.
    """
    entries = [{"product_id": pid} for pid in product_ids]
    entries += [{"product_id": pid, "compare": True} for pid in compare_ids or []]
    if size:
        entries = [{**e, "size": size} for e in entries]
    products_json = json.dumps(entries) if entries else None
    with closing(get_connection(write=True)) as conn, conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, user_text),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json)"
            " VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )


def _latest_rows(user_id: int, limit: int) -> list[sqlite3.Row]:
    """The customer's most recent messages, oldest first."""
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT * FROM ("
            "  SELECT id, role, content, products_json, created_at FROM chat_messages"
            "  WHERE user_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT ?"
            ") ORDER BY id ASC",
            (user_id, limit),
        ).fetchall()


def recent_turns(user_id: int, limit: int = MAX_HISTORY_TURNS) -> list[ChatTurn]:
    """The customer's latest messages as plain text, to give the agent its memory of them."""
    return [ChatTurn(role=r["role"], content=r["content"][:2000]) for r in _latest_rows(user_id, limit)]


def _product_ids(products_json: str | None) -> tuple[list[str], list[str], str | None]:
    """(card ids, comparison ids, size) from a stored products_json (ours is a list of
    {"product_id": ..., "compare": true?, "size": ...?}; older rows hold whole product objects).
    Only the ids and the size are used, so cards and tables are always rebuilt from the
    current catalogue."""
    if not products_json:
        return [], [], None
    try:
        entries = json.loads(products_json)
    except ValueError:
        return [], [], None
    cards: list[str] = []
    compared: list[str] = []
    size: str | None = None
    for entry in entries if isinstance(entries, list) else []:
        pid = entry.get("product_id") if isinstance(entry, dict) else entry
        if not isinstance(pid, str):
            continue
        if isinstance(entry, dict) and isinstance(entry.get("size"), str):
            size = entry["size"]
        is_compare = isinstance(entry, dict) and entry.get("compare") is True
        (compared if is_compare else cards).append(pid)
    return cards, compared, size


def history_for_display(user_id: int, limit: int = MAX_DISPLAY_MESSAGES) -> list[ChatHistoryMessage]:
    catalogue = {p.product_id: p for p in load_products()}  # one catalogue read for all rows
    messages = []
    for r in _latest_rows(user_id, limit):
        card_ids, compare_ids, size = _product_ids(r["products_json"])
        compared = [
            ComparedProduct(**to_card(catalogue[pid], size).model_dump(), details=catalogue[pid].description)
            for pid in dict.fromkeys(compare_ids)
            if pid in catalogue
        ]
        messages.append(
            ChatHistoryMessage(
                role=r["role"],
                content=r["content"],
                products=[to_card(catalogue[pid], size) for pid in dict.fromkeys(card_ids) if pid in catalogue],
                comparison=compared if len(compared) >= 2 else [],
                created_at=r["created_at"],
            )
        )
    return messages


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # creates the sessions table (and chat_messages if missing); no-op otherwise
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos are served at /media/<file>, matching catalogue.image_file_path
# ("products/<file>") once the "products/" prefix is replaced by "/media/".
app.mount("/media", StaticFiles(directory=PRODUCTS_DIR), name="media")


# --- Products -------------------------------------------------------------


@app.get("/api/products", response_model=list[Product])
def list_products() -> list[Product]:
    # Grouped by shop section (in the section order), then by name within a section.
    return sorted(load_products(), key=lambda p: (CATEGORIES.index(p.category), p.name))


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    products = load_products(product_id)
    if not products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[0]


# --- Session endpoints ----------------------------------------------------
# Who is logged in is decided here, from an HttpOnly cookie holding a random session token
# (only its hash is stored). The browser is never trusted to say who it is.


def current_user(request: Request) -> UserOut | None:
    return user_for_token(request.cookies.get(SESSION_COOKIE))


def start_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session(user_id),
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True,  # not readable from JavaScript
        samesite="lax",  # not sent on cross-site requests
        path="/",
    )


@app.get("/api/me", response_model=UserOut | None)
def me(user: UserOut | None = Depends(current_user)) -> UserOut | None:
    """The logged-in user, or null for a guest."""
    return user


@app.post("/api/logout", status_code=204)
def logout(request: Request) -> Response:
    delete_session(request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


# --- Chat -----------------------------------------------------------------


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(user: UserOut | None = Depends(current_user)) -> list[ChatHistoryMessage]:
    """The logged-in customer's saved conversation, oldest first. Guests have none."""
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see your chat history.")
    return history_for_display(user.id)


def _save_exchange(
    user_id: int,
    question: str,
    reply: str,
    card_ids: list[str],
    compare_ids: list[str],
    size: str | None = None,
) -> None:
    try:
        save_exchange(user_id, question, reply, card_ids, compare_ids, size)
    except Exception:  # a failed save must not lose the answer the shopper is waiting for
        logger.exception("Could not save chat history")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, user: UserOut | None = Depends(current_user)
) -> ChatResponse:
    # What the agent is told about this conversation. The customer comes from the session and
    # the viewed product is looked up by id in the database; neither is taken from the request.
    deps = ChatDeps(
        customer=(
            CustomerInfo(
                first_name=user.first_name or "", last_name=user.last_name or "", email=user.email
            )
            if user
            else None
        ),
        page_view=request.page.view if request.page else "other",
        viewed_product=viewed_product(request.page),
    )
    # Safety check: clear-cut prompt-injection attempts and requests unrelated to the shop get a
    # polite reply without calling the model. Anything subtler is handled by the prompt rules.
    blocked = screen_message(request.message)
    if blocked is not None:
        logger.info("Chat message screened out (%s)", blocked.category)
        record_audit_event(
            "safety_precheck",
            {"category": blocked.category, "message_chars": len(request.message)},
            "message not sent to the model; the shopper got a polite decline",
            f"blocked_{blocked.category}",
        )
        if user:
            _save_exchange(user.id, request.message, blocked.reply, [], [])
        return ChatResponse(reply=blocked.reply)

    # A logged-in customer's memory is the history saved on the server, so the browser's copy is
    # ignored. A guest's earlier turns come from the browser, and nothing is saved.
    history = recent_turns(user.id) if user else request.history
    try:
        output = await run_chat(request.message, history, deps)
    except AgentUnavailableError:
        raise HTTPException(
            status_code=503, detail="The chat assistant is not configured on this server."
        )
    except ContentFilteredError:
        # Not an outage: the provider's safety filter declined this message. Retrying won't help.
        return ChatResponse(
            reply=(
                "Sorry, I can't help with that one. I'm happy to help you find Campus Customs "
                "gear, check sizes or see what's in stock!"
            )
        )
    except Exception:
        # Details go to the server log only; the shopper gets a generic message.
        logger.exception("Chat agent failed")
        raise HTTPException(
            status_code=502, detail="The assistant could not answer right now. Please try again."
        )
    # Cards are rebuilt from the database, so the agent can only show real products.
    # When the shopper asked about a size, the badges are for that size. The agent only names
    # the size; the status itself is worked out here from the real inventory.
    size = clean_size(output.size)
    # A comparison replaces the cards: the same products are not shown twice.
    comparison = comparison_for(output.compare_product_ids, size)
    cards = [] if comparison else product_cards(output.product_ids, size)
    if user:
        _save_exchange(
            user.id,
            request.message,
            output.reply,
            [c.product_id for c in cards],
            [c.product_id for c in comparison],
            size,
        )
    return ChatResponse(reply=output.reply, products=cards, comparison=comparison)


# --- Authentication -------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash (the salt and cost factor are embedded in the result)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


# The seeded accounts store "pbkdf2_sha256$<salt>$<hex digest>" (PBKDF2-HMAC-SHA256,
# 120,000 iterations, salt used as UTF-8 text). They are verified but never created.
SEED_SCHEME = "pbkdf2_sha256"
SEED_ITERATIONS = 120_000


def verify_seed_password(password: str, password_hash: str) -> bool:
    try:
        _, salt, digest = password_hash.split("$")
        expected = bytes.fromhex(digest)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), SEED_ITERATIONS
    )
    return hmac.compare_digest(actual, expected)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a stored hash, picking the scheme from the hash prefix."""
    if password_hash.startswith(SEED_SCHEME + "$"):
        return verify_seed_password(password, password_hash)
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Not a recognised hash, or a password longer than bcrypt's 72-byte limit.
        return False


# Checked when the email is unknown so a login attempt takes the same time either way.
DUMMY_HASH = hash_password("campus-customs-dummy-password")


@app.post("/api/register", response_model=UserOut, status_code=201)
def register(request: RegisterRequest, response: Response) -> UserOut:
    email = str(request.email).lower()
    password_hash = hash_password(request.password)
    duplicate = HTTPException(status_code=409, detail="An account with this email already exists.")
    try:
        with closing(get_connection(write=True)) as conn, conn:
            if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
                raise duplicate
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    f"{request.first_name} {request.last_name}",
                    email,
                    password_hash,
                    request.first_name,
                    request.last_name,
                ),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:  # lost a race with another registration of the same email
        raise duplicate
    start_session(response, user_id)  # a new account is logged in straight away
    return UserOut(
        id=user_id,
        first_name=request.first_name,
        last_name=request.last_name,
        email=email,
    )


@app.post("/api/login", response_model=UserOut)
def login(request: LoginRequest, response: Response) -> UserOut:
    email = request.email.strip().lower()
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash, first_name, last_name"
            " FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
    password_ok = verify_password(request.password, row["password_hash"] if row else DUMMY_HASH)
    if row is None or not password_ok:
        # Same message for an unknown email and a wrong password.
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    start_session(response, row["id"])
    return UserOut(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
    )
