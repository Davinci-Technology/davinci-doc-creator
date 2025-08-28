import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  IconButton,
  Alert
} from '@mui/material';
import { Close as CloseIcon, CloudUpload as UploadIcon } from '@mui/icons-material';

interface DocumentConfig {
  company: string;
  address: string;
  phone: string;
  disclaimer: string;
  logoBase64?: string;
}

interface ConfigDialogProps {
  open: boolean;
  onClose: () => void;
  config: DocumentConfig;
  onSave: (config: DocumentConfig) => void;
}

const ConfigDialog: React.FC<ConfigDialogProps> = ({ open, onClose, config, onSave }) => {
  const [localConfig, setLocalConfig] = useState<DocumentConfig>(config);
  const [logoFileName, setLogoFileName] = useState<string>('');

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const base64String = e.target?.result as string;
        const base64Data = base64String.split(',')[1];
        setLocalConfig({ ...localConfig, logoBase64: base64Data });
        setLogoFileName(file.name);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = () => {
    onSave(localConfig);
  };

  const handleRemoveLogo = () => {
    setLocalConfig({ ...localConfig, logoBase64: undefined });
    setLogoFileName('');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          Document Configuration
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Typography variant="subtitle2" gutterBottom fontWeight="bold">
            Company Information
          </Typography>
          
          <TextField
            fullWidth
            label="Company Name"
            value={localConfig.company}
            onChange={(e) => setLocalConfig({ ...localConfig, company: e.target.value })}
            margin="normal"
            variant="outlined"
          />
          
          <TextField
            fullWidth
            label="Address"
            value={localConfig.address}
            onChange={(e) => setLocalConfig({ ...localConfig, address: e.target.value })}
            margin="normal"
            variant="outlined"
          />
          
          <TextField
            fullWidth
            label="Phone Number"
            value={localConfig.phone}
            onChange={(e) => setLocalConfig({ ...localConfig, phone: e.target.value })}
            margin="normal"
            variant="outlined"
          />
          
          <TextField
            fullWidth
            label="Footer Disclaimer"
            value={localConfig.disclaimer}
            onChange={(e) => setLocalConfig({ ...localConfig, disclaimer: e.target.value })}
            margin="normal"
            variant="outlined"
            multiline
            rows={2}
          />
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom fontWeight="bold">
              Company Logo
            </Typography>
            
            {localConfig.logoBase64 ? (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  Logo uploaded: {logoFileName || 'logo.png'}
                </Alert>
                <Box sx={{ mb: 2 }}>
                  <img 
                    src={`data:image/png;base64,${localConfig.logoBase64}`} 
                    alt="Logo preview" 
                    style={{ maxHeight: '100px', border: '1px solid #ddd', padding: '10px' }}
                  />
                </Box>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleRemoveLogo}
                  size="small"
                >
                  Remove Logo
                </Button>
              </Box>
            ) : (
              <Box>
                <input
                  accept="image/*"
                  style={{ display: 'none' }}
                  id="logo-upload"
                  type="file"
                  onChange={handleFileUpload}
                />
                <label htmlFor="logo-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadIcon />}
                  >
                    Upload Logo
                  </Button>
                </label>
                <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                  Recommended: PNG or JPG, max 5MB, will be resized to fit
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} variant="outlined">
          Cancel
        </Button>
        <Button onClick={handleSave} variant="contained">
          Save Configuration
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfigDialog;