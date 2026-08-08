from rest_framework import serializers
from auth_app.models import UserProfile
from django.contrib.auth.models import User
from offers_app.models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):

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
    # id = serializers.IntegerField(source="details.id")
    # url = serializers.HyperlinkedRelatedField()
    class Meta:

        model = OfferDetail
        fields = ["id"]
class OfferListSerializer(serializers.ModelSerializer):

    user = serializers.IntegerField(source="user_id")
    details = OfferDetailLinkSerializer(many=True)
    class Meta:

        model = Offer

        fields = ["id", "user", "title", "image", "description", "created_at", "updated_at", "details"] 


