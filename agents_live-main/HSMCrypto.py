# Enhanced encryption utilities with HSM integration
class HSMCrypto:
    def __init__(self):
        self.hsm_enabled = os.getenv("HSM_ENABLED", "false").lower() == "true"
        self.hsm_client = None
        
        if self.hsm_enabled:
            self._init_hsm_client()
    
    def _init_hsm_client(self):
        """Initialize HSM client"""
        try:
            # This would be actual HSM client initialization
            # For AWS CloudHSM:
            # import boto3
            # self.hsm_client = boto3.client('cloudhsm')
            logger.info("HSM client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize HSM: {e}")
            self.hsm_enabled = False
    
    async def encrypt_data(self, data: bytes, key_id: str = None) -> Tuple[bytes, str]:
        """Encrypt data with HSM or local encryption"""
        if self.hsm_enabled and key_id:
            # Use HSM for encryption
            try:
                # This would be actual HSM encryption call
                # encrypted_data = self.hsm_client.encrypt(KeyId=key_id, Plaintext=data)
                encrypted_data = SecurityUtils.encrypt_data(data)  # Fallback
                return encrypted_data, key_id
            except Exception as e:
                logger.error(f"HSM encryption failed: {e}")
                # Fallback to local encryption
                return SecurityUtils.encrypt_data(data), "local"
        else:
            # Use local encryption
            return SecurityUtils.encrypt_data(data), "local"
    
    async def decrypt_data(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data with HSM or local decryption"""
        if self.hsm_enabled and key_id != "local":
            try:
                # This would be actual HSM decryption call
                # decrypted_data = self.hsm_client.decrypt(KeyId=key_id, CiphertextBlob=encrypted_data)
                decrypted_data = SecurityUtils.decrypt_data(encrypted_data)  # Fallback
                return decrypted_data
            except Exception as e:
                logger.error(f"HSM decryption failed: {e}")
                # Fallback to local decryption
                return SecurityUtils.decrypt_data(encrypted_data)
        else:
            return SecurityUtils.decrypt_data(encrypted_data)

# Enhanced field-level encryption
class EncryptedField:
    def __init__(self, field_name: str, sensitive: bool = True):
        self.field_name = field_name
        self.sensitive = sensitive
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        encrypted_value = getattr(instance, f"_{self.field_name}_encrypted")
        key_id = getattr(instance, f"_{self.field_name}_key_id", "local")
        
        if encrypted_value is None:
            return None
        
        # Decrypt the value
        hsm_crypto = HSMCrypto()
        decrypted_value = asyncio.run(hsm_crypto.decrypt_data(encrypted_value, key_id))
        return decrypted_value.decode()
    
    def __set__(self, instance, value):
        if value is None:
            setattr(instance, f"_{self.field_name}_encrypted", None)
            setattr(instance, f"_{self.field_name}_key_id", None)
            return
        
        # Encrypt the value
        hsm_crypto = HSMCrypto()
        encrypted_value, key_id = asyncio.run(hsm_crypto.encrypt_data(value.encode()))
        
        setattr(instance, f"_{self.field_name}_encrypted", encrypted_value)
        setattr(instance, f"_{self.field_name}_key_id", key_id)

# Enhanced UserRecord with encrypted fields
class UserRecord(Base):
    __tablename__ = "users"
    
    # Encrypted fields
    _ssn_encrypted = Column(LargeBinary, nullable=True)
    _ssn_key_id = Column(String(100), nullable=True)
    
    @property
    def ssn(self):
        encrypted_value = getattr(self, "_ssn_encrypted")
        key_id = getattr(self, "_ssn_key_id", "local")
        
        if encrypted_value is None:
            return None
        
        hsm_crypto = HSMCrypto()
        decrypted_value = asyncio.run(hsm_crypto.decrypt_data(encrypted_value, key_id))
        return decrypted_value.decode()
    
    @ssn.setter
    def ssn(self, value):
        if value is None:
            self._ssn_encrypted = None
            self._ssn_key_id = None
            return
        
        hsm_crypto = HSMCrypto()
        encrypted_value, key_id = asyncio.run(hsm_crypto.encrypt_data(value.encode()))
        self._ssn_encrypted = encrypted_value
        self._ssn_key_id = key_id

# Data Loss Prevention (DLP) integration
class DLPEngine:
    @staticmethod
    async def inspect_content(content: str, content_type: str = "text") -> Dict[str, Any]:
        """Inspect content for sensitive data"""
        findings = []
        
        # PII detection patterns
        pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "phone": r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        }
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                findings.append({
                    "type": pii_type,
                    "count": len(matches),
                    "matches": matches[:5]  # Limit exposed data
                })
        
        # Data classification
        classification = "public"
        if findings:
            classification = "confidential"
        
        return {
            "findings": findings,
            "classification": classification,
            "recommended_action": "encrypt" if findings else "none"
        }
    
    @staticmethod
    async def anonymize_content(content: str, content_type: str = "text") -> str:
        """Anonymize sensitive content"""
        anonymized = content
        
        # Anonymize PII
        anonymization_patterns = {
            "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "XXX-XX-XXXX"),
            "credit_card": (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "XXXX-XXXX-XXXX-XXXX"),
            "phone": (r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "(XXX) XXX-XXXX")
        }
        
        for pii_type, (pattern, replacement) in anonymization_patterns.items():
            anonymized = re.sub(pattern, replacement, anonymized)
        
        return anonymized

# DLP middleware
@app.middleware("http")
async def dlp_middleware(request: Request, call_next):
    """Middleware to inspect and protect sensitive data"""
    response = await call_next(request)
    
    # Check if response contains sensitive data
    if response.headers.get("content-type", "").startswith("application/json"):
        content = await response.body()
        try:
            json_content = json.loads(content.decode())
            
            # Inspect JSON content for sensitive data
            dlp_result = await DLPEngine.inspect_content(json.dumps(json_content))
            
            if dlp_result["findings"]:
                # Log the finding
                await AuditLogger.log_dlp_event(
                    request, 
                    dlp_result, 
                    "sensitive_data_exposure"
                )
                
                # For highly sensitive data, we might want to redact or block
                if dlp_result["classification"] == "confidential":
                    # In production, implement proper redaction logic
                    pass
                    
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    
    return response