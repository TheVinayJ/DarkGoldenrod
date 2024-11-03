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

# class SignupView(generics.CreateAPIView):
#     serializer_class = SignupSerializer
#     permission_classes = [AllowAny]

    # def post(self, request, *args, **kwargs):
    #     next_url = request.data.get('next') or request.GET.get('next') or '/'
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     author = serializer.save()
    #
    #     # Generate JWT tokens
    #     refresh = RefreshToken.for_user(author)
    #     access = refresh.access_token
    #
    #     response_data = {
    #         'refresh': str(refresh),
    #         'access': str(access),
    #         'next': next_url,
    #     }
    #
    #     response = Response(response_data, status=status.HTTP_201_CREATED)

    # def post(self, request, *args, **kwargs):
    #     next_url = request.data.get('next') or request.GET.get('next') or '/'
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     try:
    #         author = serializer.save()
    #         print(f"Author saved with ID: {author.id}")
    #     except Exception as e:
    #         print(f"Error saving author: {e}")
    #         return Response({'detail': 'Error saving user.'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Check if the author has an ID
    #     if not author.id:
    #         print("Author ID is None after saving.")
    #         return Response({'detail': 'User ID not set after saving.'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Generate JWT tokens
    #     try:
    #         refresh = RefreshToken.for_user(author)
    #         access = refresh.access_token
    #     except Exception as e:
    #         print(f"Error creating tokens: {e}")
    #         return Response({'detail': 'Error creating tokens.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #
    #     response_data = {
    #         'next': next_url,
    #     }
    #
    #     response = redirect(next_url)  # Redirect to the next URL after signup
    #
    #     # Set JWT tokens in HTTP-only cookies
    #     response.set_cookie(
    #         key='access_token',
    #         value=str(access),
    #         httponly=True,
    #         secure=False,  # Ensure this is True in production
    #         samesite='Lax',
    #         max_age=60*60*24*7  # 1 week
    #     )
    #     response.set_cookie(
    #         key='refresh_token',
    #         value=str(refresh),
    #         httponly=True,
    #         secure=False,
    #         samesite='Lax',
    #         max_age=60*60*24*7
    #     )
    #     response.set_cookie(
    #         key='user_id',
    #         value=author.id,
    #         httponly=False,
    #         secure=False,
    #         samesite='Lax',
    #         max_age=60*60*24*7
    #     )
    #
    #     # Set CSRF token
    #     csrf_token = get_token(request)
    #     response['X-CSRFToken'] = csrf_token
    #
    #     return response

    # class SignupView(generics.CreateAPIView):
    #     serializer_class = SignupSerializer
    #     permission_classes = [AllowAny]
    #
    #     def post(self, request, *args, **kwargs):
    #         next_url = request.data.get('next') or request.GET.get('next') or '/'
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         author = serializer.save()
    #
    #         # Generate access token without creating OutstandingToken
    #         access = AccessToken.for_user(author)
    #
    #         response = redirect(next_url)
    #
    #         secure_cookie = False
    #         max_age = 60*60*24*7
    #
    #         # Set the access token in the cookie
    #         response.set_cookie(
    #             key='access_token',
    #             value=str(access),
    #             httponly=True,
    #             secure=secure_cookie,
    #             samesite='Lax',
    #             max_age=max_age,
    #         )
    #
    #         response.set_cookie(
    #             key='user_id',
    #             value=author.id,
    #             httponly=False,
    #             secure=secure_cookie,
    #             samesite='Lax',
    #             max_age=max_age,
    #         )
    #
    #         return response

# class SignupView(generics.CreateAPIView):
#     serializer_class = SignupSerializer
#     permission_classes = [AllowAny]
#
#     def post(self, request, *args, **kwargs):
#         next_url = request.data.get('next') or request.GET.get('next') or '/'
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         author = serializer.save()
#
#         # Authenticate the user and generate tokens
#         token_serializer = TokenObtainPairSerializer(data={
#             'email': author.email,
#             'password': request.data.get('password')  # Ensure password is available
#         })
#
#         print(author.email)
#         print(request.data.get('password'))
#         token_serializer.is_valid(raise_exception=True)
#         tokens = token_serializer.validated_data
#
#         response = redirect(next_url)
#
#         secure_cookie = False
#         max_age = 60*60*24*7
#
#         # Set tokens in cookies
#         response.set_cookie(
#             key='access_token',
#             value=tokens['access'],
#             httponly=True,
#             secure=secure_cookie,
#             samesite='Lax',
#             max_age=max_age,
#         )
#         response.set_cookie(
#             key='refresh_token',
#             value=tokens['refresh'],
#             httponly=True,
#             secure=secure_cookie,
#             samesite='Lax',
#             max_age=max_age,
#         )
#         response.set_cookie(
#             key='user_id',
#             value=author.id,
#             httponly=False,
#             secure=secure_cookie,
#             samesite='Lax',
#             max_age=max_age,
#         )
#
#         return response

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