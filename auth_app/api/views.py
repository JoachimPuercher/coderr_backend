from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegisterSerializer, LoginSerializer
from .throttles import RegistrationRateThrottle, LoginRateThrottle


class RegistrationView(generics.CreateAPIView):
    """Registers a new user and returns the auth token right away."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegistrationRateThrottle]

    def create(self, request):
        """Create user and profile, then answer with token and user data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        # the client should be logged in after
        # registering, so it gets a token immediately
        token, create = Token.objects.get_or_create(user=new_user)
        data = {
            'token': token.key,
            'username': new_user.username,
            'email': new_user.email,
            'user_id': new_user.pk,
        }

        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Exchanges username and password for an auth token."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        """Return the user's token; it is created on the first login only."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # the serializer already verified the
        # password and put the user in validated_data
        login_user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=login_user)
        data = {
            'token': token.key,
            'username': login_user.username,
            'email': login_user.email,
            'user_id': login_user.pk,
        }

        return Response(data, status=status.HTTP_200_OK)
