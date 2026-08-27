from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import UserTypeChoices, UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """Creates a User together with its UserProfile from a single registration payload."""

    repeated_password = serializers.CharField(max_length=100, write_only=True)
    type = serializers.ChoiceField(choices=UserTypeChoices.choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'type']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def save(self):
        """Create the user with a hashed password and the matching profile."""
        user = User(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
        )
        # set_password hashes the value, a plain assignment would store it in clear text
        user.set_password(self.validated_data['password'])
        user.save()

        user_profile = UserProfile(
            user=user,
            type=self.validated_data['type'],
        )
        user_profile.save()

        return user

    def validate_email(self, value):
        """Reject duplicate addresses and store them lower cased."""
        new_mail = value.lower()
        if User.objects.filter(email=new_mail).exists():
            raise serializers.ValidationError('Email already exists')
        else:
            return new_mail

    def validate(self, values):
        """Both password fields have to match."""
        if values['password'] != values['repeated_password']:
            raise serializers.ValidationError('Password do not match')
        else:
            return values


class LoginSerializer(serializers.Serializer):
    """Checks the credentials and hands the matching user to the view."""

    username = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)

    def validate(self, values):
        new_username = values['username']
        user = User.objects.filter(username=new_username).first()

        if user:
            pw_valid = user.check_password(values['password'])

            if pw_valid:
                # the view needs the instance, so it travels on in validated_data
                values['user'] = user
                return values
            else:
                # same message for both cases, otherwise it would leak existing usernames
                raise serializers.ValidationError('Invalid Credentials')
        else:
            raise serializers.ValidationError('Invalid Credentials')


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# New serializer to change jwt login with username, not email.
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
             user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        data = super().validate({"username" : user.username, "password" : password})
        return data