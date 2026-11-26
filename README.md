# Warrantly — Cloud Digital Warranty Manager

A React application backed by Firebase Authentication and Cloud Firestore, with a Python 3.11+ FastAPI API. It keeps product warranties, invoices and service history together and creates expiry notifications at 30, 7 and 0 days. At the user's request, invoice files are stored on the backend's local filesystem instead of paid Firebase Storage.

## Objectives

- Keep product, warranty, invoice and service information in one authenticated workspace.
- Protect user data with Firebase Authentication and owner-scoped API access.
- Provide expiry reminders and supporting workflows for claims and maintenance.

## Architecture

```text
React + Firebase Authentication (Firebase Hosting)
                 │ Firebase ID token in Authorization: Bearer
                 ▼
          FastAPI on Cloud Run
                 │ Firebase Admin SDK (Application Default Credentials)
        ┌────────┴─────────┐
        ▼                  ▼
   Cloud Firestore   Firebase Auth
        │
        └── FastAPI local invoice files (.local_storage/)
        ▲
 Cloud Scheduler ── POST /api/notifications/scheduled
```

The browser uses Firebase Authentication for identity. All product, invoice, warranty, service-history, analytics and notification requests go to FastAPI; the API verifies the ID token and scopes Firestore queries by the verified UID. Admin SDK calls bypass Firebase Security Rules, so the backend also checks ownership before reads, updates and deletes. Invoice file bytes are stored on the backend's local disk and never in Firestore.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── firebase.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   ├── claims.py
│   │   │   ├── invoices.py
│   │   │   ├── maintenance.py
│   │   │   ├── notifications.py
│   │   │   ├── ocr.py
│   │   │   ├── products.py
│   │   │   ├── qr.py
│   │   │   ├── services.py
│   │   │   └── warranties.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── claims.py
│   │   │   ├── maintenance.py
│   │   │   ├── product.py
│   │   │   └── service.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── notification_service.py
│   │       ├── product_service.py
│   │       ├── storage_service.py
│   │       └── warranty_service.py
│   ├── tests/
│   │   ├── test_api_auth.py
│   │   └── test_warranty_service.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements-dev.txt
│   └── requirements.txt
├── src/
│   └── frontend/
│       ├── App.jsx
│       ├── api.js
│       ├── firebase.js
│       ├── main.jsx
│       └── styles.css
├── .env.example
├── .gitignore
├── README.md
├── firebase.json
├── firestore.indexes.json
├── firestore.rules
├── index.html
├── package-lock.json
├── package.json
└── vite.config.js
```

The frontend is served and built from the repository root by Vite. The FastAPI application, its dependencies, tests and Dockerfile are grouped under `backend/`. Firebase Hosting and Firestore configuration stay at the root because the Firebase CLI and `firebase.json` refer to those paths. There is no Docker Compose configuration, separate docs/data tree, frontend test suite, or generated test-report framework in this project, so none is represented by empty folders.

## Features

- Email/password registration, sign-in, persistent Firebase session and password reset.
- User-isolated product records with product search and category filtering.
- Month-aware expiry-date calculation, active/expiring/expired status and 30-day views.
- Private PDF/JPEG/PNG/WebP invoice uploads (10 MB limit), replacement and authenticated downloads from local disk.
- Per-product service records and service-history overview.
- Product and category analytics, purchase spending and in-app expiry reminders.
- OCR-assisted invoice extraction with editable fields and explicit confirmation before saving.
- User-specific QR generation and authenticated QR lookup/download.
- Warranty eligibility checks, claim tracking, claim checklists and PDF claim-letter export.
- Maintenance scheduling, completion tracking, expense totals and duplicate-safe scheduled reminders.
- Daily scheduled reminders at 30 days, 7 days and expiry day, with deterministic IDs preventing duplicate Firestore notifications.
- Optional SMTP email delivery. Without SMTP configuration, in-app notifications still work; no email is sent.
- Firestore rules for owner-scoped client access.

## Technologies

- Frontend: React 18, JavaScript/JSX, Vite 6, Lucide React.
- Identity and data: Firebase Authentication, Firebase Admin SDK, Cloud Firestore.
- Backend: Python 3.11+, FastAPI, Pydantic Settings, Uvicorn.
- File processing: PyMuPDF, Pillow, optional Tesseract OCR, QR Code and ReportLab.
- Tests: Python `unittest` with FastAPI `TestClient`.
- Optional deployment: Docker, Firebase Hosting, Google Cloud Run and Cloud Scheduler.

> **Persistent local storage:** On Windows, invoice files live in `%LOCALAPPDATA%\Warrantly\invoices`, outside the source tree, so they survive app restarts, rebuilds and source cleanup. On Linux/macOS, the default is `$XDG_DATA_HOME/warrantly/invoices` or `~/.local/share/warrantly/invoices`. These files still depend on the local machine and should be backed up. Cloud Run's writable filesystem is ephemeral and instance-local; do not use this local-storage configuration there for durable invoices.

## Local setup

### Prerequisites

- Node.js 18 or newer and npm.
- Python 3.11 or newer and pip.
- A Firebase project with Email/Password Authentication enabled and Cloud Firestore created.
- Google Cloud Application Default Credentials for local backend access (`gcloud` CLI), or a service-account credential kept outside the repository.
- Docker Engine only if using the container instructions below.

### 1. Firebase project

1. Create a Firebase project and register a Web app.
2. In Firebase Authentication, enable **Email/Password**.
3. Create a Cloud Firestore database. Firebase Storage is not required for this local-file configuration.
4. Configure the Web app values in a root `.env` copied from `.env.example`.
5. From the project root, install the Firebase CLI if needed, select your project with `firebase use --add`, and deploy rules/indexes:

   ```powershell
   firebase deploy --only firestore:rules,firestore:indexes
   ```

### 2. Python API

Use Python 3.11 or newer. For local development, authenticate using Application Default Credentials for the same Google Cloud project. This avoids storing a service-account key in the project:

```powershell
gcloud auth application-default login
Copy-Item backend\.env.example backend\.env
```

Set `FIREBASE_PROJECT_ID`, `ALLOWED_ORIGINS` and a long random `SCHEDULER_SECRET` in `backend\.env`. The invoice directory defaults to a persistent per-user data folder; override it with an absolute `LOCAL_INVOICE_STORAGE_DIR` path if desired. `GOOGLE_APPLICATION_CREDENTIALS` is optional; if used, it must point to a credential file stored outside the repository. Never commit credentials.

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

FastAPI health check: <http://localhost:8000/health>  
Interactive API reference: <http://localhost:8000/docs>

### 3. React app

From the project root:

```powershell
npm install
Copy-Item .env.example .env
```

Fill in the Firebase Web app configuration and set `VITE_API_URL=http://localhost:8000`. Then run:

```powershell
npm run dev
```

The app does not use mock or local fallback data. Firebase configuration and a running API with valid Firebase credentials are required to sign in and use the dashboard.

### Environment variables

Copy the tracked examples and replace their placeholders with your own project settings:

- Root `.env`: `VITE_API_URL` and the Firebase web app values (`VITE_FIREBASE_*`).
- `backend\.env`: `FIREBASE_PROJECT_ID`, `ALLOWED_ORIGINS` and `SCHEDULER_SECRET`. Optional settings include `GOOGLE_APPLICATION_CREDENTIALS`, `LOCAL_INVOICE_STORAGE_DIR` and SMTP values.

Vite exposes variables prefixed with `VITE_` to browser code; do not put private keys, passwords or service-account credentials in the root `.env`. `.env.example` files contain placeholders and should remain safe to commit.

### Database setup

The application uses Cloud Firestore; it has no SQL database or schema migration command. Create the Firestore database in your Firebase project, authenticate the Firebase CLI, select the project (`firebase use --add`) and deploy the checked-in rules and indexes:

```powershell
firebase deploy --only firestore:rules,firestore:indexes
```

The backend uses Firebase Admin SDK with Application Default Credentials locally. Admin SDK access bypasses Firestore rules, so API routes also enforce ownership. The browser-side Firebase Authentication uses the root `.env` web configuration.

## Run with Docker

The existing Dockerfile builds the backend only. From the repository root:

```powershell
Set-Location backend
docker build -t warrantly-api .
docker run --rm --name warrantly-api -p 8000:8080 --env-file .env warrantly-api
```

Create `backend\.env` from `backend\.env.example` first. The container needs Firebase Admin credentials at runtime for Firestore-backed API operations; configure ADC or securely mount a credential and set `GOOGLE_APPLICATION_CREDENTIALS` to its **container path**. Do not copy credential files into the build context or image. No `docker-compose.yml` is present; Docker Compose commands are therefore not applicable. The frontend remains a separate Vite process (`npm run dev` from the repository root).

## API outline

All routes below (except health and scheduled notification invocation) require `Authorization: Bearer <Firebase ID token>`.

| Area | Routes |
|---|---|
| Authentication | `GET /api/auth/me` |
| Products | `GET/POST /api/products`, `GET/PUT/DELETE /api/products/{product_id}` |
| Warranties | `GET /api/warranties/expiring` |
| Invoices | `POST/GET/DELETE /api/invoices/{product_id}`, `GET /api/invoices/{product_id}/download` |
| Service history | `GET/POST /api/products/{product_id}/services`, `PUT/DELETE /api/products/{product_id}/services/{service_id}`, `GET /api/services` |
| Notifications | `GET /api/notifications`, `PATCH /api/notifications/{notification_id}/read` |
| Analytics | `GET /api/analytics` |
| OCR | `POST /api/ocr/extract` |
| QR | `POST/GET /api/qr/{product_id}`, `GET /api/qr/{product_id}/download`, `GET /api/qr/scan/{product_id}` |
| Claims | `GET/POST /api/claims`, `PUT/DELETE /api/claims/{claim_id}`, `GET /api/claims/eligibility/{product_id}`, `GET /api/claims/{claim_id}/letter` |
| Maintenance | `GET/POST /api/maintenance`, `PUT/DELETE /api/maintenance/{maintenance_id}`, `PATCH /api/maintenance/{maintenance_id}/complete` |
| Scheduler | `POST /api/notifications/scheduled` (requires `X-Scheduler-Secret`) |

Product documents are stored in `products` and include the user ID, product information, purchase/warranty dates, a relative local invoice path, and Firestore creation/update timestamps. Invoice contents live in the persistent local data directory (configurable with `LOCAL_INVOICE_STORAGE_DIR`), not Firestore or Firebase Storage. Service records and notifications are stored in their own top-level collections. Purchase and expiry dates are stored as Firestore timestamps; API responses use ISO date strings.

## Deploy to Google Cloud Run

1. Select a Google Cloud project, enable billing, and enable the Cloud Run, Cloud Build, Artifact Registry, Firestore and Cloud Scheduler APIs.
2. Create/use the Firebase project's Firestore database and grant the Cloud Run runtime service account Firestore access.
3. Deploy the API from the repository root (replace the values):

   ```powershell
   gcloud run deploy warranty-api `
     --source backend `
     --region us-central1 `
     --allow-unauthenticated `
     --set-env-vars "FIREBASE_PROJECT_ID=your-project-id,ALLOWED_ORIGINS=https://your-project-id.web.app,SCHEDULER_SECRET=your-long-secret,LOCAL_INVOICE_STORAGE_DIR=.local_storage"
   ```

   `--allow-unauthenticated` allows the browser to reach the API; protected API routes still require verified Firebase ID tokens. Do not put service-account private keys in the image or environment. Cloud Run should use its attached service identity via Application Default Credentials. **Local invoice files on Cloud Run are ephemeral and are not a durable storage solution.**

4. For optional email reminders, set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` and `SMTP_FROM` using Secret Manager-backed Cloud Run environment variables. Keep credentials out of source control and command history.

## Schedule automated reminders

Create a Cloud Scheduler HTTP job that invokes the Cloud Run endpoint once daily. The configured secret is sent in the `X-Scheduler-Secret` header:

```powershell
gcloud scheduler jobs create http warranty-expiry-notifications `
  --location us-central1 `
  --schedule "0 9 * * *" `
  --time-zone "UTC" `
  --uri "https://YOUR-CLOUD-RUN-URL/api/notifications/scheduled" `
  --http-method POST `
  --headers "X-Scheduler-Secret=YOUR_SCHEDULER_SECRET"
```

Set the same secret on Cloud Run as `SCHEDULER_SECRET`. The endpoint creates Firestore notifications for products expiring exactly 30, 7 or 0 days from the run date. The notification ID includes the product and expiry date, making reruns idempotent. Daily scheduling is necessary to hit each reminder interval.

## Deploy frontend to Firebase Hosting

1. Set the Firebase project with `firebase use --add`.
2. Build with production values in the root `.env`: the Firebase Web app configuration and `VITE_API_URL` set to the deployed Cloud Run URL.

   ```powershell
   npm install
   npm run build
   firebase deploy --only hosting
   ```

3. Include the Hosting origin in Cloud Run's `ALLOWED_ORIGINS` and redeploy the API if it changes.

## Test

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The tests cover authentication requirements across API routes, scheduler authorization, invoice validation/local disk lifecycle/path isolation, month-end/leap-year expiry calculation, status thresholds and product validation. Test output is printed to the terminal. To save a plain-text report from PowerShell, run the test command from `backend` and pipe it to `Tee-Object`, for example `python -m unittest discover -s tests -v 2>&1 | Tee-Object -FilePath ..\unittest-report.txt`. No XML/HTML report generator is currently configured. For an end-to-end check, configure Firebase, run the API and frontend, then register an account and exercise product, invoice and service-record operations through the UI and `/docs`.

## OCR dependency

PDF text extraction uses PyMuPDF. Image OCR uses Tesseract through `pytesseract` when the Tesseract executable is available. On Windows, install Tesseract separately or configure its executable path. If OCR cannot extract text, the invoice scanner remains usable with manual entry.

## Troubleshooting

- **Firebase sign-in is disabled:** check the root `.env` has all required `VITE_FIREBASE_*` values, then restart Vite.
- **Dashboard API requests fail:** verify the API is running at `VITE_API_URL` and that its `ALLOWED_ORIGINS` includes the Vite origin (normally `http://localhost:5173`).
- **Firestore reports missing credentials or project:** authenticate with `gcloud auth application-default login` and set `FIREBASE_PROJECT_ID` in `backend\.env`.
- **Invoice files are unavailable after container restart:** local container storage is not durable; use durable object storage before production use.
- **Image OCR returns no text:** install Tesseract separately and confirm it is on `PATH`; PDF text extraction does not require Tesseract.
- **PowerShell blocks virtual-environment activation:** use `.\.venv\Scripts\python.exe -m pip ...` and `.\.venv\Scripts\python.exe -m uvicorn ...` without activating the environment.

## Screenshots and demonstration

No screenshots or recorded demo are currently included. Run the frontend and backend using the setup steps above, configure Firebase, and use the app in a browser to capture a demonstration.

## Future enhancements

- Use durable object storage for invoice files in deployed environments.
- Add frontend and end-to-end tests, plus a machine-readable test-report workflow.
- Add deployment automation and operational monitoring for the API and scheduled reminders.

## Contributors

Contributors are not identified in the project files. Add project contributors here when they are known.

## License

No license is currently specified in the repository. Choose and add a `LICENSE` file before distributing or publishing the project.
