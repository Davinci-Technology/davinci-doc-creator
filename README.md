# Davinci Document Creator

A professional markdown-to-PDF converter with corporate branding and templates. Write in Markdown, get beautifully formatted PDFs with your company letterhead, logo, and consistent styling.

## Features

- **Markdown Editor**: Write documents in familiar Markdown syntax
- **Live Preview**: See your document rendered in real-time
- **Corporate Branding**: Add your company logo and letterhead
- **Professional Templates**: Consistent heading styles and formatting
- **Automatic Features**: Page numbering, disclaimers, and footers
- **Easy Export**: One-click PDF generation and download

## Quick Start

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. Open http://localhost:3000 in your browser

### Docker Development

```bash
docker-compose up --build
```

Access the application at http://localhost:3000

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

Click the Settings icon in the app to configure:
- Company name
- Address
- Phone number
- Footer disclaimer
- Company logo (upload as image)

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

## Technology Stack

- **Backend**: Python Flask, ReportLab for PDF generation
- **Frontend**: React, TypeScript, Material-UI
- **PDF Generation**: ReportLab with custom templates
- **Deployment**: Docker, Kubernetes (AKS ready)

## License

MIT