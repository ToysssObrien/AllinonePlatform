# OmniDesk

Starter backend and UI for managing multiple customer support channels from one inbox.

## What is included

- FastAPI backend
- Vue 3 single-page chat UI
- SQLite storage for demo data and messages
- Optional Telethon integration for real Telegram sending
- Image, video, and voice attachment support for both outgoing and incoming messages

## Run

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn backend.app.main:app --reload
```

4. Open `http://127.0.0.1:8000`

### Facebook OAuth setup

Create a local `.env` file at the project root with:

```env
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret
FB_VERIFY_TOKEN=omnidesk_fb_verify
OMNIDESK_BASE_URL=http://127.0.0.1:8000
```

`backend.app.main` loads this file automatically on startup.

## Telegram mode

To connect a real Telegram account:

1. Open the account in the sidebar.
2. Fill in `Display name`, `Phone`, `API ID`, and `API Hash`.
3. Click `Save profile`.
4. Click `Send code`.
5. Enter the login code you receive from Telegram and click `Verify code`.
6. If the account has 2FA enabled, enter the password and click `Verify password`.

After a successful login, the Telethon session is stored under `data/sessions/` and can be reused without logging in again.

Other channels are represented in the UI and can be connected through future adapters.

Without API credentials, the app stays in demo mode and still lets you test the inbox flow.

### Media support

- Use the Customer Inbox panel to reply with text, images, videos, or voice notes.
- Use the Inbound Test panel to simulate a customer sending an image, video, or voice note.
- Uploaded files are stored locally under `data/media/` and served from `/media/...`.
