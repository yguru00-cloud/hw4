"""Pydantic types shared by the API, the database helpers and the chat agent."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# --- Products -------------------------------------------------------------

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class SizeStock(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    """A catalogue item joined with its per-size inventory (GET /api/products)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int
    stock_status: StockStatus = Field(
        description="in_stock, low_stock (30 units or fewer in all) or out_of_stock (none)."
    )
    category: str = Field(
        description="The shop section the product belongs to, such as Hoodies or T-Shirts."
    )


class ProductCard(BaseModel):
    """One matching product in a chat reply, shown as a card that opens the detail view.

    Everything here is read from the database, never written by the model. `product_id`
    is the key for the detail page (`/products/{product_id}`).
    """

    product_id: str
    name: str
    price: float
    image_url: str
    summary: str = Field(description="One short sentence about the product, from its description.")
    garment_type: str
    colors: list[str]
    sizes_in_stock: list[str]
    in_stock: bool
    total_stock: int = Field(description="Units in stock across all sizes.")
    size: str | None = Field(
        default=None,
        description="The size the shopper asked about, when they named one; stock_status is for it.",
    )
    size_stock: int | None = Field(
        default=None, description="Units in stock in `size`; None when no size was asked about."
    )
    stock_status: StockStatus = Field(
        description=(
            "Availability of `size` when one was asked about (out_of_stock at 0 units, low_stock "
            "at 5 or fewer), otherwise of the whole product (out_of_stock at 0 units, low_stock "
            "at 30 or fewer across all sizes)."
        )
    )


class ComparedProduct(ProductCard):
    """One column of a comparison table: a card plus the product's full description."""

    details: str = Field(description="The full product description (its features).")


# --- Agent tool outputs ---------------------------------------------------
# What the agent's database tools return. Every fact the agent states about a product,
# price or stock level has to come from one of these.
# product_id is a str slug (e.g. "basic-hoodie-big-yale") because that is how the
# catalogue and inventory tables identify products; there are no integer ids.


class ProductInfo(BaseModel):
    """Description and price of one product, straight from the catalogue table."""

    product_id: str
    name: str
    description: str
    price: float


class StockInfo(BaseModel):
    """Units in stock for one size of one product, straight from the inventory table."""

    product_id: str
    size: str
    quantity: int
    is_in_stock: bool


class ProductMatch(BaseModel):
    """A search hit. It deliberately has no price or stock: those come from the lookup tools."""

    product_id: str
    name: str
    garment_type: str
    colors: list[str]


class ProductSearchResult(BaseModel):
    """Result of search_products: the best matches plus how many products matched in all."""

    total_matches: int
    products: list[ProductMatch]


FitPreference = Literal["fitted", "regular", "relaxed"]


class SizeOption(BaseModel):
    size: str
    quantity: int
    is_in_stock: bool


class SizeRecommendation(BaseModel):
    """Result of recommend_size: a suggested size, how it was worked out, and (when a product
    was given) whether that size and the neighbouring ones are in stock."""

    recommended_size: str | None = None
    fit_preference: FitPreference = "regular"
    needs_more_info: bool = False
    basis: str = ""
    message: str
    product_id: str | None = None
    recommended_in_stock: bool | None = Field(
        default=None, description="None when no product was given, so stock was not checked."
    )
    nearby_sizes: list[SizeOption] = Field(
        default_factory=list,
        description="Real stock for the recommended size and the sizes next to it.",
    )


class ProductLookup(BaseModel):
    """Result of looking a product up by id; `found` is False when there is no such product."""

    found: bool
    product: ProductInfo | None = None
    message: str = ""


class StockLookup(BaseModel):
    """Result of a stock check.

    `stock` has one StockInfo per size asked about (every size when none was requested) and is
    empty when the product or the requested size does not exist. `message` always states the
    outcome in words, including sold-out sizes (quantity 0) and sizes that are not carried.
    """

    found: bool
    product_id: str
    stock: list[StockInfo] = Field(default_factory=list)
    message: str


# --- Authentication -------------------------------------------------------

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # bcrypt only uses the first 72 bytes, so longer passwords are rejected


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    email: str


# --- Chat -----------------------------------------------------------------

MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_TURNS = 20
MAX_PRODUCT_CARDS = 12  # most product cards one chat reply can carry
MAX_COMPARED_PRODUCTS = 4  # most products one comparison table can hold


class ChatTurn(BaseModel):
    """One earlier message in the conversation, sent back by the browser for context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


PageView = Literal["home", "products", "product", "about", "login", "register", "other"]


class PageContext(BaseModel):
    """Where the shopper is in the site when they send a chat message.

    The browser only says which page and which product id; the server looks the product up
    itself, so nothing in here is trusted as a fact about the product.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    view: PageView = "other"
    path: str = Field(default="", max_length=200)
    product_id: str | None = Field(default=None, max_length=100)


class CustomerInfo(BaseModel):
    """The logged-in customer details the agent is given. Nothing else about the account."""

    first_name: str
    last_name: str
    email: str


class ViewedProduct(BaseModel):
    """The product page the shopper has open, as looked up by the server (never client text)."""

    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    summary: str


class ChatHistoryMessage(BaseModel):
    """One saved message returned when a logged-in customer's chat history is loaded."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    comparison: list[ComparedProduct] = Field(default_factory=list)
    created_at: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Earlier turns for guests. Logged-in customers' history is read from the database instead.
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)
    page: PageContext | None = None


class AgentOutput(BaseModel):
    """What the agent must return on every turn (structured output)."""

    reply: str = Field(description="The message shown to the shopper, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_PRODUCT_CARDS,
        description=(
            "product_id values of the matching products to show as cards, best match first. "
            "Only use product_id values returned by the tools; leave empty when no product is "
            "relevant."
        ),
    )
    size: str | None = Field(
        default=None,
        description=(
            "The size (XS, S, M, L, XL or XXL) the shopper is asking about, if they named one "
            "(for example 'in XL' or 'medium hoodies'), so the product cards show availability "
            "in that size. Also set it to the size you recommended. Leave empty otherwise."
        ),
    )
    compare_product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_COMPARED_PRODUCTS,
        description=(
            "product_id values of 2 to 4 products to show side by side in a comparison table. "
            "Fill this when the shopper asks to compare products or how they differ, instead of "
            "product_ids. Leave empty otherwise."
        ),
    )


class ChatResponse(BaseModel):
    """The /api/chat payload: the text reply, the matching products to show as cards, and, when
    the shopper asked to compare products, the products to show in a comparison table."""

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    comparison: list[ComparedProduct] = Field(default_factory=list)
