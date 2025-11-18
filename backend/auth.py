"""
Azure AD Authentication Module for Davinci Document Creator
"""
import os
import json
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
import msal
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient

class AzureADAuth:
    def __init__(self, app):
        self.app = app
        self.tenant_id = os.environ.get('AZURE_AD_TENANT_ID', '953021b0-d492-4cc9-8551-e0b35080b03a')
        self.client_id = os.environ.get('AZURE_AD_CLIENT_ID')
        self.client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('AZURE_AD_REDIRECT_URI', 'http://localhost:5001/auth/callback')

        # Authority and endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["User.Read"]

        # JWKS URL for token validation
        self.jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(self.jwks_url)

        # Initialize MSAL app
        if self.client_id and self.client_secret:
            self.msal_app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret,
            )
        else:
            self.msal_app = None

    def get_auth_url(self):
        """Generate Azure AD login URL"""
        if not self.msal_app:
            return None

        auth_url = self.msal_app.get_authorization_request_url(
            self.scope,
            redirect_uri=self.redirect_uri,
            state=session.get('state', 'random_state')
        )
        return auth_url

    def acquire_token_by_code(self, code):
        """Exchange authorization code for tokens"""
        if not self.msal_app:
            return {'error': 'Authentication not configured'}

        result = self.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scope,
            redirect_uri=self.redirect_uri
        )
        return result

    def validate_token(self, token):
        """Validate JWT token from Azure AD"""
        try:
            # Get the signing key from Azure AD
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate the token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://sts.windows.net/{self.tenant_id}/"
            )

            return decoded_token
        except Exception as e:
            print(f"Token validation error: {e}")
            return None

    def login_required(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for Authorization header
            auth_header = request.headers.get('Authorization')

            # In development, allow bypass
            if os.environ.get('FLASK_ENV') == 'development' and not os.environ.get('REQUIRE_AUTH'):
                return f(*args, **kwargs)

            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.split(' ')[1]
            user_info = self.validate_token(token)

            if not user_info:
                return jsonify({"error": "Invalid token"}), 401

            # Add user info to request context
            request.user = user_info
            return f(*args, **kwargs)

        return decorated_function

    def get_user_info(self, access_token):
        """Get user information from Microsoft Graph"""
        import requests

        graph_url = 'https://graph.microsoft.com/v1.0/me'
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(graph_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None