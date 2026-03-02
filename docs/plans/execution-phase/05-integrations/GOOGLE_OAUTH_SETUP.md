# Google OAuth Setup

## Overview

PDP Automation v.3 uses Google OAuth 2.0 for user authentication, restricting access to users within the @your-domain.com Google Workspace domain. This provides secure, single sign-on authentication without managing passwords.

**Key Features:**
- Domain-restricted authentication (@your-domain.com only)
- JWT-based session management
- Secure token storage and rotation
- Role-based access control integration

## Prerequisites

1. **Google Cloud Project** (YOUR-GCP-PROJECT-ID)
2. **Google Workspace Admin** access (@your-domain.com domain)
3. **Backend service** deployed with HTTPS
4. **Frontend application** with OAuth callback handling

## OAuth Consent Screen Configuration

### Step 1: Configure OAuth Consent Screen

```bash
# Enable required APIs
gcloud services enable \
  oauth2.googleapis.com \
  iap.googleapis.com \
  --project=YOUR-GCP-PROJECT-ID
```

**Manual Configuration (Google Cloud Console):**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: `YOUR-GCP-PROJECT-ID`
3. Navigate to **APIs & Services** > **OAuth consent screen**

4. **OAuth consent screen setup:**
   - User Type: **Internal** (restricts to @your-domain.com users only)
   - App name: `PDP Automation`
   - User support email: `support@your-domain.com`
   - Developer contact email: `dev@your-domain.com`
   - App logo: Upload company logo (120x120px)
   - Authorized domains: `your-domain.com`
   - Application home page: `https://pdp-automation.your-domain.com`
   - Application privacy policy: `https://pdp-automation.your-domain.com/privacy`
   - Application terms of service: `https://pdp-automation.your-domain.com/terms`

5. **Scopes:**
   - `openid`
   - `email`
   - `profile`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

6. Click **Save and Continue**

### Step 2: Create OAuth 2.0 Client ID

1. Navigate to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**

3. **Application type:** Web application

4. **Name:** `PDP Automation Web Client`

5. **Authorized JavaScript origins:**
   ```
   https://pdp-automation-frontend-XXXXX.run.app
   http://localhost:5173  (for local development)
   ```

6. **Authorized redirect URIs:**
   ```
   https://pdp-automation-frontend-XXXXX.run.app/auth/callback
   http://localhost:5173/auth/callback  (for local development)
   ```

7. Click **Create**

8. **Save credentials:**
   - Note the **Client ID** (ends with `.apps.googleusercontent.com`)
   - Note the **Client Secret**

### Step 3: Store OAuth Credentials in Secret Manager

```bash
# Create JSON file with OAuth credentials
cat > oauth-credentials.json << EOF
{
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uris": [
    "https://pdp-automation-frontend-XXXXX.run.app/auth/callback",
    "http://localhost:5173/auth/callback"
  ],
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF

# Store in Secret Manager
gcloud secrets create google-oauth-credentials \
  --data-file=oauth-credentials.json \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Grant access to service account
gcloud secrets add-iam-policy-binding google-oauth-credentials \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR-GCP-PROJECT-ID

# Delete local file (security)
rm oauth-credentials.json
```

## Backend Implementation

### Configuration

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OAuth Configuration
    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_CLIENT_SECRET: str
    GOOGLE_OAUTH_REDIRECT_URI: str
    ALLOWED_EMAIL_DOMAIN: str = "your-domain.com"

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days

    # Frontend URL
    FRONTEND_URL: str = "https://pdp-automation-frontend-XXXXX.run.app"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Install Dependencies

```bash
pip install google-auth>=2.0.0
pip install google-auth-oauthlib>=1.0.0
pip install google-auth-httplib2>=0.1.0
pip install pyjwt>=2.8.0
pip install python-jose[cryptography]>=3.3.0
```

### Authentication Service

```python
# backend/app/services/auth_service.py
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from app.db.session import get_db

class AuthService:
    """Service for handling OAuth authentication"""

    def __init__(self):
        self.client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.allowed_domain = settings.ALLOWED_EMAIL_DOMAIN

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Google OAuth token and extract user info.

        Args:
            token: Google OAuth token

        Returns:
            User info dictionary

        Raises:
            ValueError: If token is invalid or domain not allowed
        """
        try:
            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )

            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')

            # Extract user info
            email = idinfo.get('email')
            email_verified = idinfo.get('email_verified', False)

            if not email_verified:
                raise ValueError('Email not verified')

            # Check domain restriction
            if not self._is_allowed_domain(email):
                raise ValueError(f'Email domain not allowed. Must be @{self.allowed_domain}')

            user_info = {
                'email': email,
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'google_id': idinfo.get('sub')
            }

            logger.info(f"Successfully verified token for user: {email}")
            return user_info

        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise ValueError('Invalid token')

    def _is_allowed_domain(self, email: str) -> bool:
        """Check if email domain is allowed"""
        return email.endswith(f'@{self.allowed_domain}')

    async def get_or_create_user(self, user_info: Dict[str, Any]) -> User:
        """
        Get existing user or create new one.

        Args:
            user_info: User information from Google

        Returns:
            User model instance
        """
        from sqlalchemy.orm import Session
        from sqlalchemy import select

        db = next(get_db())

        try:
            # Check if user exists
            stmt = select(User).where(User.email == user_info['email'])
            result = db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Update user info
                user.name = user_info.get('name')
                user.picture = user_info.get('picture')
                user.last_login = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    email=user_info['email'],
                    name=user_info.get('name'),
                    picture=user_info.get('picture'),
                    google_id=user_info.get('google_id'),
                    role='user',  # Default role
                    is_active=True,
                    last_login=datetime.utcnow()
                )
                db.add(user)

            db.commit()
            db.refresh(user)

            logger.info(f"User retrieved/created: {user.email}")
            return user

        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token.

        Args:
            user: User model instance

        Returns:
            JWT token string
        """
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'type': 'access'
        }

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return token

    def create_refresh_token(self, user: User) -> str:
        """
        Create JWT refresh token.

        Args:
            user: User model instance

        Returns:
            JWT refresh token string
        """
        payload = {
            'sub': str(user.id),
            'exp': datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise ValueError('Token has expired')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')

# Singleton instance
auth_service = AuthService()
```

### API Routes

```python
# backend/app/api/routes/auth.py
from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from app.services.auth_service import auth_service
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api/auth", tags=["auth"])

class GoogleAuthRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, response: Response):
    """
    Authenticate user with Google OAuth token.
    """
    try:
        # Verify Google token
        user_info = await auth_service.verify_google_token(request.token)

        # Get or create user
        user = await auth_service.get_or_create_user(user_info)

        # Create tokens
        access_token = auth_service.create_access_token(user)
        refresh_token = auth_service.create_refresh_token(user)

        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return AuthResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "role": user.role
            }
        )

    except ValueError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """
    Refresh access token using refresh token.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    try:
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token)

        if payload.get('type') != 'refresh':
            raise ValueError('Invalid token type')

        # Get user
        from app.models.user import User
        from app.db.session import get_db

        db = next(get_db())
        user = db.query(User).filter(User.id == payload['sub']).first()

        if not user or not user.is_active:
            raise ValueError('User not found or inactive')

        # Create new access token
        access_token = auth_service.create_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing refresh token cookie.
    """
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "role": current_user.role
    }
```

### Authentication Dependency

```python
# backend/app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import auth_service
from app.models.user import User
from app.db.session import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    token = credentials.credentials

    try:
        # Verify token
        payload = auth_service.verify_token(token)

        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == payload['sub']).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
```

## Frontend Implementation

### Install Dependencies

```bash
npm install @react-oauth/google
npm install axios
```

### OAuth Provider Setup

```typescript
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <App />
    </GoogleOAuthProvider>
  </React.StrictMode>
);
```

### Login Component

```typescript
// frontend/src/components/Login.tsx
import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { Button, message } from 'antd';
import { GoogleOutlined } from '@ant-design/icons';
import { authService } from '../services/authService';
import { useNavigate } from 'react-router-dom';

export const Login: React.FC = () => {
  const navigate = useNavigate();

  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        // Send token to backend for verification
        const authResponse = await authService.authenticate(tokenResponse.access_token);

        // Store access token
        localStorage.setItem('access_token', authResponse.access_token);

        message.success(`Welcome, ${authResponse.user.name}!`);
        navigate('/dashboard');
      } catch (error: any) {
        if (error.response?.status === 401) {
          message.error('Authentication failed. Please ensure you are using an @your-domain.com account.');
        } else {
          message.error('Login failed. Please try again.');
        }
      }
    },
    onError: () => {
      message.error('Login failed. Please try again.');
    },
  });

  return (
    <div className="login-container">
      <h1>PDP Automation</h1>
      <p>Sign in with your @your-domain.com Google account</p>
      <Button
        type="primary"
        icon={<GoogleOutlined />}
        size="large"
        onClick={() => login()}
      >
        Sign in with Google
      </Button>
    </div>
  );
};
```

### Auth Service

```typescript
// frontend/src/services/authService.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    picture: string;
    role: string;
  };
}

export interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
  role: string;
}

class AuthService {
  /**
   * Authenticate with Google OAuth token
   */
  async authenticate(googleToken: string): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(
      `${API_URL}/api/auth/google`,
      { token: googleToken },
      { withCredentials: true }  // Include cookies
    );
    return response.data;
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    const response = await axios.post(
      `${API_URL}/api/auth/refresh`,
      {},
      { withCredentials: true }
    );
    return response.data.access_token;
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    await axios.post(
      `${API_URL}/api/auth/logout`,
      {},
      { withCredentials: true }
    );
    localStorage.removeItem('access_token');
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('access_token');
    const response = await axios.get<User>(
      `${API_URL}/api/auth/me`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }
}

export const authService = new AuthService();
```

### API Client with Token Refresh

```typescript
// frontend/src/services/apiClient.ts
import axios, { AxiosError, AxiosResponse } from 'axios';
import { authService } from './authService';

const API_URL = import.meta.env.VITE_API_URL;

export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    // If 401 and haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const newToken = await authService.refreshToken();
        localStorage.setItem('access_token', newToken);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

## Security Considerations

1. **Domain Restriction**
   - Always validate email domain on backend
   - Never trust frontend domain checks alone

2. **Token Storage**
   - Access tokens: localStorage (short-lived, 1 hour)
   - Refresh tokens: HTTP-only cookies (long-lived, 7 days)
   - Never store sensitive tokens in regular cookies

3. **HTTPS Only**
   - Enforce HTTPS in production
   - Set `secure=True` for cookies

4. **CSRF Protection**
   - Use `SameSite=Lax` for cookies
   - Implement CSRF tokens for state-changing operations

5. **Token Rotation**
   - Rotate access tokens every 60 minutes
   - Rotate refresh tokens every 7 days
   - Invalidate old tokens on rotation

## Rate Limiting

```python
# backend/app/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        now = datetime.now()

        # Clean old requests
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # Record request
        self.requests[client_ip].append(now)

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
```

## Troubleshooting

### Issue: "Email domain not allowed" error

```python
# Verify domain setting in backend
print(settings.ALLOWED_EMAIL_DOMAIN)  # Should be "your-domain.com"

# Check user email
# Must end with @your-domain.com
```

### Issue: Token refresh fails

```bash
# Check cookie settings
# Ensure withCredentials: true in frontend
# Ensure CORS allows credentials in backend

# Backend CORS config
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: OAuth redirect not working

```bash
# Verify redirect URI matches exactly
# Google Cloud Console > Credentials > OAuth Client ID
# Must match frontend callback URL exactly
```

## Next Steps

- Configure [Google Sheets Integration](GOOGLE_SHEETS_INTEGRATION.md) for content export
- Set up [Google Drive Integration](GOOGLE_DRIVE_INTEGRATION.md) for file sharing
- Review [Google Cloud Setup](GOOGLE_CLOUD_SETUP.md) for infrastructure

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/sign-in/web)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
