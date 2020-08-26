from rest_framework import serializers
from .models import Car, CarRate


class CarSerializer(serializers.ModelSerializer):
    avg_rate = serializers.ReadOnlyField()

    class Meta:
        model = Car
        fields = ("id", "make", "model", "avg_rate")


class CarRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarRate
        fields = ("car_id", "rate")


class PopularSerializer(serializers.ModelSerializer):
    votes_cnt = serializers.ReadOnlyField()

    class Meta:
        model = Car
        fields = ("make", "model", "votes_cnt")
