# AI Prompts

A record of every prompt I typed, organized by problem.

## Problem 1: Setting Up hw4 and the AI_prompts.md Prompt Log

**Prompt 1**

```
I wanna make AI_prompts.md where all the prompts I typed are recorded

Make one section for each problem(problem 1 to 13) and each section includes the problem number and title
Write the title based on its content

This is Problem1
```

## Problem 2: Documenting the Campus Customs Database Tables and Fields in output/harness.md

**Prompt 1**

```
Problem2

Read and analyze 'data/campus_customs.db'

Create a new file 'output/harness.md' and write down each table and field.
For every field, include one short line explanation of why it matters for either the web shop frontend or the PydanticAI chatbot agent.
```

## Problem 3: Scaffolding the React + Vite + TypeScript Shop Frontend and FastAPI Backend

**Prompt 1**

```
Scaffold a React + Vite + TypeScript frontend and a FastAPI backend in 'backend/main.py'

Requirements:

1. Frontend Navigation: Add a top navbar with links for Home, Products, About Us, Log in, and Create account.

Home Page Hero Section Text:
- Title: Authentic Campus Apparel & Custom Gear
- Subtitle: Show your campus pride with premium quality gear, custom merchandise, and official apparel. Designed for students, alumni, and fans.

About Us Page Text:
- Heading: Welcome to Campus Customs
- Description: For over four decades, Campus Customs has been the official provider of top-quality university gear and tailored apparel. We are dedicated to delivering authentic merchandise, transparent inventory, and personalized service for our entire campus community.

2. FastAPI Backend:
- Serve static images from 'data/products/'
- Create an API endpoint (e.g., '/api/products') to fetch items from 'data/campus_customs.db' ('catalogue' and 'inventory' tables).

3. Products Page & Item Detail:
- Display product cards with image, name, price, and short description on the Products page.
- Clicking a card opens a single-item page/modal showing a large image on one side and full details (description, price, sizes/stock) on the other.

4. Floating Chat Interface:
- Add a floating chat panel in the bottom right corner of the page with a stub placeholder response (backend integration ready for later).
```

**Prompt 2**

```
Three products in data/campus_customs.db (catalogue table) still have placeholder data from a failed image analysis: benjamin-franklin-t-shirt, berkeley-sweater-fleece-jacket, and timothy-dwight-college-crewneck. Their description says "Vision blocked; filename-based stub.", colors is an empty list, and search_tags are just words split from the filename. Fix them.
```

What was lacking after the first: The first prompt produced a working shop, but three products still had placeholder data (stub descriptions, empty colors, filename-only tags) that made their pages look unfinished and hard to search.

## Problem 4: Building the User Authentication Flow (Create Account and Log In) for Frontend and Backend

**Prompt 1**

```
Problem4

Do the user authentication flow for both frontend and backend

Requirements:

1. Frontend UI:
- Create Account Page: Form with First Name, Last Name, Email, Password, and Confirm Password fields.
- Log In Page: Form with Email and Password fields.

2. FastAPI Auth Endpoints:
- '/api/register': Accept first name, last name, email, and password. Hash the password securely (e.g., using passlib/bcrypt) and store the record in the 'users' table of 'data/campus_customs.db'.
- '/api/login': Validate email and password against the 'users' table (support password verification for hashed passwords).

3. Update Harness Specification:
- Append an "Authentication & Security" section to `output/harness.md` explaining how user accounts are stored and how passwords are protected with secure hashing.
```

**Prompt 2**

```
The seed database already has a test user (email: test@campuscustoms.yale.edu, password: password), but I can't log in as that user. Make that login work without changing the seed data, and confirm that a brand-new account I create also works. New passwords must still be stored securely. Then update output/harness.md so it explains how the seeded accounts and new accounts are verified.
```

What was lacking after the first: The first prompt's login only verified the bcrypt hashes of newly created accounts, so the seeded test user, whose password is stored in a different PBKDF2 format, could not log in even with the correct password.

## Problem 5: Building the PydanticAI Chat Agent Backend and Integrating It into FastAPI

**Prompt 1**

```
Problem5

Build the PydanticAI agent backend in the 'backend/' directory and integrate it into FastAPI alongside existing product and authentication endpoints.
(Use PORTKEY_API_KEY for any AI model calls in the agent and use OpenAI model through Portkey: gpt-6-astra)

Requirements:

1. Agent File Structure:
- 'backend/prompts/prompt.md': Store the system prompt defining Campus Customs voice and safety guidelines.
- 'backend/models.py': Define or update Pydantic types for chat requests/responses, structured agent output, and product cards, as well as product/auth schemas.
- 'backend/tools.py': Prepare tool helper functions for the agent (e.g., database lookup helpers for items and stock).
- 'backend/agent.py': Initialize and configure the PydanticAI agent using the prompt and models.

2. FastAPI Integration in 'backend/main.py':
- Keep and preserve all existing endpoints needed for products and user authentication (signup/login).
- Add a POST endpoint '/api/chat' that receives chat messages, routes them to the PydanticAI agent, and returns structured replies with product cards.
- Ensure the backend runs cleanly from the 'backend/' folder using 'uvicorn main:app --reload --port 8000'.

3. Update Harness Documentation:
- Append a section to 'output/harness.md' explaining how the frontend talks to FastAPI (for products, auth, and chat) and how the agent is loaded (prompt file + model).
```

## Problem 6: Adding Database Lookup Tools for Product Info and Stock to the PydanticAI Agent

**Prompt 1**

```
Problem6

Implement DB lookup tools for the PydanticAI agent to fetch accurate product info and stock levels from 'campus_customs.db'.

Requirements:

1. Agent Tools in 'backend/tools.py':
- Create tools that look up real information from 'campus_customs.db' for:
     * Product description
     * Price
     * Stock quantities (filtered by size when requested)
- Ensure tools handle missing sizes or zero stock cleanly so the agent never hallucinates.

2. Data Models in 'backend/models.py':
- Define structured Pydantic models for tool outputs:
     * 'ProductInfo': 'product_id' (int), 'name' (str), 'description' (str), 'price' (float).
     * 'StockInfo': 'product_id' (int), 'size' (str), 'quantity' (int), 'is_in_stock' (bool).

3. Prompt Update in 'backend/prompts/prompt.md':
- Instruct the agent to strictly call these tools before stating prices or stock.
- The agent MUST NOT invent or assume prices or quantities under any circumstances. If a size is out of stock or quantity is 0, explicitly inform the user.

4. Update Harness Specification in 'output/harness.md':
- List each created tool, and briefly explain why each field was chosen for the lookup results: product_id identifies exactly which product the result is about, name lets the agent refer to the product by the name the shopper sees, description gives the agent real details to use instead of inventing them, price gives the exact price from the database so the agent never guesses it, size is needed because stock is tracked per size so each quantity must say which size it is for, quantity gives the exact number in stock where 0 means sold out, and is_in_stock is a simple yes/no so the agent can clearly say when something is sold out.
```

## Problem 7: Chat-Driven Product Search with Interactive Product Cards on the Page

**Prompt 1**

```
Problem7

Implement the dynamic chat-driven product search that updates the page with interactive product cards.

Requirements:

1. Agent Search & Backend Integration:
- Ensure the PydanticAI agent can search product items in 'campus_customs.db' upon user query (e.g., "what hoodies do you have?").
- Define a structured response payload in 'backend/models.py' returning both text reply and a list of matching product objects (image_url, name, price, summary, product_id).

2. Frontend Dynamic UI & Detail View:
- When the frontend chat widget receives matching product data from '/api/chat', dynamically render these items as product cards on the page.
- Ensure every dynamically rendered product card triggers the single-item detail view (large image + full info) when clicked, matching Problem 3's behavior.

3. Prompt & Harness Documentation Updates:
- Update 'backend/prompts/prompt.md' instructing the agent to perform catalog search and return structured product matches whenever a user asks about types of items.
- Update 'output/harness.md' explaining the API contract and data flow of how agent search results reach the frontend and trigger page/modal updates.
```

## Problem 8: Adding Customer Identity, Persistent Chat History and Page Context Awareness to the Agent

**Prompt 1**

```
Problem8

Implement customer memory, persistent chat history, and page context awareness for the PydanticAI agent.

Requirements:

1. Chat History Persistence:
- Create a database table (e.g., 'chat_history') in 'campus_customs.db' to log messages for logged-in users.
- For logged-in users, load past chat history upon page load or chat widget initialization.
- Guest user chats do not need to persist in the database.

2. Customer Identity Context:
- Pass logged-in user information (first name, last name, email) into PydanticAI agent dependencies ('RunContext' / 'deps') so the agent knows who it is speaking with.

3. Page Context Integration:
- Include the current page context (e.g., active 'product_id' and item details when on a product view) in requests sent to '/api/chat'.
- Update 'backend/prompts/prompt.md' and agent logic so queries like "do you have this in pink?" correctly reference the currently viewed product.

4. Update Harness Specification:
- Update 'output/harness.md' documenting:
     * How chat history is stored in the database for logged-in users versus guests.
     * What customer fields (name, email) the agent sees via dependencies.
     * How current page context (product ID / view state) is passed from the frontend to the agent.
```

## Problem 9: Adding Four Usability Improvements (Stock Badges, Comparison Table, Size Recommendation, Out-of-Scope Guardrails)

**Prompt 1**

```
Problem9

Implement 4 usability improvements (2 frontend, 2 backend/agent) and update 'output/usability.md'.

Requirements:

1. Frontend Usability Improvements (Implement both):
- Visual Stock Status Badges: Display color-coded badges ('In Stock', 'Low Stock', or 'Out of Stock') directly on chatbot product cards based on real inventory data.
- Formatted Product Comparison View / Table: Render a clear side-by-side comparison table/card view in the chat UI whenever users compare items or ask about product differences (displaying price, specs, stock status, and features).

2. Agent / Backend Usability Improvements (Implement both):
- Size Recommendation Tool: Add a backend agent tool in 'backend/tools.py' that provides sizing suggestions based on customer height/weight/preference.
- Out-of-Scope Guardrail Tool/Prompt: Enhance 'backend/prompts/prompt.md' and safety checks to handle off-topic questions politely, keeping focus strictly on Campus Customs merchandise.

3. Document in 'output/usability.md':
- Write the content below in 'output/usability.md'.

1) Front-End Improvements

Feature 1: Visual Stock Status Badges
- What you added: Added color-coded badges ('In Stock', 'Low Stock', 'Out of Stock') to product cards in chat.
- Why it helps: Shoppers instantly see availability, avoiding frustration with sold-out items while creating urgency for low-stock products.

Feature 2: Formatted Product Comparison Table
- What you added: A side-by-side comparison table in chat displaying price, specs, and stock for queried items.
- Why it helps: Simplifies decision-making for shoppers evaluating multiple items and drives faster purchase conversions.

2) Agent / Backend Improvements

Feature 1: Size Recommendation Tool
- What you added: A backend tool ('recommend_size') in 'backend/tools.py' recommending sizes based on customer measurements.
- Why it helps: Increases purchasing confidence for shoppers and lowers return rates for the business.

Feature 2: Out-of-Scope Guardrails
- What you added: System prompt rules and input filters in 'backend/prompts/prompt.md' to handle off-topic queries politely.
- Why it helps: Keeps conversations focused on store merchandise, protecting brand reputation and preventing prompt misuse.
```

## Problem 10: Styling the Storefront with a Dynamic Navy-and-Gold Varsity Design

**Prompt 1**

```
Problem10

Style the Campus Customs website to feel like a dynamic, energetic, and modern college storefront, and create 'output/design.md'.

Requirements:

1. Frontend Styling & Dynamic UI Enhancements:
- Apply a dynamic varsity aesthetic (vibrant navy, bright varsity gold/amber accents, bold modern typography).
- Add energetic motion effects: hover elevation lifts, playful spring transitions for chat panels, animated gradient borders, and pulse badges ('Selling Fast!').
- Enhance product cards with subtle image zoom on hover, high-contrast action buttons, and clear price tags.
- Restyle the chat widget interface with animated message bubbles, glowing online indicators, and interactive side-by-side comparison tables.
- Organize the Products page by clothing-type categories.
- The surroundings and background feel a bit plain: decorate them with Yale phrases, a bulldog, or anything else that fits.

2. Document in 'output/design.md':
- Write the content below in 'output/design.md'.

1) Energetic Brand Aesthetic & Palette
What changed: Applied vibrant navy blue, athletic varsity gold accents, and bold modern sans-serif typography ('Outfit' / 'Inter').
Why it helps: Captures the energetic college spirit and builds immediate brand trust with student shoppers.

2) Dynamic Motion & Micro-Interactions
What changed: Added 3D hover lifts on cards, spring animations for chat opening, and pulse urgency badges ('Selling Fast!').
Why it helps: Provides tactile feedback that keeps shoppers engaged and browsing longer.

3) High-Impact Visual Hierarchy
What changed: Enhanced product cards with hover image zoom, clear high-contrast pricing, and dynamic stock badges.
Why it helps: Reduces visual friction and drives quick, confident add-to-cart actions.

4) Modern Chat Interface
What changed: Restyled the chat widget with smooth entry animations, glowing state icons, and interactive side-by-side comparison tables.
Why it helps: Integrates AI recommendations smoothly into the shopping flow without disrupting user browsing.

5) Shop Sections by Clothing Type
What changed: Sorted the Products page into six clothing sections with a sticky category bar for quick jumping.
Why it helps: Lets shoppers find the type of item they want in seconds instead of scrolling through 102 products.

6) Yale Spirit & Campus Character
What changed: Added Handsome Dan the bulldog mascot, a Yale cheer ticker, and subtle "YALE" and paw-print backgrounds.
Why it helps: Gives the store campus personality and school pride that build an emotional connection with student shoppers.
```

## Problem 11: Site Testing and Verification Document with Screenshots

**Prompt 1**

```
Problem11

Perform site testing and generate the verification document 'output/app_check.html'.

Requirements:
1. Directory & Screenshot Setup:
- Ensure the directory 'output/app_check_images/' exists for storing verification screenshots.
- Capture/place clear screenshots demonstrating:
1. 'inventory.png': Chat checking inventory levels and prices accurately from the DB.
2. 'category_search.png': Dynamic search-result product cards appearing after a category question (e.g., hoodies).
3. 'usability_feature.png': One of the Problem 9 usability features (e.g., side-by-side product comparison table or visual stock badges).
2. Generate 'output/app_check.html':
- Create a clean, easy-to-grade HTML page at 'output/app_check.html'.
- Structure each test check with:
* A clear Heading ('<h2>').
* The embedded image using relative paths (e.g., '<img src="app_check_images/inventory.png">').
* 1-2 concise sentences explaining what the screenshot proves.
```

## Problem 12: Audit Trail Logger, Safety Rules and Final Harness Spec

**Prompt 1**

```
Problem12

Implement the audit trail logger, update safety rules in prompts, and finalize 'output/harness.md'.

Requirements:

1. Append-Only Audit Trail ('output/audit_trail.json'):
- Implement an append-only logger in the backend that records every agent action to 'output/audit_trail.json'.
- Log fields: 'timestamp', 'tool_name', 'arguments', 'result_summary', and 'stop_reason'.
- Ensure the JSON file is updated in append mode without wiping previous logs across server restarts.

2. Safety Rules in Prompt ('backend/prompts/prompt.md'):
- Explicitly define core safety rules: strictly prohibit inventing prices/stock quantities, enforce database tool lookups before confirming product data, politely decline off-topic queries, and prevent prompt injection attempts.

3. Finalize Harness Spec ('output/harness.md'):
- Complete 'output/harness.md' with sections covering:
     *Model Fields: List of Pydantic fields in 'models.py' ('product_id', 'name', 'price', 'size', 'quantity', 'is_in_stock') and design rationale.
     *Tools & Abilities: Breakdown of all agent tools (DB search, stock lookup, size recommendation).
     *Safety Rules: Summary of safety constraints.
     *System Specs: Models, loop limits, search result caps, and step-by-step instructions on how to run frontend and backend servers.
```

## Problem 13: Push to GitHub and Submit the Repository URL

**Prompt 1**

```
Problem13

Push the project to a public GitHub repository so it can be submitted.

Requirements:
1. Repository layout:
- The repository root contains a single folder named 'hw4' that holds the whole project. Create a new git repository in a separate staging folder (outside the parent folder that holds my real .env and other homework), copy 'hw4' into it, and run git there. Never run git in the parent folder.
- The layout inside hw4 must match the assignment: AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/ (Vite React TypeScript app), backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md, plus the other backend files the app needs), and output/ (harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json).
- requirements.txt belongs in the hw4 root (move it from backend/) and the run instructions must be updated to match.

2. Keep secrets and local data out of git:
- Add a .gitignore so that .env, data/ (campus_customs.db and product images), node_modules, .venv, __pycache__ and build output are never committed.
- Add a .env.example with placeholders only (for example PORTKEY_API_KEY=your-portkey-api-key-here).
- Before pushing, check that no API key, password or personal data is in any tracked file and that no .env, database or product image is tracked.

3. README.md:
- Explain how to run the frontend and backend after placing the data pack in hw4/data/ (campus_customs.db and products/), how to create the .env from .env.example, and that the app adds a 'sessions' table and corrects three catalogue rows when it starts, so the database file must be writable.

4. Verify and push:
- Test a fresh clone of the repository with the original database to confirm that the README steps work (clone it, place the data pack in hw4/data/, then follow the README).
- Create the public repository on GitHub (use my GitHub account and the noreply commit email), commit and push, and show me the file list and ask me before pushing.
- Give me the repository URL to submit on Canvas.
```
