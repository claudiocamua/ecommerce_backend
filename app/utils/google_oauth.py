from authlib.integrations.starlette_client import OAuth
from app.config import settings

oauth = OAuth()


redirect_uri = settings.get_google_redirect_uri()

print(f"🔍 Ambiente: {settings.ENVIRONMENT}")
print(f"🔍 Google Redirect URI: {redirect_uri}")

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'redirect_uri': redirect_uri
    }
)