from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password
from .models import AllowedNode
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
        

class NodeBasicAuthentication(BasicAuthentication):
    """
    Custom Basic Authentication class to authenticate against the AllowedNode model.
    """

    def authenticate_credentials(self, userid, password, request=None):
        try:
            # Find the node by username
            node = AllowedNode.objects.get(username=userid, is_active=True)
        except AllowedNode.DoesNotExist:
            raise AuthenticationFailed('Invalid username/password for node.')

        # Check if the provided password matches the stored hash
        if not check_password(password, node.password):
            raise AuthenticationFailed('Invalid username/password for node.')

        # Return a tuple of (node, None) - DRF expects the first element to be a user-like object
        return (node, None)