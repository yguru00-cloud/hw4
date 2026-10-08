# Design

## 1) Energetic Brand Aesthetic & Palette
- What changed: Applied vibrant navy blue, athletic varsity gold accents, and bold modern sans-serif typography ('Outfit' / 'Inter').
- Why it helps: Captures the energetic college spirit and builds immediate brand trust with student shoppers.

## 2) Dynamic Motion & Micro-Interactions
- What changed: Added 3D hover lifts on cards, spring animations for chat opening, and pulse urgency badges ('Selling Fast!').
- Why it helps: Provides tactile feedback that keeps shoppers engaged and browsing longer.

## 3) High-Impact Visual Hierarchy
- What changed: Enhanced product cards with hover image zoom, clear high-contrast pricing, and dynamic stock badges.
- Why it helps: Reduces visual friction and drives quick, confident add-to-cart actions.

## 4) Modern Chat Interface
- What changed: Restyled the chat widget with smooth entry animations, glowing state icons, and interactive side-by-side comparison tables.
- Why it helps: Integrates AI recommendations smoothly into the shopping flow without disrupting user browsing.

## 5) Shop Sections by Clothing Type
- What changed: Sorted the Products page into six clothing sections with a sticky category bar for quick jumping.
- Why it helps: Lets shoppers find the type of item they want in seconds instead of scrolling through 102 products.

## 6) Yale Spirit & Campus Character
- What changed: Added Handsome Dan the bulldog mascot, a Yale cheer ticker, and subtle "YALE" and paw-print backgrounds.
- Why it helps: Gives the store campus personality and school pride that build an emotional connection with student shoppers.

---

# Implementation details

The sections above say what changed and why. This part records how each point is built, what was measured, and where the running app differs from the one-line wording. All styling lives in one stylesheet, `frontend/src/index.css`, built on a small set of design tokens at the top.

## 1) Energetic Brand Aesthetic & Palette

- **Palette:**

  | Token | Color | Used for |
  |---|---|---|
  | Vibrant navy | `#0d2a85` | navbar, hero, price tags, headings |
  | Deep navy | `#040c2b`, `#061238` | gradients, button text, dark panels |
  | Bright navy | `#1d44c2` | gradient highlights, hover states |
  | Varsity gold | `#ffc629` | accents, buttons, active links, "Selling Fast!" |
  | Amber | `#f5a300` | button depth, gradient ends, labels |
  | Soft gold | `#fff3c9` | hover highlights, best-price cell |

  The page itself is a cool off-white with a faint gold glow in one corner and a navy glow in the other, so the navy and gold elements stand out.
- **Typography:** Outfit (bold, 700 to 800) for the brand name, headings, prices, buttons and navigation; Inter for body text. Both are installed as local packages (`@fontsource-variable/outfit` and `@fontsource-variable/inter`) and bundled with the site, so there is no request to an outside font service and the type looks the same offline.
- **Where it shows:** the navbar is a navy gradient with a gold rule and a gold star beside the name; the home hero is a navy gradient with varsity-style diagonal stripes, "Campus Apparel" picked out in gold and a gold "Shop Products" button. The hero text is exactly the required copy, unchanged.
- **Contrast checked:** twelve text and background pairs were measured in the running site (navigation, brand, buttons, price tags, badges, card text, page titles and the chat button) and all meet the WCAG AA minimum of 4.5 to 1 for normal text. The lowest is the navigation links on the navy gradient at 5.9 to 1 (measured against the worst point of the gradient); gold on navy is 7.9 to 1 and navy on gold is 12.2 to 1. The check also found one real bug, a dim price on the detail page (a grey paragraph rule overrode the gold), which was fixed. The muted grey used for descriptions was darkened a little as well, from 6.1 to 7.2 to 1 on white.

## 2) Dynamic Motion & Micro-Interactions

| Effect | Where | How |
|---|---|---|
| 3D hover lift | product cards | on hover a card rises 9px, tilts slightly toward the viewer in 3D (`rotateX`), scales up a little and gains a gold-and-navy glow, with a springy ease so it settles with a little bounce |
| Animated gradient border | card on hover, hero, chat panel | a navy-and-gold conic gradient whose angle turns continuously (2.4 s on hover, 7 s on the hero, 6 s on the chat panel), made with the CSS `@property` feature; in a browser without it the border is simply a still gradient |
| Spring chat opening | chat panel and button | the panel pops up from the bottom-right corner, overshooting and settling (650 ms, `cubic-bezier(0.34, 1.56, 0.64, 1)`); the chat button wobbles on hover and presses down when clicked |
| Pulse urgency badge | "Selling Fast!" | a gold pill on the product photo that scales up and sends out a ring, repeating every 1.8 s |
| Message animation | chat bubbles | each message springs in; while the assistant is working, three dots bounce one after another |
| Glow | chat | the green online dot and the dot on the chat button pulse with a soft glow; the chat button sends out a gold ring |

- **"Selling Fast!" is data-driven, not decoration:** it appears only on products that are low on stock (30 units or fewer across all sizes, the same rule as the Low Stock badge). Today that is 11 of the 102 products, for example the Fencing Left Chest Hoodie with 29 units. It shows on the product grid, on the cards the chat puts on the page, and on the product page.
- **Accessibility:** if a shopper's device is set to "reduce motion", all animation and transition is switched off.

## 3) High-Impact Visual Hierarchy

- **Image zoom:** the product photo scales up 9% over 0.7 seconds when the card is hovered; the detail page photo zooms 7% on hover.
- **Clear pricing:** every price is a navy tag with large gold Outfit numerals (the detail page uses a larger tag). They keep a contrast of 7.9 to 1 against their background.
- **High-contrast action button:** each card ends in a gold "View details" button with navy text (12.2 to 1). When the card is hovered it flips to navy with gold text and its arrow slides forward.
- **Dynamic stock badges:** green In Stock, amber Low Stock and red Out of Stock, computed from the real inventory (see `output/usability.md`); they appear on the product grid and the product page as well as in the chat.
- **Note on "add-to-cart":** the shop has no cart or checkout, so the card's action is "View details", which opens the product page with its large photo, sizes and stock. That page is the step before a purchase action; the wording above describes the goal this hierarchy serves.

## 4) Modern Chat Interface

- **Entry and state:** the panel header has a gold "CC" avatar, the assistant's name and a glowing green "Online" indicator. Assistant messages are white with a gold edge; the shopper's are a navy gradient; the Send button is gold.
- **Product cards in the chat** lift and zoom on hover and carry the stock badge.
- **Interactive comparison table:** navy header with a gold underline and the product photos, which tilt when hovered; hovering any cell highlights that product's whole column in soft gold and turns the row label gold; the lowest price is tinted and marked "Lowest"; row labels stay in place when the table scrolls sideways; the panel widens by itself (with a spring) when a table is shown, so three products fit without scrolling.

## 5) Shop Sections by Clothing Type

- **Six sections.** The catalogue stores each item's type as free text with 19 different spellings ("hoodie", "pullover hoodie", "hooded sweatshirt"...), so the server groups them into six shop sections (`categorize()` in `backend/tools.py`):

  | Section | What goes in it | Products |
  |---|---|---|
  | Hoodies | any type containing "hood", including full-zip hooded sweatshirts | 27 |
  | Crewnecks & Sweatshirts | crewnecks, raglan and mock necks | 29 |
  | T-Shirts | every T-shirt spelling | 25 |
  | Quarter-Zips | quarter-zip pullovers | 11 |
  | Jackets & Fleece | fleece, bomber and other jackets | 8 |
  | Performance Tops | long-sleeve performance shirts (athletic shirts) | 2 |

  The product's **type** decides, not its name: the "School Of Architecture Crewneck" is really a quarter-zip (its photo and description both say so), so it sits in Quarter-Zips. `/api/products` returns the products already grouped in this order, and each product carries its `category`.
- **On the page:** a banner, then a sticky bar of category chips with their counts. Clicking a chip scrolls smoothly to that section, and the highlighted chip follows as the shopper scrolls. Each section has a heading with its count and a huge faint ghost of its first word behind it.
- **Checked:** 35 automated checks (every raw spelling, the tricky cases, all 102 products landing in exactly one section, section sizes 27, 29, 25, 11, 8 and 2, and sorted order inside each). In the running app there are six chips with the right counts, 102 cards in total, chips that scroll to their section, a highlight that follows the scroll, and a bar that stays pinned.
- **Phones:** the check found a real bug. The ghost word behind the "Performance Tops" heading was wider than a phone screen and made the Products page scroll sideways (442 px in a 390 px screen). It is now clipped at the section's sides, and all five pages measure exactly 390 px.

## 6) Yale Spirit & Campus Character

- **Ticker:** a slow, endless banner under the navbar: Go Bulldogs!, Boola Boola, Lux et Veritas, Handsome Dan, Est. 1701, Bright College Years, The Game. It pauses when hovered.
- **Backdrop:** faint oversized words (YALE, BOOLA BOOLA, LUX ET VERITAS, 1701) and a trail of paw prints sit behind every page and drift slowly. They ignore the mouse and are hidden from screen readers.
- **Handsome Dan, the Yale bulldog:** he lives in the hero's corner on wide screens, in the Products banner and in the footer. He is built entirely from HTML elements styled with CSS (no image file and no drawing): a cream head with a tan eye patch, folded ears, scowling brows, an underbite, a panting tongue and a navy collar with a gold "Y". He bobs, blinks and pants, tilts when hovered, and barks a cheer in a speech bubble each time he is clicked ("Boola Boola!", "Woof!", "Go Bulldogs!", "Lux et Veritas!", "Bright College Years!").
- **Footer:** a big gold "Lux et Veritas" with "Light and Truth · Est. 1701".
- **Traditions used:** these are well-known Yale traditions (Handsome Dan is Yale's bulldog mascot; Boola Boola and Bright College Years are Yale songs; Lux et Veritas is its motto; 1701 is the founding year), used as decoration. Nothing else about the university is claimed.
- **Checked in the running app:** a bulldog that barks a different cheer on each click, a running ticker, the backdrop words and paw prints, a hero whose text is unchanged and that Handsome Dan never overlaps, and a footer dog clear of the chat button.

## What was checked in the running app

- **Home:** Outfit and Inter both loaded; the hero text is unchanged; the gradient border, the chat button's gold ring and the online dot are all animating.
- **Products:** 102 cards; exactly 11 "Selling Fast!" badges, one on each low-stock product, each pulsing; navy-and-gold price tags and gold buttons. The 3D lift, glow, animated border and image zoom were checked two ways: the hover rules were read from the live stylesheet, and a picture was taken with those exact rules applied to one card.
- **Chat:** the panel opens with the spring animation; a comparison table renders, and real pointer hover highlights the right row and column.
- **Detail page:** price tag, "Selling Fast!" badge, stock badge and size tiles.
- **Phones:** at 390 px wide none of the five pages scrolls sideways, the chat panel fits the screen, and the table scrolls inside itself.

## Limits

- Hover effects need a mouse or trackpad; on a touch screen cards show their resting state.
- The "3D" lift is a CSS perspective tilt, not a full 3D scene.
- The animated gradient border needs a browser with `@property` support (current Chrome, Edge, Safari and Firefox); elsewhere it stays still.
