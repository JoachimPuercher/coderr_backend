from rest_framework import serializers
from auth_app.models import UserProfile
from django.contrib.auth.models import User
class ProfilSerializer(serializers.ModelSerializer):
    """Full profile for the owner: flattens the related User onto the profile."""

    # source='user.…' pulls the value out of the related User instead of the profile
    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')

    class Meta:

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at'
            ]

        read_only_fields= [
            'file',
            'type',
            'created_at'
        ]

    def update(self, instance, validated_data):
        """Update the profile and the related user."""
        # the nested user fields cannot be saved by the default update, so they go first
        user_data = validated_data.pop('user', {})

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        return super().update(instance, validated_data)


class BusinessProfilSerializer(serializers.ModelSerializer):
    """Read-only business profile as shown in the provider list."""

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    class Meta:

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
        ]
        read_only_fields = [
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type'
        ]


class CustomerProfilSerializer(serializers.ModelSerializer):
    """Read-only customer profile, a smaller field set than the business one."""

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:

        model = UserProfile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'uploaded_at',
            'type',
        ]
        read_only_fields = [
            'file',
            'uploaded_at',
            'type'
        ]