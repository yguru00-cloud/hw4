"""Database access and the tools the chat agent calls.

Everything here is plain Python over data/campus_customs.db, so the REST endpoints
and the agent read products and stock through the same code. The three agent tools
(search_products, get_product_info, get_stock) are registered in agent.py as they are:
their signatures, type hints and docstrings are what the model sees.
"""

import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from models import (
    MAX_COMPARED_PRODUCTS,
    MAX_PRODUCT_CARDS,
    ComparedProduct,
    FitPreference,
    PageContext,
    Product,
    ProductCard,
    ProductInfo,
    ProductLookup,
    ProductMatch,
    ProductSearchResult,
    SizeOption,
    SizeRecommendation,
    StockInfo,
    StockLookup,
    StockStatus,
    ViewedProduct,
)

ROOT = Path(__file__).resolve().parent.parent
# CAMPUS_DB_PATH lets tests point the API at a copy of the database.
DB_PATH = Path(os.environ.get("CAMPUS_DB_PATH") or ROOT / "data" / "campus_customs.db")
PRODUCTS_DIR = ROOT / "data" / "products"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

MAX_SEARCH_RESULTS = MAX_PRODUCT_CARDS  # a search can return as many products as a reply can show
SUMMARY_MAX_CHARS = 110
LOW_STOCK_UNITS = 30  # a product with this many units or fewer in all sizes is "low stock"
LOW_SIZE_UNITS = 5  # one size with this many units or fewer is "low stock"


# --- Database -------------------------------------------------------------


def get_connection(write: bool = False) -> sqlite3.Connection:
    if write:
        conn = sqlite3.connect(DB_PATH, timeout=10)
    else:
        conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# The shop sections, in the order they appear on the Products page.
CATEGORIES = [
    "Hoodies",
    "Crewnecks & Sweatshirts",
    "T-Shirts",
    "Quarter-Zips",
    "Jackets & Fleece",
    "Performance Tops",
]


def categorize(garment_type: str) -> str:
    """The shop section for a catalogue garment_type.

    garment_type is free text with many spellings ("hoodie", "pullover hoodie", "hooded
    sweatshirt"...), so it is matched by keyword. The order of the checks matters: a "full-zip
    hooded sweatshirt" is a hoodie, not a jacket. The product's name is deliberately ignored,
    because a name can be wrong while the type is right (the "School Of Architecture Crewneck"
    is really a quarter-zip).
    """
    t = garment_type.lower()
    if "hood" in t:
        return "Hoodies"
    if "quarter-zip" in t or "quarter zip" in t:
        return "Quarter-Zips"
    if "jacket" in t or "fleece" in t:
        return "Jackets & Fleece"
    if "t-shirt" in t or "tee" in t.split():
        return "T-Shirts"
    if "performance" in t:
        return "Performance Tops"
    return "Crewnecks & Sweatshirts"


def build_product(row: sqlite3.Row, inventory: list[sqlite3.Row]) -> Product:
    sizes = sorted(
        ({"size": r["size"], "quantity": r["quantity"]} for r in inventory),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER),
    )
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image_url="/media/" + row["image_file_path"].removeprefix("products/"),
        price=row["price"],
        inventory=sizes,
        total_stock=sum(s["quantity"] for s in sizes),
        stock_status=stock_status(sum(s["quantity"] for s in sizes)),
        category=categorize(row["garment_type"]),
    )


def load_products(product_id: str | None = None) -> list[Product]:
    with closing(get_connection()) as conn:
        if product_id is None:
            rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
            ).fetchall()
        stock: dict[str, list[sqlite3.Row]] = {}
        for inv in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            stock.setdefault(inv["product_id"], []).append(inv)
    return [build_product(r, stock.get(r["product_id"], [])) for r in rows]


# --- Product cards --------------------------------------------------------


def make_summary(description: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    """A one-line summary of a description: its first sentence, cut at a word if too long."""
    text = " ".join(description.split())
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    if len(first) <= max_chars:
        return first
    head = first[: max_chars - 1]
    comma = head.rfind(",")
    # Prefer ending at a comma (a whole clause) over ending mid-phrase.
    cut = head[:comma] if comma >= max_chars // 2 else head.rsplit(" ", 1)[0]
    return cut.rstrip(",;:- ") + "…"


def stock_status(units: int, low_at: int = LOW_STOCK_UNITS) -> StockStatus:
    """Availability from real stock: none, a few (`low_at` or fewer), or plenty."""
    if units <= 0:
        return "out_of_stock"
    return "low_stock" if units <= low_at else "in_stock"


def to_card(product: Product, size: str | None = None) -> ProductCard:
    """A card for the product. With a `size` the stock status is for that size (so a hoodie that
    is sold out in XL shows Out of Stock when the shopper asks about XL); without one it is for
    the whole product."""
    in_stock = [s.size for s in product.inventory if s.quantity > 0]
    quantities = {s.size: s.quantity for s in product.inventory}
    asked = size if size in quantities else None
    if asked is not None:
        status = stock_status(quantities[asked], LOW_SIZE_UNITS)
    else:
        status = stock_status(product.total_stock)
    return ProductCard(
        product_id=product.product_id,
        name=product.name,
        price=product.price,
        image_url=product.image_url,
        summary=make_summary(product.description),
        garment_type=product.garment_type,
        colors=product.colors,
        sizes_in_stock=in_stock,
        in_stock=bool(in_stock),
        total_stock=product.total_stock,
        size=asked,
        size_stock=quantities[asked] if asked is not None else None,
        stock_status=status,
    )


def comparison_for(product_ids: list[str], size: str | None = None) -> list[ComparedProduct]:
    """Columns for a comparison table, in the order given, built from the database.

    Unknown and repeated ids are dropped. A comparison needs at least two products, so with
    fewer the result is empty.
    """
    by_id = {p.product_id: p for p in load_products()}
    columns: list[ComparedProduct] = []
    for pid in dict.fromkeys(product_ids):
        product = by_id.get(pid)
        if product is not None:
            columns.append(
                ComparedProduct(**to_card(product, size).model_dump(), details=product.description)
            )
    return columns[:MAX_COMPARED_PRODUCTS] if len(columns) >= 2 else []


def product_cards(product_ids: list[str], size: str | None = None) -> list[ProductCard]:
    """Cards for the given ids, in order. Unknown or repeated ids are dropped. With a `size`
    each card's stock status is for that size."""
    by_id = {p.product_id: p for p in load_products()}
    cards: list[ProductCard] = []
    for pid in dict.fromkeys(product_ids):
        if pid in by_id:
            cards.append(to_card(by_id[pid], size))
    return cards


def clean_size(size: str | None) -> str | None:
    """A size the agent reported ("XL", "medium", "extra large") as XS to XXL, or None."""
    return normalize_size(size) if size and size.strip() else None


def viewed_product(page: PageContext | None) -> ViewedProduct | None:
    """The product page the shopper has open, looked up in the database by id.

    The browser only supplies the id. Anything it claims about the product is ignored, and an
    unknown id (or a page that is not a product page) means no product is open.
    """
    if page is None or page.view != "product" or not page.product_id:
        return None
    products = load_products(page.product_id)
    if not products:
        return None
    product = products[0]
    return ViewedProduct(
        product_id=product.product_id,
        name=product.name,
        garment_type=product.garment_type,
        colors=product.colors,
        summary=make_summary(product.description),
    )


# --- Search helpers -------------------------------------------------------

STOP_WORDS = {
    "a", "an", "the", "i", "you", "we", "me", "my", "do", "does", "have", "has", "any", "some",
    "for", "in", "on", "of", "to", "and", "or", "with", "is", "are", "it", "this", "that", "show",
    "what", "which", "looking", "want", "need", "please", "can", "get", "find", "your", "yale",
}

SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x-small": "XS",
    "s": "S", "small": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "double extra large": "XXL",
}


def _stem(word: str) -> str:
    """Crude plural handling so "hoodies" matches "hoodie" and "shirts" matches "shirt"."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _tokens(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())} - STOP_WORDS


def normalize_size(size: str) -> str | None:
    return SIZE_ALIASES.get(size.strip().lower())


def _score(product: Product, query_tokens: set[str]) -> int:
    weighted = [
        (_tokens(product.name), 3),
        (_tokens(product.garment_type), 3),
        (_tokens(" ".join(product.search_tags)), 2),
        (_tokens(" ".join(product.colors)), 2),
        (_tokens(product.description), 1),
    ]
    return sum(weight * len(query_tokens & tokens) for tokens, weight in weighted)


# --- Agent tools ----------------------------------------------------------


def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
) -> ProductSearchResult:
    """Find products in the Campus Customs catalogue; best matches first (at most 12).

    Use this whenever the shopper asks about a type of item, a team, a color or a price range.
    It tells you which products exist and gives their product_id. total_matches is how many
    products matched in all, which can be more than the number returned. Results do NOT
    include prices or stock: call get_product_info and get_stock for those.

    Args:
        query: Keywords such as a team, sport, college or style ("baseball", "bulldog").
        garment_type: Kind of item, such as "hoodie", "crewneck", "t-shirt", "quarter-zip"
            or "fleece jacket".
        color: A color word the product must come in, such as "navy" or "gray".
        max_price: Only products priced at or below this many US dollars.
        in_stock_only: Only products with at least one unit in stock in some size.
    """
    query_tokens = _tokens(query)
    type_tokens = _tokens(garment_type) if garment_type else set()
    color_tokens = _tokens(color) if color else set()

    scored: list[tuple[int, Product]] = []
    for product in load_products():
        if type_tokens and not type_tokens <= _tokens(product.garment_type + " " + product.name):
            continue
        if color_tokens and not color_tokens <= _tokens(" ".join(product.colors)):
            continue
        if max_price is not None and product.price > max_price:
            continue
        if in_stock_only and product.total_stock == 0:
            continue
        score = _score(product, query_tokens) if query_tokens else 0
        if query_tokens and score == 0:
            continue
        scored.append((score, product))

    # Highest score first, then alphabetical (load_products is already name-ordered).
    scored.sort(key=lambda pair: -pair[0])
    return ProductSearchResult(
        total_matches=len(scored),
        products=[
            ProductMatch(
                product_id=p.product_id, name=p.name, garment_type=p.garment_type, colors=p.colors
            )
            for _, p in scored[:MAX_SEARCH_RESULTS]
        ],
    )


def get_product_info(product_id: str) -> ProductLookup:
    """Look up the real description and price of one product in the database.

    Call this before stating any price or describing a product. If found is false there is no
    such product: say so, and do not guess its price or details.

    Args:
        product_id: The product_id from search_products, e.g. "basic-hoodie-big-yale".
    """
    products = load_products(product_id)
    if not products:
        return ProductLookup(
            found=False,
            message=(
                f"No product has the id '{product_id}'. Use search_products to find a valid "
                "product_id. Do not guess a price or description."
            ),
        )
    product = products[0]
    return ProductLookup(
        found=True,
        product=ProductInfo(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            price=product.price,
        ),
    )


def get_stock(product_id: str, size: str | None = None) -> StockLookup:
    """Look up how many units of a product are in stock, from the inventory table.

    Call this before saying anything about availability, sizes or quantities. Give a size
    (XS, S, M, L, XL or XXL; "medium" and "extra large" also work) to check that size, or
    leave it out to get every size. A quantity of 0 means sold out. Read the message field:
    it states the outcome, including sold-out sizes and sizes the product does not come in.

    Args:
        product_id: The product_id from search_products, e.g. "basic-hoodie-big-yale".
        size: The size to check. Omit it to see all sizes.
    """
    products = load_products(product_id)
    if not products:
        return StockLookup(
            found=False,
            product_id=product_id,
            message=(
                f"No product has the id '{product_id}', so there is no stock information. "
                "Use search_products to find a valid product_id. Do not guess quantities."
            ),
        )
    product = products[0]
    all_sizes = [
        StockInfo(
            product_id=product.product_id,
            size=s.size,
            quantity=s.quantity,
            is_in_stock=s.quantity > 0,
        )
        for s in product.inventory
    ]
    if not all_sizes:
        return StockLookup(
            found=True,
            product_id=product.product_id,
            message=(
                f"{product.name} has no inventory records, so its stock is unknown. "
                "Do not state any quantity."
            ),
        )

    if size is None or not size.strip():
        available = [f"{s.size} ({s.quantity})" for s in all_sizes if s.is_in_stock]
        sold_out = [s.size for s in all_sizes if not s.is_in_stock]
        parts = [f"{product.name}: in stock: {', '.join(available) if available else 'none'}."]
        if sold_out:
            parts.append(f"Sold out (quantity 0): {', '.join(sold_out)}.")
        if not available:
            parts.append("Every size is sold out.")
        return StockLookup(
            found=True, product_id=product.product_id, stock=all_sizes, message=" ".join(parts)
        )

    normalized = normalize_size(size)
    match = next((s for s in all_sizes if s.size == normalized), None)
    if match is None:
        carried = ", ".join(s.size for s in all_sizes)
        return StockLookup(
            found=True,
            product_id=product.product_id,
            message=(
                f"{product.name} does not come in '{size}'. Sizes carried: {carried}. "
                "Do not guess a quantity for a size that is not carried."
            ),
        )
    if match.is_in_stock:
        message = f"{product.name}, size {match.size}: {match.quantity} in stock."
    else:
        message = f"{product.name}, size {match.size}: OUT OF STOCK (quantity 0)."
    return StockLookup(found=True, product_id=product.product_id, stock=[match], message=message)


# --- Size recommendation --------------------------------------------------
# The catalogue has no size chart or garment measurements, so this is general guidance for a
# typical adult unisex top (T-shirt, sweatshirt, hoodie, jacket), not a measured chart for any
# one product. Each row is the largest height and weight that still fits that size.
SIZE_BANDS: list[tuple[str, float, float]] = [
    ("XS", 160, 54),  # (size, max height in cm, max weight in kg)
    ("S", 168, 63),
    ("M", 176, 74),
    ("L", 183, 86),
    ("XL", 190, 100),
    ("XXL", float("inf"), float("inf")),
]
WEIGHT_SHARE = 0.6  # weight counts a little more than height when both are given
HEIGHT_RANGE_CM = (120.0, 230.0)
WEIGHT_RANGE_KG = (30.0, 220.0)
DISCLAIMER = (
    "This is general sizing guidance for a typical adult top, not a measured size chart for this "
    "product: Campus Customs does not list garment measurements."
)


def _to_cm(height: float, unit: str) -> float | None:
    unit = unit.strip().lower()
    if unit in ("cm", "centimeter", "centimeters", "centimetre", "centimetres"):
        return float(height)
    if unit in ("in", "inch", "inches", '"'):
        return float(height) * 2.54
    return None


def _to_kg(weight: float, unit: str) -> float | None:
    unit = unit.strip().lower()
    if unit in ("kg", "kgs", "kilogram", "kilograms"):
        return float(weight)
    if unit in ("lb", "lbs", "pound", "pounds"):
        return float(weight) * 0.45359237
    return None


def _band_index(value: float, which: int) -> int:
    """Index in SIZE_BANDS of the first size that still fits this height (1) or weight (2)."""
    for index, band in enumerate(SIZE_BANDS):
        if value <= band[which]:
            return index
    return len(SIZE_BANDS) - 1


def recommend_size(
    height: float | None = None,
    height_unit: str = "cm",
    weight: float | None = None,
    weight_unit: str = "kg",
    fit_preference: FitPreference = "regular",
    product_id: str | None = None,
) -> SizeRecommendation:
    """Suggest a size from the shopper's height and/or weight and how they like clothes to fit.

    Use this when the shopper asks what size to get. At least one of height or weight is
    needed; if both are missing, ask the shopper for them. The answer is general guidance,
    not a measured chart. Pass the product_id (for example from the open product page) to
    also get the real stock of the suggested size and the sizes next to it.

    Args:
        height: The shopper's height as a number, exactly as they said it (for example 180).
        height_unit: "cm" or "in" (inches). Pass 5'10" as 70 with "in".
        weight: The shopper's weight as a number, exactly as they said it.
        weight_unit: "kg" or "lb" (pounds).
        fit_preference: "fitted" (a closer fit, one size down), "regular", or "relaxed" (a
            looser fit, one size up).
        product_id: Optional product to check stock for.
    """
    if height is None and weight is None:
        return SizeRecommendation(
            fit_preference=fit_preference,
            needs_more_info=True,
            message=(
                "No measurements were given. Ask the shopper for their height and/or weight "
                "(either one is enough). Do not guess a size."
            ),
        )

    height_cm = weight_kg = None
    if height is not None:
        height_cm = _to_cm(height, height_unit)
        if height_cm is None:
            return SizeRecommendation(
                fit_preference=fit_preference,
                needs_more_info=True,
                message=f"Unknown height unit '{height_unit}'. Use 'cm' or 'in'.",
            )
        if not HEIGHT_RANGE_CM[0] <= height_cm <= HEIGHT_RANGE_CM[1]:
            return SizeRecommendation(
                fit_preference=fit_preference,
                needs_more_info=True,
                message=(
                    f"A height of {height:g} {height_unit} looks like a typo or the wrong unit. "
                    "Ask the shopper to check it. Do not guess a size."
                ),
            )
    if weight is not None:
        weight_kg = _to_kg(weight, weight_unit)
        if weight_kg is None:
            return SizeRecommendation(
                fit_preference=fit_preference,
                needs_more_info=True,
                message=f"Unknown weight unit '{weight_unit}'. Use 'kg' or 'lb'.",
            )
        if not WEIGHT_RANGE_KG[0] <= weight_kg <= WEIGHT_RANGE_KG[1]:
            return SizeRecommendation(
                fit_preference=fit_preference,
                needs_more_info=True,
                message=(
                    f"A weight of {weight:g} {weight_unit} looks like a typo or the wrong unit. "
                    "Ask the shopper to check it. Do not guess a size."
                ),
            )

    # Size from each measurement, then combine them (weight counts a little more).
    steps: list[str] = []
    height_index = weight_index = None
    if height_cm is not None:
        height_index = _band_index(height_cm, 1)
        steps.append(f"height {height:g} {height_unit} points to {SIZE_BANDS[height_index][0]}")
    if weight_kg is not None:
        weight_index = _band_index(weight_kg, 2)
        steps.append(f"weight {weight:g} {weight_unit} points to {SIZE_BANDS[weight_index][0]}")
    if height_index is not None and weight_index is not None:
        score = WEIGHT_SHARE * weight_index + (1 - WEIGHT_SHARE) * height_index
        base = int(score + 0.5)
        steps.append(f"combined (weight counts more) gives {SIZE_BANDS[base][0]}")
    else:
        base = height_index if height_index is not None else weight_index  # type: ignore[assignment]

    shift = {"fitted": -1, "regular": 0, "relaxed": 1}[fit_preference]
    index = max(0, min(len(SIZE_BANDS) - 1, base + shift))
    if shift and index != base + shift:
        steps.append(f"a {fit_preference} fit would move it past the end of the range, so it stays at {SIZE_BANDS[index][0]}")
    elif shift:
        steps.append(f"a {fit_preference} fit moves it {'down' if shift < 0 else 'up'} one size to {SIZE_BANDS[index][0]}")
    recommended = SIZE_BANDS[index][0]
    basis = "; ".join(steps) + "."

    result = SizeRecommendation(
        recommended_size=recommended,
        fit_preference=fit_preference,
        basis=basis,
        product_id=product_id,
        message=f"Suggested size: {recommended}. {DISCLAIMER}",
    )

    if product_id:
        products = load_products(product_id)
        if not products:
            result.message += f" (No product has the id '{product_id}', so stock was not checked.)"
            return result
        product = products[0]
        stock = {s.size: s.quantity for s in product.inventory}
        nearby = [SIZE_BANDS[i][0] for i in (index - 1, index, index + 1) if 0 <= i < len(SIZE_BANDS)]
        result.nearby_sizes = [
            SizeOption(size=s, quantity=stock.get(s, 0), is_in_stock=stock.get(s, 0) > 0)
            for s in nearby
        ]
        quantity = stock.get(recommended, 0)
        result.recommended_in_stock = quantity > 0
        if quantity > 0:
            result.message += f" {product.name} in {recommended}: {quantity} in stock."
        else:
            options = [f"{o.size} ({o.quantity})" for o in result.nearby_sizes if o.is_in_stock]
            result.message += (
                f" {product.name} in {recommended} is OUT OF STOCK (quantity 0)."
                + (f" In stock next to it: {', '.join(options)}." if options else
                   " The sizes next to it are sold out too.")
            )
    return result
