import requests_cache

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Car
from .serializers import CarSerializer, PopularSerializer, CarRateSerializer
from .utils import verify_car


ONE_DAY = 60 * 60 * 24
requests_cache.install_cache("cars_cache", backend="memory", expire_after=ONE_DAY)


class CarList(APIView):
    def get(self, request):
        cars = Car.objects.all()
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)

    def post(self, request):
        make = request.data.get("make")
        model = request.data.get("model")

        verify_car(make, model)

        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RateView(APIView):
    def post(self, request):
        serializer = CarRateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PopularList(APIView):
    def get(self, request, limit=None):
        cars = sorted(Car.objects.all(), key=lambda a: a.votes_cnt, reverse=True)[
            :limit
        ]
        serializer = PopularSerializer(cars, many=True)
        return Response(serializer.data)
