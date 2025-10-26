# Enhanced security configuration
class ZeroTrustConfig:
    # OAuth 2.0 / OIDC providers
    OAUTH_PROVIDERS = {
        "google": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "authorize_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scopes": ["openid", "email", "profile"]
        },
        "microsoft": {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
            "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/oidc/userinfo",
            "scopes": ["openid", "email", "profile"]
        }
    }
    
    # JWT with asymmetric keys
    JWT_ALGORITHM = "RS256"
    JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
    JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
    
    # Biometric authentication
    BIOMETRIC_ENABLED = os.getenv("BIOMETRIC_ENABLED", "false").lower() == "true"
    BIOMETRIC_PROVIDERS = ["apple", "android", "windows"]

# Enhanced permission system
class Permission(str, Enum):
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_EXPORT = "project:export"
    
    # Task permissions
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"
    TASK_EXECUTE = "task:execute"
    
    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

# Role-Permission matrix
ROLE_PERMISSION_MATRIX = {
    UserRole.ADMIN: [
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE, Permission.PROJECT_EXPORT,
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_DELETE, Permission.TASK_ASSIGN, Permission.TASK_EXECUTE,
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.SYSTEM_ADMIN, Permission.SYSTEM_CONFIG, Permission.SYSTEM_BACKUP, Permission.SYSTEM_RESTORE,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT
    ],
    UserRole.MANAGER: [
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_EXPORT,
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_ASSIGN, Permission.TASK_EXECUTE,
        Permission.USER_READ,
        Permission.AUDIT_READ
    ],
    UserRole.MEMBER: [
        Permission.PROJECT_READ,
        Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_EXECUTE
    ],
    UserRole.VIEWER: [
        Permission.PROJECT_READ,
        Permission.TASK_READ
    ],
    UserRole.GUEST: [
        Permission.PROJECT_READ
    ]
}

# Enhanced UserRecord with permissions
class UserRecord(Base):
    __tablename__ = "users"
    
    # Existing fields...
    permissions = Column(JSON, default=[])
    mfa_method = Column(String(20), default="totp")  # totp, webauthn, sms, email
    webauthn_credentials = Column(JSON, default=[])
    risk_score = Column(Float, default=0.0)
    last_risk_assessment = Column(DateTime)
    adaptive_auth_factors = Column(JSON, default={})
    
    # Additional indexes
    __table_args__ = (
        Index('ix_users_risk_score', 'risk_score'),
        Index('ix_users_mfa_method', 'mfa_method'),
    )

# Enhanced authentication utilities
class AdvancedAuthUtils:
    @staticmethod
    def generate_rsa_jwt(payload: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Generate JWT with RSA private key"""
        to_encode = payload.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        
        private_key = serialization.load_pem_private_key(
            ZeroTrustConfig.JWT_PRIVATE_KEY.encode(),
            password=None,
            backend=default_backend()
        )
        
        return jwt.encode(
            to_encode, 
            private_key, 
            algorithm=ZeroTrustConfig.JWT_ALGORITHM
        )
    
    @staticmethod
    def verify_rsa_jwt(token: str) -> Dict[str, Any]:
        """Verify JWT with RSA public key"""
        try:
            public_key = serialization.load_pem_public_key(
                ZeroTrustConfig.JWT_PUBLIC_KEY.encode(),
                backend=default_backend()
            )
            
            payload = jwt.decode(
                token, 
                public_key, 
                algorithms=[ZeroTrustConfig.JWT_ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise AuthenticationError("Invalid token")
    
    @staticmethod
    async def calculate_risk_score(user: UserRecord, request: Request) -> float:
        """Calculate adaptive authentication risk score"""
        risk_score = 0.0
        factors = {}
        
        # Device fingerprinting
        device_hash = hashlib.sha256(
            f"{request.headers.get('User-Agent')}{request.client.host}".encode()
        ).hexdigest()
        
        # Check if device is known
        async with DatabaseUtils.get_session() as session:
            known_device = await session.execute(
                select(UserSessionRecord).where(
                    and_(
                        UserSessionRecord.user_id == str(user.id),
                        UserSessionRecord.device_hash == device_hash,
                        UserSessionRecord.is_revoked == False
                    )
                )
            )
            known_device = known_device.scalar_one_or_none()
            
            if not known_device:
                risk_score += 0.3
                factors["unknown_device"] = True
            
        # Geographic location analysis (simplified)
        # In production, integrate with geoIP service
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers['X-Forwarded-For'].split(',')[0]
                # Simulate geographic risk (e.g., login from different country)
                risk_score += 0.2
                factors["geo_risk"] = True
        
        # Time-based analysis
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Unusual hours
            risk_score += 0.2
            factors["unusual_time"] = True
        
        # Login velocity
        login_count = await CacheManager.increment(f"login_attempts:{user.id}:{datetime.utcnow().strftime('%Y%m%d')}")
        if login_count > 5:
            risk_score += 0.3
            factors["high_velocity"] = True
        
        return min(risk_score, 1.0), factors

# Enhanced permission checking dependency
async def require_permission(required_permission: Permission):
    """Require specific permission"""
    def permission_checker(current_user: UserRecord = Depends(get_current_active_user)):
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        user_permissions = current_user.permissions or []
        if required_permission not in user_permissions:
            raise AuthorizationError(f"Requires permission: {required_permission}")
        
        return current_user
    return permission_checker

# Enhanced OAuth2 integration
@app.post("/auth/oauth/{provider}")
async def oauth_login(
    provider: str,
    code: str = Body(...),
    redirect_uri: str = Body(...)
):
    """OAuth2 login endpoint"""
    if provider not in ZeroTrustConfig.OAUTH_PROVIDERS:
        raise NotFoundError("OAuth provider not supported")
    
    provider_config = ZeroTrustConfig.OAUTH_PROVIDERS[provider]
    
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_response = await client.post(
            provider_config["token_url"],
            data={
                "client_id": provider_config["client_id"],
                "client_secret": provider_config["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise AuthenticationError("Failed to exchange OAuth code")
        
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        userinfo_response = await client.get(
            provider_config["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise AuthenticationError("Failed to get user info")
        
        user_info = userinfo_response.json()
        
        # Find or create user
        async with DatabaseUtils.get_session() as session:
            user = await session.execute(
                select(UserRecord).where(
                    UserRecord.email == user_info["email"]
                )
            )
            user = user.scalar_one_or_none()
            
            if not user:
                # Create new user with OAuth info
                user = UserRecord(
                    email=user_info["email"],
                    username=user_info.get("preferred_username", user_info["email"].split("@")[0]),
                    full_name=user_info.get("name", ""),
                    is_verified=True,
                    oauth_provider=provider,
                    oauth_id=user_info["sub"]
                )
                session.add(user)
                await session.commit()
            
            # Generate JWT
            jwt_token = AdvancedAuthUtils.generate_rsa_jwt({
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
                "type": "access"
            })
            
            return {"access_token": jwt_token, "token_type": "bearer"}