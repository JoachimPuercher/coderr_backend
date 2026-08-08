from rest_framework import serializers


class OrderRetrieveWriteSerializer(serializers.ModelSerializer):

    class Meta:

        model = Order