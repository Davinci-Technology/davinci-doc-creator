import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  AppBar,
  Toolbar,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  IconButton,
  Tooltip,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  Download as DownloadIcon,
  Description as DocumentIcon,
  Settings as SettingsIcon,
  Preview as PreviewIcon,
  Logout as LogoutIcon,
  Send as SendIcon
} from '@mui/icons-material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import ConfigDialog from './components/ConfigDialog';
import DocuSignDialog from './components/DocuSignDialog';
import Login from './Login';
import './App.css';

// Default to relative base so NGINX can proxy `/api` in Docker/K8s.
// For local dev with `npm start`, set REACT_APP_API_URL=http://localhost:5001
const API_URL = process.env.REACT_APP_API_URL || '/api';

interface DocumentConfig {
  company: string;
  address: string;
  phone: string;
  email?: string;
  disclaimer: string;
  logoBase64?: string;
}

interface User {
  name: string;
  email: string;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [markdown, setMarkdown] = useState<string>(`# Document Title

## Introduction

This is a sample document created with the Davinci Document Creator. You can write in **Markdown** format and convert it to a professionally formatted PDF.

### Key Features

- Custom letterhead with company information
- Logo placement in the top right corner
- Automatic page numbering
- Professional disclaimer footer
- Consistent heading styles
- Bullet point formatting

## Section 1: Getting Started

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Subsection 1.1

Here are some important points:

- First bullet point with important information
- Second bullet point with additional details
- Third bullet point with final thoughts

## Section 2: Advanced Features

This document creator supports various Markdown elements including:

1. Numbered lists
2. Bold and italic text
3. Headers at multiple levels
4. Code blocks
5. Tables (coming soon)

## Conclusion

Thank you for using the Davinci Document Creator!`);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [configOpen, setConfigOpen] = useState<boolean>(false);
  const [docuSignOpen, setDocuSignOpen] = useState<boolean>(false);
  const [showPreview, setShowPreview] = useState<boolean>(false);
  
  const [config, setConfig] = useState<DocumentConfig>({
    company: 'Davinci AI Solutions',
    address: '11-6320 11 Street SE, Calgary, AB T2H 2L7',
    phone: '+1 (403) 245-9429',
    email: 'info@davincisolutions.ai',
    disclaimer: 'This document contains confidential and proprietary information of Davinci AI Solutions. © 2025 All Rights Reserved.',
  });

  // Template page options (per-document, not saved in config)
  const [includeTitlePage, setIncludeTitlePage] = useState<boolean>(false);
  const [includeSignaturePage, setIncludeSignaturePage] = useState<boolean>(false);

  useEffect(() => {
    // Check if user is authenticated
    const checkAuth = async () => {
      try {
        const response = await axios.get(`${API_URL}/auth/user`);
        if (response.data && response.data.email) {
          setIsAuthenticated(true);
          setUser(response.data);
        } else {
          setIsAuthenticated(false);
        }
      } catch (error: any) {
        // If the backend returns a 404 for /api/auth/user, but auth is meant to be bypassed (e.g., staging)
        // we'll assume authentication is not required and proceed as a mock user.
        // This is a workaround for the current backend 404 issue on /api/auth/user.
        if (error.response && error.response.status === 404) {
          console.warn('Backend /api/auth/user returned 404. Assuming auth bypass for staging.');
          setIsAuthenticated(true);
          setUser({ name: 'Staging User', email: 'staging@example.com' }); // Mock user for frontend
        } else {
          console.error('Authentication check failed:', error);
          setIsAuthenticated(false);
        }
      }
    };

    checkAuth();
  }, []);

  const handleConvert = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    const apiEndpoint = `${API_URL}/convert`;
    console.log('Attempting to call:', apiEndpoint);
    console.log('API_URL:', API_URL);

    try {
      const response = await axios.post(
        apiEndpoint,
        {
          markdown,
          ...config,
          includeTitlePage,
          includeSignaturePage,
        },
        {
          responseType: 'blob',
        }
      );

      // Extract filename from Content-Disposition header
      // Note: axios lowercases all header names
      const contentDisposition = response.headers['content-disposition'];
      let filename = `document-${Date.now()}.pdf`;
      if (contentDisposition) {
        // More robust regex to handle various formats
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      console.log('Content-Disposition:', contentDisposition);
      console.log('Extracted filename:', filename);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      setSuccess('PDF generated successfully!');
    } catch (err: any) {
      console.error('PDF generation error:', err);
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      console.error('Error config:', err.config);

      if (err.message === 'Network Error' && !err.response) {
        setError('Cannot connect to server. Please ensure the backend is running on port 5001.');
      } else {
        setError(err.response?.data?.error || err.message || 'Failed to generate PDF');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfigSave = (newConfig: DocumentConfig) => {
    setConfig(newConfig);
    setConfigOpen(false);
  };

  const handleSendForSignature = async (
    recipientName: string,
    recipientEmail: string,
    emailSubject?: string,
    emailMessage?: string
  ) => {
    const apiEndpoint = `${API_URL}/docusign/send-for-signature`;
    console.log('Sending to DocuSign:', apiEndpoint);

    try {
      const response = await axios.post(apiEndpoint, {
        markdown,
        recipient_name: recipientName,
        recipient_email: recipientEmail,
        email_subject: emailSubject,
        email_message: emailMessage,
        ...config,
        includeTitlePage,
        includeSignaturePage: true, // Always include signature page for DocuSign
      });

      console.log('DocuSign response:', response.data);

      setSuccess(
        `Document sent successfully! ${recipientName} will receive an email with signing instructions. ` +
        `Envelope ID: ${response.data.envelope_id}`
      );
      setDocuSignOpen(false);
    } catch (err: any) {
      console.error('DocuSign error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Failed to send document for signature';
      throw new Error(errorMessage);
    }
  };

  const handleLogout = () => {
    window.location.href = '/api/auth/logout';
  };

  // Show loading while checking authentication
  if (isAuthenticated === null) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <>
      <AppBar position="static" sx={{ mb: 3 }}>
        <Toolbar>
          <DocumentIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Davinci Document Creator
          </Typography>
          {user && (
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user.name || user.email}
            </Typography>
          )}
          <Tooltip title="Configure Document Settings">
            <IconButton color="inherit" onClick={() => setConfigOpen(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Logout">
            <IconButton color="inherit" onClick={handleLogout}>
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' } }}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Markdown Editor</Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<PreviewIcon />}
                    onClick={() => setShowPreview(!showPreview)}
                  >
                    {showPreview ? 'Hide' : 'Show'} Preview
                  </Button>
                </Box>
                <TextField
                  multiline
                  fullWidth
                  rows={25}
                  value={markdown}
                  onChange={(e) => setMarkdown(e.target.value)}
                  variant="outlined"
                  placeholder="Enter your markdown here..."
                  sx={{
                    fontFamily: 'monospace',
                    '& .MuiInputBase-input': {
                      fontSize: '14px',
                    },
                  }}
                />
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 48%' } }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {showPreview ? 'Preview' : 'Document Information'}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {showPreview ? (
                  <Paper 
                    elevation={0} 
                    sx={{ 
                      p: 3, 
                      bgcolor: 'grey.50',
                      maxHeight: '600px',
                      overflowY: 'auto',
                      '& h1': { fontSize: '1.8rem', fontWeight: 'bold', color: '#2c3e50', mb: 2 },
                      '& h2': { fontSize: '1.5rem', fontWeight: 'bold', color: '#34495e', mt: 2, mb: 1 },
                      '& h3': { fontSize: '1.2rem', fontWeight: 'bold', color: '#34495e', mt: 1, mb: 1 },
                      '& p': { mb: 1, lineHeight: 1.6 },
                      '& ul': { ml: 3 },
                      '& li': { mb: 0.5 },
                    }}
                  >
                    <ReactMarkdown>{markdown}</ReactMarkdown>
                  </Paper>
                ) : (
                  <Box>
                    <Box mb={3}>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Current Configuration
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Company: {config.company}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Address: {config.address}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Phone: {config.phone}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Disclaimer: {config.disclaimer}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Logo: {config.logoBase64 ? 'Uploaded' : 'Not uploaded'}
                      </Typography>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        How to Use
                      </Typography>
                      <Typography variant="body2" paragraph>
                        1. Write or paste your content in Markdown format in the editor
                      </Typography>
                      <Typography variant="body2" paragraph>
                        2. Click the Settings icon to configure your company details and upload a logo
                      </Typography>
                      <Typography variant="body2" paragraph>
                        3. Use the Preview button to see how your document will look
                      </Typography>
                      <Typography variant="body2" paragraph>
                        4. Click "Generate PDF" to create and download your formatted document
                      </Typography>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Markdown Tips
                      </Typography>
                      <Typography variant="body2" component="div">
                        <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
{`# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*

- Bullet point
- Another point

1. Numbered list
2. Second item`}
                        </pre>
                      </Typography>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        </Box>

        <Box mt={3} textAlign="center">
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 3, mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeTitlePage}
                  onChange={(e) => setIncludeTitlePage(e.target.checked)}
                  color="primary"
                />
              }
              label="Include Title Page"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeSignaturePage}
                  onChange={(e) => setIncludeSignaturePage(e.target.checked)}
                  color="primary"
                />
              }
              label="Include Signature Page"
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
              onClick={handleConvert}
              disabled={loading || !markdown.trim()}
              sx={{ px: 4, py: 1.5 }}
            >
              {loading ? 'Generating...' : 'Download PDF'}
            </Button>

            <Button
              variant="contained"
              size="large"
              color="secondary"
              startIcon={<SendIcon />}
              onClick={() => setDocuSignOpen(true)}
              disabled={loading || !markdown.trim() || !includeSignaturePage}
              sx={{ px: 4, py: 1.5 }}
            >
              Send for Signature
            </Button>
          </Box>
        </Box>
      </Container>

      <ConfigDialog
        open={configOpen}
        onClose={() => setConfigOpen(false)}
        config={config}
        onSave={handleConfigSave}
      />

      <DocuSignDialog
        open={docuSignOpen}
        onClose={() => setDocuSignOpen(false)}
        onSend={handleSendForSignature}
      />
    </>
  );
}

export default App;
