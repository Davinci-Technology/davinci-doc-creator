# Davinci Document Creator

A professional markdown-to-PDF converter with corporate branding and templates. Write in Markdown, get beautifully formatted PDFs with your company letterhead, logo, and consistent styling following Davinci AI Solutions' 2025 branding guidelines.

## Purpose

This application was built for Davinci AI Solutions to create professional documents with consistent branding. It automatically applies corporate styling including letterhead, logos, page numbering, and disclaimers to any markdown content, ensuring all documents maintain brand consistency.

## Features

- **Markdown Editor**: Write documents in familiar Markdown syntax with sample content preloaded
- **Live Preview**: Toggle between document info and rendered markdown preview
- **Corporate Branding**: Automatic Davinci AI Solutions branding with customizable options
- **Professional Styling**: Headers use official brand colors (Davinci Blue #0B98CE, Davinci Denim #316EA8, Davinci Grey #494949)
- **Smart Features**: 
  - Dynamic page numbering ("Page X of Y" format)
  - Filename generation from document title
  - Date-stamped exports (format: `document-title-YYYY-MM-DD-HHMMSS.pdf`)
- **Logo Placement**: Top-right corner following brand guidelines (Size S: 3.5cm x 1.05cm)

## Quick Start

### Local Development

1. **Backend Setup** (runs on port 5002)
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py  # Starts on http://localhost:5002
   ```

2. **Frontend Setup** (runs on port 3001)
   ```bash
   cd frontend
   npm install
   # For local dev (CRA), set API to backend:
   REACT_APP_API_URL=http://localhost:5002 npm start
   ```

3. Open http://localhost:3001 in your browser

### Using tmux sessions (recommended for persistent sessions)
```bash
# Backend
tmux new-session -d -s doc-flask -c ./backend
tmux send-keys -t doc-flask "source venv/bin/activate" Enter
tmux send-keys -t doc-flask "python app.py" Enter

# Frontend  
tmux new-session -d -s doc-react -c ./frontend
tmux send-keys -t doc-react "npm start" Enter
```

### Docker Development

```bash
docker-compose up --build
```

Access the application at http://localhost:3001 (frontend via NGINX, proxied `/api`) with backend at http://localhost:5002.

## Project Structure

```
davinci-doc-creator/
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # React TypeScript app
│   ├── src/
│   │   ├── App.tsx        # Main component
│   │   └── components/    # React components
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Frontend container
├── assets/                # Static assets
│   ├── logos/            # Company logos
│   └── templates/        # PDF templates
├── k8s/                   # Kubernetes configs
│   ├── namespace.yaml
│   └── deployment.yaml
└── docker-compose.yml     # Docker orchestration
```

## Configuration

### Default Settings (Davinci AI Solutions)
- **Company**: Davinci AI Solutions  
- **Address**: 11-6320 11 Street SE, Calgary, AB T2H 2L7
- **Phone**: +1 (403) 245-9429
- **Email**: info@davincisolutions.ai
- **Disclaimer**: "This document contains confidential and proprietary information of Davinci AI Solutions. © 2025 All Rights Reserved."
- **Logo**: Davinci horizontal logo (pre-loaded from assets)

### Customization
Click the Settings icon in the app to configure:
- Company name and contact details
- Footer disclaimer text
- Upload custom logo (replaces default Davinci logo)

## Deployment

### Azure Kubernetes Service (AKS)

1. Build and push images to Azure Container Registry:
   ```bash
   # Build images
   docker build -t davinciregistry.azurecr.io/davinci-backend:latest ./backend
   docker build -t davinciregistry.azurecr.io/davinci-frontend:latest ./frontend
   
   # Push to registry
   docker push davinciregistry.azurecr.io/davinci-backend:latest
   docker push davinciregistry.azurecr.io/davinci-frontend:latest
   ```

2. Deploy to AKS:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/deployment.yaml
   ```

Note: The frontend container (NGINX) proxies `/api` to the backend Service named `backend` in the same namespace.

## How It Works

### PDF Generation Process
1. User writes content in Markdown format in the editor
2. Frontend sends markdown + configuration to Flask backend
3. Backend processes the markdown:
   - Extracts title from first H1 header for filename
   - Converts markdown to HTML using markdown2
   - Parses HTML and creates ReportLab flowables
4. Custom `NumberedCanvas` class:
   - Tracks all pages during document building
   - Calculates total page count
   - Draws headers, footers, and page numbers on each page
5. PDF is generated with all branding elements
6. File is sent back with proper Content-Disposition header
7. Frontend extracts filename and triggers download

### Key Technical Details

#### CORS Configuration
The backend exposes the Content-Disposition header for filename access:
```python
CORS(app, expose_headers=['Content-Disposition'])
```

#### Page Numbering Implementation
The custom canvas class saves page states and applies numbering in a second pass:
```python
def save(self):
    num_pages = len(self._saved_page_states)
    for page_num, state in enumerate(self._saved_page_states, start=1):
        self.current_page_number = page_num
        self.total_pages = num_pages
        self.draw_page_number()
```

#### Filename Generation
```python
# Extract from first H1 header
title = line[2:].strip()  
# Clean and format
title = title.replace(' ', '-').lower()
# Add timestamp
filename = f'{title}-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.pdf'
```

## API Reference

### POST /api/convert
Converts markdown to branded PDF.

**Request**:
```json
{
  "markdown": "# Title\n\nContent...",
  "company": "Company Name",
  "address": "Company Address", 
  "phone": "Phone Number",
  "email": "email@company.com",
  "disclaimer": "Footer disclaimer text",
  "logo_base64" or "logoBase64": "optional base64 encoded logo image (base64)"
}
```

**Response**: PDF file with Content-Disposition header

### GET /api/health
Health check endpoint.

Note: The frontend performs client-side preview and does not use a preview API.

## Testing

- Use a long Markdown document in the editor to verify multipage styling, headers, and page numbering.
- End-to-end smoke test script writes outputs under `tmp/e2e/`:
  ```bash
  chmod +x scripts/e2e_smoke.sh
  ./scripts/e2e_smoke.sh
  ```
  - Saves request payload, response headers, and `output.pdf` for inspection.
  - Backend also writes logs to `backend/tmp/logs/backend.log`.
This generates a multi-page PDF to verify page numbering works correctly.

## Common Issues

### Port Conflicts
- Backend uses port 5001 (port 5000 conflicts with macOS AirPlay)
- Frontend uses port 3001 (port 3000 may be in use)

### Flask Not Auto-Reloading
Restart Flask manually if changes aren't reflected:
```bash
tmux send-keys -t doc-flask C-c Enter
tmux send-keys -t doc-flask "python app.py" Enter
```

### Missing Dependencies
Ensure virtual environment is activated and requirements installed:
```bash
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

## Technology Stack

- **Backend**: Python Flask, ReportLab for PDF generation, markdown2 for parsing
- **Frontend**: React, TypeScript, Material-UI, Axios
- **PDF Generation**: ReportLab with custom Canvas class
- **Deployment**: Docker, Kubernetes (AKS ready)
- **Python**: 3.11+
- **Node.js**: 18+

## License

Proprietary - Davinci AI Solutions © 2025 All Rights Reserved
