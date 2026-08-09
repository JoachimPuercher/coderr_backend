from rest_framework import serializers
from reviews_app.models import Review


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:

        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at"
        ]

        read_only_fields = [
            "id",
            "reviewer",
            "created_at",
            "updated_at"
        ]

    def validate(self, attrs):
        user = attrs["business_user"]
        reviewer = self.context["request"].user
        exists = Review.objects.filter(reviewer=reviewer, business_user=user).exists()
        if exists:
            raise serializers.ValidationError({"error" : "You have already sent a review to that business."})
        else:
            return attrs


class ReviewUpdateSerializer(ReviewSerializer):

    class Meta(ReviewSerializer.Meta):

        read_only_fields = ReviewSerializer.Meta.read_only_fields + ["business_user"]

    def validate(self, attrs):
        sent = set(self.initial_data)
        allowed = set(attrs)
        too_much = sent - allowed

        if too_much:
            raise serializers.ValidationError(f"Not allowed. {", ".join(too_much)}")
        else:
            return attrs
        
