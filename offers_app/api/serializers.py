from rest_framework import serializers
from auth_app.models import UserProfile
from django.contrib.auth.models import User
from offers_app.models import Offer, OfferDetail
from django.db.models import Min, Max

class OfferDetailSerializer(serializers.ModelSerializer):

    price = serializers.DecimalField(decimal_places=2, coerce_to_string=False, max_digits=10)
    class Meta:

        model = OfferDetail

        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type' 
        ]
        read_only_fields = ['id']


class OfferWriteSerializer(serializers.ModelSerializer):

    details = OfferDetailSerializer(many=True)

    class Meta:

        model = Offer

        fields = [
            'id',
            'title',
            'image',
            'description',
            'details'
        ]
        read_only_fields = ['id']

    def update(self, instance, validated_data):

        details_data = validated_data.pop("details", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if details_data is not None:
            for detail_data in details_data:
                offer_type = detail_data.get("offer_type")
                if not offer_type:
                    raise serializers.ValidationError("Every detail must contain an offer_type.")
                detail = instance.details.filter(offer_type=offer_type).first()
                if detail is None:
                    raise serializers.ValidationError(f"There is no detail with offer_type {offer_type}.")
                for attr, value in detail_data.items():
                    setattr(detail, attr, value)
                detail.save()

        return instance

    def create(self, validated_data):

        details_data = validated_data.pop('details')
        detail_choices = []
        for i in details_data:
            detail_choices.append(i["offer_type"])

        if len(details_data) == 3:
            if detail_choices[0] != detail_choices[1] != detail_choices[2] != detail_choices[0]:
                offer = Offer.objects.create(**validated_data)
                for detail in details_data:
                    OfferDetail.objects.create(offer=offer, **detail)
                return offer
            else:
                raise serializers.ValidationError("There musst be exact three different details.")
        else:
            raise serializers.ValidationError("Missing details, there musst be exact three details.")

class OfferDetailLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name = "offerdetails", lookup_url_kwarg = "id")
    class Meta:

        model = OfferDetail
        fields = ["id", "url"]


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = ["first_name", "last_name", "username"]

class OfferRetrieveSerializer(serializers.ModelSerializer):

    user = serializers.IntegerField(source="user_id", read_only=True)
    details = OfferDetailLinkSerializer(many=True)
    min_price = serializers.FloatField(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:

        model = Offer

        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time"
            ]


class OfferListSerializer(OfferRetrieveSerializer):

    user_details = UserDetailSerializer(source="user")

    class Meta(OfferRetrieveSerializer.Meta):

        fields = OfferRetrieveSerializer.Meta.fields + ["user_details"]
