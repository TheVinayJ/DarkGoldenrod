from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Retrieve token from cookies
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None  # No authentication if token is missing

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except exceptions.AuthenticationFailed:
            return None