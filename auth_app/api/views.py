from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, LoginSerializer


# TESTING JWT AUTH FOR LEARING:
class RegistrationView(generics.CreateAPIView):
    """Registers a new user and returns the auth token right away."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        data = {
            'username': new_user.username,
            'email': new_user.email,
            'user_id': new_user.pk,
        }

        return Response(data, status=status.HTTP_201_CREATED)


# 100% WORKING - NORMAL TOKEN AUTH.
# class RegistrationView(generics.CreateAPIView):
#     """Registers a new user and returns the auth token right away."""

#     permission_classes = [AllowAny]
#     serializer_class = RegisterSerializer

#     def create(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         new_user = serializer.save()
#         # the client should be logged in after registering, so it gets a token immediately
#         token, create = Token.objects.get_or_create(user=new_user)
#         data = {
#             'token': token.key,
#             'username': new_user.username,
#             'email': new_user.email,
#             'user_id': new_user.pk,
#         }

#         return Response(data, status=status.HTTP_201_CREATED)


# COOKIE VIEW FÜR JWT, ERWEITERUNG DER STANDARD CLASS VON SIMPLEJWT

class CookieTokenObtainPairView(TokenObtainPairView):
# Self created class from the simplejwt class.
    def post(self, request, *args, **kwargs):
        # Dont return the response, use the response to extract access/refresh token.
        # return super().post(request, *args, **kwargs)
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get("access")
        refresh_token =response.data.get("refresh")

        # Set cookie direkt on response access/token.
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        # Update response.data that no access/refresh token is in the response.
        response.data = {"message" : "Login was successful."}
        return response

class LoginView(generics.GenericAPIView):
    """Exchanges username and password for an auth token."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # the serializer already verified the password and put the user in validated_data
        login_user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=login_user)
        data = {
            'token': token.key,
            'username': login_user.username,
            'email': login_user.email,
            'user_id': login_user.pk,
        }

        return Response(data, status=status.HTTP_200_OK)
