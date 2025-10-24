import React, { useState } from 'react';
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
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Close as CloseIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

interface DocuSignDialogProps {
  open: boolean;
  onClose: () => void;
  onSend: (recipientName: string, recipientEmail: string, emailSubject?: string, emailMessage?: string) => Promise<void>;
}

const DocuSignDialog: React.FC<DocuSignDialogProps> = ({ open, onClose, onSend }) => {
  const [recipientName, setRecipientName] = useState<string>('');
  const [recipientEmail, setRecipientEmail] = useState<string>('');
  const [emailSubject, setEmailSubject] = useState<string>('');
  const [emailMessage, setEmailMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<boolean>(false);

  const handleClose = () => {
    if (!loading) {
      // Reset form
      setRecipientName('');
      setRecipientEmail('');
      setEmailSubject('');
      setEmailMessage('');
      setError('');
      setSuccess(false);
      onClose();
    }
  };

  const validateEmail = (email: string): boolean => {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  };

  const handleSend = async () => {
    // Validation
    if (!recipientName.trim()) {
      setError('Recipient name is required');
      return;
    }

    if (!recipientEmail.trim()) {
      setError('Recipient email is required');
      return;
    }

    if (!validateEmail(recipientEmail)) {
      setError('Please enter a valid email address');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await onSend(
        recipientName.trim(),
        recipientEmail.trim(),
        emailSubject.trim() || undefined,
        emailMessage.trim() || undefined
      );

      setSuccess(true);

      // Auto-close after 2 seconds on success
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to send document for signature');
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          Send for Signature
          <IconButton onClick={handleClose} size="small" disabled={loading}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {success ? (
            <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2 }}>
              Document sent successfully! The recipient will receive an email with signing instructions.
            </Alert>
          ) : (
            <>
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Signing Order:</strong>
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  1. The recipient you specify will sign first
                </Typography>
                <Typography variant="body2">
                  2. Ian Strom (Davinci AI Solutions) will counter-sign after the recipient completes signing
                </Typography>
              </Alert>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                  {error}
                </Alert>
              )}

              <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                Recipient Information *
              </Typography>

              <TextField
                fullWidth
                label="Recipient Name"
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                margin="normal"
                variant="outlined"
                required
                disabled={loading}
                placeholder="John Doe"
              />

              <TextField
                fullWidth
                label="Recipient Email"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                margin="normal"
                variant="outlined"
                type="email"
                required
                disabled={loading}
                placeholder="john.doe@example.com"
              />

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                Email Customization (Optional)
              </Typography>

              <TextField
                fullWidth
                label="Email Subject"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
                margin="normal"
                variant="outlined"
                disabled={loading}
                placeholder="Please sign: [Document Name]"
                helperText="Leave blank to use default subject"
              />

              <TextField
                fullWidth
                label="Email Message"
                value={emailMessage}
                onChange={(e) => setEmailMessage(e.target.value)}
                margin="normal"
                variant="outlined"
                multiline
                rows={3}
                disabled={loading}
                placeholder="Please review and sign the attached document."
                helperText="Leave blank to use default message"
              />
            </>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} variant="outlined" disabled={loading}>
          {success ? 'Close' : 'Cancel'}
        </Button>
        {!success && (
          <Button
            onClick={handleSend}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {loading ? 'Sending...' : 'Send for Signature'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DocuSignDialog;
