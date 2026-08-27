from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, LoginSerializer, CustomTokenObtainPairSerializer


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
# UMBAU FÜR EIGENEN SERIALZER - USERNAME/PASSWORD CHECK, NOT EMAIL

class CookieTokenObtainPairView(TokenObtainPairView):
# Self created class from the simplejwt class.
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        # Get own serializer
        serializer = self.get_serializer(data=request.data)

        # Check if serializer is valid
        serializer.is_valid(raise_exception=True)

        # Dont return the response, use the response to extract access/refresh token.
        # Get data for tokens from the custom serializer defined
        access_token = serializer.validated_data["access"]
        refresh_token = serializer.validated_data["refresh"]

        # Build response
        response = Response({"message" : "Login successfull"})


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

    
# class CookieTokenObtainPairView(TokenObtainPairView):
# # Self created class from the simplejwt class.
#     def post(self, request, *args, **kwargs):
#         # Dont return the response, use the response to extract access/refresh token.
#         # return super().post(request, *args, **kwargs)
#         response = super().post(request, *args, **kwargs)
#         access_token = response.data.get("access")
#         refresh_token =response.data.get("refresh")

#         # Set cookie direkt on response access/token.
#         response.set_cookie(
#             key="access_token",
#             value=access_token,
#             httponly=True,
#             secure=True,
#             samesite="Lax"
#         )
#         response.set_cookie(
#             key="refresh_token",
#             value=refresh_token,
#             httponly=True,
#             secure=True,
#             samesite="Lax"
#         )
#         # Update response.data that no access/refresh token is in the response.
#         response.data = {"message" : "Login was successful."}
#         return response


# Create Class that inherits the baseclass from simplejwt refresh token
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Get the refresh token from the cookies set before in the login view
        refresh_token = request.COOKIES.get("refresh_token")

        # Check if token exists or rais error 
        if refresh_token is None:
            return Response(
                {"message" : "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set own data (getted from the cookies) to the original serializer
        serializer = self.get_serializer(data={"refresh":refresh_token})

        # Check if serializer ist valid or raise an error
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {"message" : "Refresh token not found!"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get the access token from the validated serializer
        access_token = serializer.validated_data.get("access")

        # Build the response for the CookieRefreshTokenView
        response = Response({"message" : "Access Token refreshed."})

        # Set the new access token to the cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        # Return the response
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
