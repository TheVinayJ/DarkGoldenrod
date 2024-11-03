# yourapp/views.py
from django.contrib.auth.models import update_last_login
from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import SignupSerializer, LoginSerializer
from .utils import get_tokens_for_user
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.views import APIView
from .services import RemoteNodeService
from django.middleware.csrf import get_token
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

def signup(request):
    return render(request, 'login/signup.html')

def login(request):
    return render(request, 'login/login.html')

def signout(request):
    return render(request, 'login/login.html')

class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        next_url = request.data.get('next') or request.GET.get('next') or '/'
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        author = serializer.save()

        # Generate access token
        access_token = AccessToken.for_user(author)

        response = redirect(next_url)

        # Set the access token in the cookie
        response.set_cookie(
            key='access_token',
            value=str(access_token),
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            max_age=60*60*24*7,
        )

        # Optionally, set user_id or other cookies
        response.set_cookie(
            key='user_id',
            value=author.id,
            httponly=False,
            secure=False,
            samesite='Lax',
            max_age=60*60*24*7,
        )

        return response


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        next_url = request.data.get('next') or request.GET.get('next') or '/'
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate access token
        access_token = AccessToken.for_user(user)

        # Optionally update last login
        update_last_login(None, user)

        response_data = {
            'next': next_url,
        }
        response = JsonResponse(response_data, status=200)

        # Set the access token in the cookie
        response.set_cookie(
            key='access_token',
            value=str(access_token),
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            max_age=60*60*24*7,
        )

        response.set_cookie(
            key='user_id',
            value=user.id,
            httponly=False,
            secure=False,
            samesite='Lax',
            max_age=60*60*24*7,
        )

        # CSRF cookie is set by the decorator
        return response

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('user_id')
        return response

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'display_name': user.display_name,
            'description': user.description,
            'host': user.host,
            'github': user.github,
            'profile_image': request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
            'page': user.page,
            'friends': [friend.id for friend in user.friends.all()],
        }, status=status.HTTP_200_OK)

# class RemoteNodeViewSet(viewsets.ModelViewSet):
#     queryset = RemoteNode.objects.all()
#     serializer_class = RemoteNodeSerializer
#     permission_classes = [IsAdminUser]

#     @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
#     def connect(self, request, pk=None):
#         remote_node = self.get_object()
#         result = RemoteNodeService.connect_to_node(remote_node.id)
#         if "error" in result:
#             return Response(result, status=status.HTTP_400_BAD_REQUEST)
#         return Response(result, status=status.HTTP_200_OK)