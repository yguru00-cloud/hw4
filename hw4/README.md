# Campus Customs

A web shop for university apparel with a chat assistant. Shoppers browse 102 products by clothing type, check stock by size, compare items side by side and ask the assistant questions. The assistant looks up every price and stock number in the database before it states it.

- **Frontend:** React 19 + TypeScript + Vite (`frontend/`)
- **Backend:** FastAPI + SQLite (`backend/`)
- **Assistant:** a PydanticAI agent using the OpenAI model `gpt-6-astra` through Portkey, with four database tools

## What is in this repository

```
hw4/
├── AI_prompts.md        every prompt used to build the project, by problem
├── requirements.txt     Python packages for the backend
├── .env.example         placeholder for the API key (copy to .env)
├── .gitignore
├── README.md
├── frontend/            Vite React TypeScript app
├── backend/
│   ├── main.py          FastAPI app (run with: uvicorn main:app --reload); also the
│   │                    login sessions, saved chat history and catalogue corrections
│   ├── agent.py         builds and runs the chat agent; also the safety pre-check
│   │                    and the audit trail
│   ├── models.py        Pydantic models
│   ├── tools.py         the agent's database tools
│   └── prompts/
│       └── prompt.md    the agent's instructions and safety rules
└── output/
    ├── harness.md       how the system works (fields, tools, safety rules, specs)
    ├── design.md        visual design
    ├── usability.md     usability improvements
    ├── app_check.html   site test with screenshots (open it in a browser)
    ├── app_check_images/  the screenshots
    └── audit_trail.json append-only log of the agent's actions
```

The database and the product photos are **not** in this repository. They come in a separate data pack (see step 1).

## Run it

You need **Python 3.10 or newer** and **Node.js 20.19+ or 22.12+**. Commands are for Windows PowerShell and are run from this `hw4` folder; on macOS or Linux activate the environment with `source .venv/bin/activate`.

### 1. Place the data pack

Put the two items of the data pack in a `data/` folder next to `backend/` and `frontend/`:

```
hw4/data/
├── campus_customs.db
└── products/          the product photos
```

The database file must be **writable**. When the backend starts it adds a `sessions` table (for logins) and corrects three catalogue rows that ship with placeholder text (`benjamin-franklin-t-shirt`, `berkeley-sweater-fleece-jacket`, `timothy-dwight-college-crewneck`). Registering and chatting while logged in also write to it. Nothing else in the data is changed.

### 2. Add your API key

```powershell
copy .env.example .env
```

Open `.env` and replace `your-portkey-api-key-here` with your own Portkey key. `.env` is ignored by git. Without a key the shop works, but the chat answers "not configured".

### 3. Start the backend (first terminal)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

The first three lines are needed only once. Start `uvicorn` from the `backend/` folder, because its files import each other by plain name. It is ready when it prints `Application startup complete`. Check it at `http://127.0.0.1:8000/api/products` (the product list) or `http://127.0.0.1:8000/docs` (the API). Restart it after editing `backend/prompts/prompt.md`.

### 4. Start the frontend (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

`npm install` is needed only once. Open `http://localhost:5173`. The dev server forwards `/api` and `/media` to the backend on port 8000, so the backend must be running first. If the backend is somewhere else, set `BACKEND_URL` (for example `$env:BACKEND_URL="http://127.0.0.1:8001"`) before `npm run dev`.

### 5. Try it

Open the chat button at the bottom right and ask, for example:

- "How much is the Champion Reverse Weave Hoodie 1, and how many do you have in medium?"
- "What hoodies do you have?"
- "Compare the Fencing Left Chest Hoodie and the Basic Hoodie Big Yale"
- "What size should I get? I'm 5'10 and 170 lbs."

Every tool call the assistant makes is appended to `output/audit_trail.json` (it already holds a few sample entries), so `git status` will show that file as modified after you chat. That is expected.

Stop each server with `Ctrl+C`.

### If something does not start

- `ModuleNotFoundError: bcrypt` (or another package): `uvicorn` was started with a Python that is not the activated `.venv`. Activate it and run `pip install -r requirements.txt` again.
- "address already in use": another program is using port 8000 or 5173.
- The chat answers "not configured" (`503`): `.env` is missing or has no key. Add it and restart the backend.
- Products load but have no photos: the `products/` folder is not in `hw4/data/`.

## More detail

- [`output/harness.md`](output/harness.md): the data model, the agent's tools, the safety rules, the audit trail and the system limits.
- [`output/usability.md`](output/usability.md) and [`output/design.md`](output/design.md): what was improved and why.
- [`output/app_check.html`](output/app_check.html): screenshots that show the chat checking stock and prices, product cards from a category question, and a comparison table.
