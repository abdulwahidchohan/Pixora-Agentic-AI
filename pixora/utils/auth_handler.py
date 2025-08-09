"""
Authentication handler for Pixora system.

Manages authentication tokens and credentials for different
image generation providers (ImageFX, Vertex AI).
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import config
from .logger import get_logger, log_error


class AuthHandler:
    """Handles authentication for different image generation providers."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._fernet_key = None
        self._cipher_suite = None
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Set up encryption for storing sensitive data."""
        try:
            # Try to get existing key from keyring
            key = keyring.get_password("pixora", "encryption_key")
            
            if not key:
                # Generate new key if none exists
                key = Fernet.generate_key()
                keyring.set_password("pixora", "encryption_key", key.decode())
            
            self._fernet_key = key if isinstance(key, bytes) else key.encode()
            self._cipher_suite = Fernet(self._fernet_key)
            
        except Exception as e:
            self.logger.warning(f"Failed to set up encryption: {e}")
            self._cipher_suite = None
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._cipher_suite:
            return data
        
        try:
            encrypted_data = self._cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return data
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._cipher_suite:
            return encrypted_data
        
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self._cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def store_imagefx_token(self, token: str, expires_at: Optional[datetime] = None) -> bool:
        """
        Store ImageFX authentication token securely.
        
        Args:
            token: The authentication token
            expires_at: When the token expires (optional)
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            token_data = {
                "token": token,
                "stored_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None
            }
            
            encrypted_data = self._encrypt(json.dumps(token_data))
            keyring.set_password("pixora", "imagefx_token", encrypted_data)
            
            self.logger.info("ImageFX token stored successfully")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "store_imagefx_token"})
            return False
    
    def get_imagefx_token(self) -> Optional[str]:
        """
        Retrieve the stored ImageFX authentication token.
        
        Returns:
            The authentication token if available and valid, None otherwise
        """
        try:
            encrypted_data = keyring.get_password("pixora", "imagefx_token")
            if not encrypted_data:
                return None
            
            token_data = json.loads(self._decrypt(encrypted_data))
            token = token_data.get("token")
            expires_at = token_data.get("expires_at")
            
            # Check if token is expired
            if expires_at:
                expiry = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expiry:
                    self.logger.warning("ImageFX token has expired")
                    self.clear_imagefx_token()
                    return None
            
            return token
            
        except Exception as e:
            log_error(e, context={"action": "get_imagefx_token"})
            return None
    
    def clear_imagefx_token(self) -> bool:
        """
        Clear the stored ImageFX authentication token.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            keyring.delete_password("pixora", "imagefx_token")
            self.logger.info("ImageFX token cleared")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "clear_imagefx_token"})
            return False
    
    def is_imagefx_token_valid(self) -> bool:
        """
        Check if the stored ImageFX token is valid and not expired.
        
        Returns:
            True if token is valid, False otherwise
        """
        token = self.get_imagefx_token()
        return token is not None
    
    def store_vertex_credentials(self, service_account_path: str) -> bool:
        """
        Store Vertex AI service account credentials path.
        
        Args:
            service_account_path: Path to the service account JSON file
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Validate the service account file
            if not Path(service_account_path).exists():
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")
            
            # Read and validate the JSON content
            with open(service_account_path, 'r') as f:
                credentials = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in credentials:
                    raise ValueError(f"Missing required field in service account: {field}")
            
            # Store the path securely
            encrypted_path = self._encrypt(service_account_path)
            keyring.set_password("pixora", "vertex_credentials_path", encrypted_path)
            
            self.logger.info("Vertex AI credentials stored successfully")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "store_vertex_credentials"})
            return False
    
    def get_vertex_credentials_path(self) -> Optional[str]:
        """
        Retrieve the stored Vertex AI credentials path.
        
        Returns:
            Path to the service account file if available, None otherwise
        """
        try:
            encrypted_path = keyring.get_password("pixora", "vertex_credentials_path")
            if not encrypted_path:
                return None
            
            path = self._decrypt(encrypted_path)
            
            # Verify the file still exists
            if not Path(path).exists():
                self.logger.warning("Vertex AI credentials file no longer exists")
                self.clear_vertex_credentials()
                return None
            
            return path
            
        except Exception as e:
            log_error(e, context={"action": "get_vertex_credentials_path"})
            return None
    
    def clear_vertex_credentials(self) -> bool:
        """
        Clear the stored Vertex AI credentials.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            keyring.delete_password("pixora", "vertex_credentials_path")
            self.logger.info("Vertex AI credentials cleared")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "clear_vertex_credentials"})
            return False
    
    def is_vertex_credentials_valid(self) -> bool:
        """
        Check if the stored Vertex AI credentials are valid.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        path = self.get_vertex_credentials_path()
        if not path:
            return False
        
        try:
            # Verify the file exists and is readable
            with open(path, 'r') as f:
                credentials = json.load(f)
            
            # Check required fields
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            return all(field in credentials for field in required_fields)
            
        except Exception:
            return False
    
    def get_provider_auth_info(self) -> Dict[str, Any]:
        """
        Get authentication information for the configured provider.
        
        Returns:
            Dictionary with provider authentication details
        """
        if config.use_imagefx:
            token = self.get_imagefx_token()
            return {
                "provider": "imagefx",
                "authenticated": token is not None,
                "token": token,
                "base_url": config.imagefx_base_url
            }
        
        elif config.use_vertex_ai:
            credentials_path = self.get_vertex_credentials_path()
            return {
                "provider": "vertex_ai",
                "authenticated": credentials_path is not None,
                "credentials_path": credentials_path,
                "project_id": config.vertex_ai_project_id,
                "location": config.vertex_ai_location
            }
        
        else:
            return {
                "provider": "none",
                "authenticated": False,
                "error": "No image provider configured"
            }
    
    def refresh_imagefx_token(self) -> bool:
        """
        Attempt to refresh the ImageFX token.
        This would typically involve re-authenticating with the service.
        
        Returns:
            True if refresh was successful, False otherwise
        """
        # For now, this is a placeholder. In a real implementation,
        # you would need to implement the actual refresh logic
        # based on ImageFX's authentication flow.
        self.logger.warning("ImageFX token refresh not implemented")
        return False
    
    def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate all stored credentials and return status.
        
        Returns:
            Dictionary with validation results for all providers
        """
        results = {
            "imagefx": {
                "configured": config.use_imagefx,
                "authenticated": self.is_imagefx_token_valid(),
                "needs_refresh": False
            },
            "vertex_ai": {
                "configured": config.use_vertex_ai,
                "authenticated": self.is_vertex_credentials_valid(),
                "needs_refresh": False
            }
        }
        
        # Check if ImageFX token needs refresh (if it has expiration)
        if results["imagefx"]["authenticated"]:
            try:
                encrypted_data = keyring.get_password("pixora", "imagefx_token")
                if encrypted_data:
                    token_data = json.loads(self._decrypt(encrypted_data))
                    expires_at = token_data.get("expires_at")
                    if expires_at:
                        expiry = datetime.fromisoformat(expires_at)
                        # Warn if token expires within 1 hour
                        if datetime.utcnow() + timedelta(hours=1) > expiry:
                            results["imagefx"]["needs_refresh"] = True
            except Exception:
                pass
        
        return results
    
    def clear_all_credentials(self) -> bool:
        """
        Clear all stored credentials.
        
        Returns:
            True if all credentials were cleared successfully
        """
        try:
            self.clear_imagefx_token()
            self.clear_vertex_credentials()
            self.logger.info("All credentials cleared")
            return True
            
        except Exception as e:
            log_error(e, context={"action": "clear_all_credentials"})
            return False
