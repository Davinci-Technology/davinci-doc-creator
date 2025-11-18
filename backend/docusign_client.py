"""
DocuSign API Client for Davinci Document Creator
Handles envelope creation, signing, and status tracking
"""

import base64
import os
import logging
from docusign_esign import (
    ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer,
    SignHere, DateSigned, Text, Tabs, Recipients, CarbonCopy
)
from docusign_esign.client.api_exception import ApiException

logger = logging.getLogger(__name__)


class DocuSignClient:
    """Client for DocuSign eSignature API integration"""

    def __init__(self):
        """Initialize DocuSign API client with JWT authentication"""
        self.integration_key = os.getenv('DOCUSIGN_INTEGRATION_KEY')
        self.user_id = os.getenv('DOCUSIGN_USER_ID')
        self.account_id = os.getenv('DOCUSIGN_ACCOUNT_ID')
        self.base_path = os.getenv('DOCUSIGN_BASE_PATH', 'https://demo.docusign.net/restapi')
        self.oauth_host = os.getenv('DOCUSIGN_OAUTH_HOST', 'account-d.docusign.com')
        self.private_key_path = os.getenv('DOCUSIGN_PRIVATE_KEY_PATH')

        # Counter-signer (configurable via env vars, defaults to Ian Strom)
        self.counter_signer_email = os.getenv('DOCUSIGN_COUNTER_SIGNER_EMAIL', 'ian.strom@davincisolutions.ai')
        self.counter_signer_name = os.getenv('DOCUSIGN_COUNTER_SIGNER_NAME', 'Ian Strom')

        self.api_client = None
        self.envelopes_api = None

        # Validate configuration
        if not all([self.integration_key, self.user_id, self.account_id]):
            logger.warning("DocuSign not fully configured. Some environment variables are missing.")

    def _get_api_client(self):
        """Get or create authenticated API client"""
        if self.api_client is None:
            self.api_client = ApiClient()
            self.api_client.set_base_path(self.base_path)
            self.api_client.set_oauth_host_name(self.oauth_host)

            # Get JWT token
            try:
                if self.private_key_path and os.path.exists(self.private_key_path):
                    with open(self.private_key_path, 'r') as key_file:
                        private_key = key_file.read()

                    token_response = self.api_client.request_jwt_user_token(
                        client_id=self.integration_key,
                        user_id=self.user_id,
                        oauth_host_name=self.oauth_host,
                        private_key_bytes=private_key,
                        expires_in=3600,
                        scopes=["signature", "impersonation"]
                    )

                    access_token = token_response.access_token
                    self.api_client.set_default_header("Authorization", f"Bearer {access_token}")
                    logger.info("DocuSign JWT authentication successful")
                else:
                    logger.error(f"Private key not found at {self.private_key_path}")
                    raise Exception("DocuSign private key not configured")

            except Exception as e:
                logger.error(f"DocuSign authentication failed: {e}")
                raise

        return self.api_client

    def _get_envelopes_api(self):
        """Get EnvelopesApi instance"""
        if self.envelopes_api is None:
            api_client = self._get_api_client()
            self.envelopes_api = EnvelopesApi(api_client)
        return self.envelopes_api

    def create_tabs_for_recipient(self, signer_type='recipient'):
        """
        Create DocuSign tabs (form fields) using anchor tags

        Args:
            signer_type: 'recipient' or 'davinci' to determine which anchors to use

        Returns:
            Tabs object with positioned signature fields
        """
        prefix = 'recipient' if signer_type == 'recipient' else 'davinci'

        return Tabs(
            sign_here_tabs=[
                SignHere(
                    anchor_string=f'/ds_{prefix}_signature/',
                    anchor_units='pixels',
                    anchor_x_offset='0',
                    anchor_y_offset='0',
                    tab_label=f'{prefix}_signature'
                )
            ],
            text_tabs=[
                Text(
                    anchor_string=f'/ds_{prefix}_name/',
                    anchor_units='pixels',
                    anchor_x_offset='0',
                    anchor_y_offset='0',
                    tab_label=f'{prefix}_name',
                    value='',
                    required='true',
                    width='200',
                    height='20'
                ),
                Text(
                    anchor_string=f'/ds_{prefix}_title/',
                    anchor_units='pixels',
                    anchor_x_offset='0',
                    anchor_y_offset='0',
                    tab_label=f'{prefix}_title',
                    value='',
                    required='true',
                    width='200',
                    height='20'
                )
            ],
            date_signed_tabs=[
                DateSigned(
                    anchor_string=f'/ds_{prefix}_date/',
                    anchor_units='pixels',
                    anchor_x_offset='0',
                    anchor_y_offset='0',
                    tab_label=f'{prefix}_date'
                )
            ]
        )

    def send_envelope_for_signature(self, pdf_buffer, recipient_name, recipient_email,
                                    document_name='Document', email_subject=None,
                                    email_message=''):
        """
        Create and send DocuSign envelope for signature

        Sequential routing:
        1. External recipient signs first (routing order 1)
        2. Ian Strom counter-signs (routing order 2)

        Args:
            pdf_buffer: BytesIO buffer containing PDF
            recipient_name: Name of external recipient
            recipient_email: Email of external recipient
            document_name: Display name for document
            email_subject: Custom email subject (optional)
            email_message: Custom message to recipients (optional)

        Returns:
            dict with envelope_id, status, and recipient info
        """
        try:
            envelopes_api = self._get_envelopes_api()

            # Encode PDF to base64
            pdf_buffer.seek(0)
            pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('ascii')

            # Create document
            document = Document(
                document_base64=pdf_base64,
                name=document_name,
                file_extension='pdf',
                document_id='1'
            )

            # Create recipient (external person signs first)
            recipient_signer = Signer(
                email=recipient_email,
                name=recipient_name,
                recipient_id='1',
                routing_order='1',
                tabs=self.create_tabs_for_recipient('recipient')
            )

            # Create Davinci counter-signer (Ian signs second)
            davinci_signer = Signer(
                email=self.counter_signer_email,
                name=self.counter_signer_name,
                recipient_id='2',
                routing_order='2',
                tabs=self.create_tabs_for_recipient('davinci')
            )

            # Create recipients object
            recipients = Recipients(
                signers=[recipient_signer, davinci_signer]
            )

            # Create envelope definition
            envelope_definition = EnvelopeDefinition(
                email_subject=email_subject or f"Please sign: {document_name}",
                email_blurb=email_message or "Please review and sign the attached document.",
                documents=[document],
                recipients=recipients,
                status='sent'  # Send immediately
            )

            # Create and send envelope
            envelope_summary = envelopes_api.create_envelope(
                self.account_id,
                envelope_definition=envelope_definition
            )

            logger.info(f"DocuSign envelope created: {envelope_summary.envelope_id}")

            return {
                'envelope_id': envelope_summary.envelope_id,
                'status': envelope_summary.status,
                'recipient': {
                    'name': recipient_name,
                    'email': recipient_email,
                    'routing_order': 1
                },
                'counter_signer': {
                    'name': self.counter_signer_name,
                    'email': self.counter_signer_email,
                    'routing_order': 2
                }
            }

        except ApiException as e:
            logger.error(f"DocuSign API error: {e}")
            raise Exception(f"Failed to create DocuSign envelope: {e.body}")
        except Exception as e:
            logger.error(f"Unexpected error creating envelope: {e}")
            raise

    def get_envelope_status(self, envelope_id):
        """
        Get current status of an envelope

        Args:
            envelope_id: DocuSign envelope ID

        Returns:
            dict with envelope status and signer information
        """
        try:
            envelopes_api = self._get_envelopes_api()
            envelope = envelopes_api.get_envelope(self.account_id, envelope_id)

            # Get recipient status
            recipients = envelopes_api.list_recipients(self.account_id, envelope_id)

            signer_status = []
            if recipients.signers:
                for signer in recipients.signers:
                    signer_status.append({
                        'name': signer.name,
                        'email': signer.email,
                        'status': signer.status,
                        'routing_order': signer.routing_order,
                        'signed_date_time': signer.signed_date_time
                    })

            return {
                'envelope_id': envelope_id,
                'status': envelope.status,
                'created_date_time': envelope.created_date_time,
                'sent_date_time': envelope.sent_date_time,
                'completed_date_time': envelope.completed_date_time,
                'signers': signer_status
            }

        except ApiException as e:
            logger.error(f"Error getting envelope status: {e}")
            raise Exception(f"Failed to get envelope status: {e.body}")

    def download_envelope_documents(self, envelope_id):
        """
        Download completed envelope documents

        Args:
            envelope_id: DocuSign envelope ID

        Returns:
            PDF bytes of signed document
        """
        try:
            envelopes_api = self._get_envelopes_api()

            # Download combined PDF of all documents
            temp_file = envelopes_api.get_document(
                self.account_id,
                'combined',
                envelope_id
            )

            return temp_file

        except ApiException as e:
            logger.error(f"Error downloading envelope: {e}")
            raise Exception(f"Failed to download envelope: {e.body}")
