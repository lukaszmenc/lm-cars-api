import responses
import requests_cache
from requests.exceptions import ConnectionError

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from .models import Car, CarRate
from .serializers import PopularSerializer
from .utils import (
    verify_car,
    ModelDoesNotExist,
    MakeDoesNotExist,
    ConnectionErrorHandler,
)


def mock_request(response, make, response_status=200, body=None):
    responses.reset()
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{make}?format=json"
    responses.add(responses.GET, url, json=response, status=response_status, body=body)


class TestUtils(APITestCase):
    def tearDown(self):
        requests_cache.clear()

    def test_verify_car(self):
        """
        Returns None if make and model configuration exists.
        """
        make = "Jeep"
        model = "Cherokee"
        mock_request({"Results": [{"Model_Name": "Cherokee"}]}, make)

        self.assertIsNone(verify_car(make, model))

    def test_verify_car_make_does_not_exist(self):
        """
        Raises exception if make does not exist.
        """
        make = "FakeName"
        model = "Cherokee"
        mock_request({"Results": []}, make)

        self.assertRaises(MakeDoesNotExist, verify_car, make, model)

    def test_verify_car_model_does_not_exist(self):
        """
        Raises exception if model does not exist.
        """
        make = "Jeep"
        model = "FakeModel"
        mock_request({"Results": [{"Model_Name": "Cherokee"}]}, make)

        self.assertRaises(ModelDoesNotExist, verify_car, make, model)

    def test_verify_car_connection_error(self):
        """
        Raises exception icase of connection error.
        """
        make = "Jeep"
        model = "Cherokee"
        mock_request(None, make, 500, ConnectionError())

        self.assertRaises(ConnectionErrorHandler, verify_car, make, model)


class CarModelTests(APITestCase):
    def setUp(self):
        car = Car.objects.create(pk=1, make="Audi", model="A4")
        Car.objects.create(pk=2, make="Volkswagen", model="Golf")
        CarRate.objects.create(car_id=car, rate=3)
        CarRate.objects.create(car_id=car, rate=4)

    def test_get_rating(self):
        """
        avg_rate() returns result of division if there are some votes.
        """
        self.assertEquals(Car(pk=1).avg_rate, 3.5)

    def test_avg_rate_no_votes(self):
        """
        avg_rate() returns 'None' if there is no votes for a car.
        """
        self.assertEquals(Car(pk=2).avg_rate, None)


class CarViewTest(APITestCase):
    def setUp(self):
        responses.start()
        Car.objects.create(make="Audi", model="A4")
        Car.objects.create(make="Volkswagen", model="Golf")
        Car.objects.create(make="Honda", model="Civic")

    def tearDown(self):
        requests_cache.clear()

    def test_car_view_get(self):
        """
        Gets data properly.
        """
        response = self.client.get(reverse("cars:car_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_car_view_post(self):
        """
        Posts data properly.
        """
        data = {"make": "Jeep", "model": "Cherokee"}
        mock_request({"Results": [{"Model_Name": "Cherokee"}]}, data["make"])

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["make"], data["make"])
        self.assertEqual(r.data["model"], data["model"])

    @responses.activate
    def test_car_view_post_case_insensivity(self):
        """
        Posts data properly, request case format does not match external API response.
        """
        data = {"make": "Jeep", "model": "cherOKEE"}
        mock_request({"Results": [{"Model_Name": "Cherokee"}]}, data["make"])

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["make"], data["make"])
        self.assertEqual(r.data["model"], data["model"])

    @responses.activate
    def test_car_view_post_make_does_not_exists(self):
        """
            Does not allow to insert not existing make to database.
        """
        data = {"make": "FakeMake", "model": "Cherokee"}
        mock_request({"Results": []}, data["make"])

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, {"detail": "Requested make does not exist."})

    @responses.activate
    def test_car_view_post_model_does_not_exists(self):
        """
            Does not allow to insert not existing model to database.
        """
        data = {"make": "Jeep", "model": "FakeModel"}
        mock_request(
            {"Results": [{"Model_Name": "Cherokee"}, {"Model_Name": "Wrangler"}]},
            data["make"],
        )

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data, {"detail": "Requested model does not exist."})

    @responses.activate
    def test_car_view_post_car_already_exists(self):
        """
        Does not allow to insert car which is already in database.
        """
        data = {"make": "Honda", "model": "Civic"}
        mock_request({"Results": [{"Model_Name": "Civic"}]}, data["make"])

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.data["non_field_errors"][0],
            "The fields make, model must make a unique set.",
        )

        responses.reset()

    @responses.activate
    def test_car_view_post_external_api_not_responding(self):
        data = {"make": "Jeep", "model": "Cherokee"}
        mock_request(None, data["make"], 500, ConnectionError())

        r = self.client.post(reverse("cars:car_list"), data, format="json")

        self.assertEqual(r.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            r.data,
            {"detail": "Could not reach external API. Check your Internet connection."},
        )


class RateViewTests(APITestCase):
    def setUp(self):
        Car.objects.create(pk=1, make="Audi", model="A4")

    def test_rate_view_post(self):
        """
        Posts data properly.
        """
        data = {"car_id": 1, "rate": 3}
        response = self.client.post(reverse("cars:rate"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, data)

    def test_rate_view_post_rate_too_high(self):
        """
        Does not allow to rate greater than 5.
        """
        response = self.client.post(
            reverse("cars:rate"), {"car_id": 1, "rate": 6}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["rate"][0]),
            "Ensure this value is less than or equal to 5.",
        )

    def test_rate_view_post_rate_too_low(self):
        """
        Does not allow to rate less than 0.
        """
        response = self.client.post(
            reverse("cars:rate"), {"car_id": 1, "rate": 0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["rate"][0]),
            "Ensure this value is greater than or equal to 1.",
        )

    def test_rate_view_post_rate_wrong_type(self):
        """
        Returns error message if rate is not integer.
        """
        response = self.client.post(
            reverse("cars:rate"), {"car_id": 1, "rate": "one"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["rate"][0]), "A valid integer is required.")

    def test_rate_view_post_not_existing_car(self):
        """
        Returns error message in case of not existing car_id.
        """
        response = self.client.post(
            reverse("cars:rate"), {"car_id": 2, "rate": 3}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["car_id"][0]), 'Invalid pk "2" - object does not exist.'
        )


class PopularViewTests(APITestCase):
    def setUp(self):
        car1 = Car.objects.create(make="Audi", model="A4")
        car2 = Car.objects.create(make="Volkswagen", model="Golf")
        car3 = Car.objects.create(make="Honda", model="Civic")
        Car.objects.create(make="Tesla", model="Model X")
        Car.objects.create(make="Toyota", model="Corolla")
        Car.objects.create(make="BMW", model="X1")
        CarRate.objects.create(car_id=car1, rate=3)
        CarRate.objects.create(car_id=car1, rate=4)
        CarRate.objects.create(car_id=car2, rate=3)
        CarRate.objects.create(car_id=car2, rate=4)
        CarRate.objects.create(car_id=car2, rate=5)
        CarRate.objects.create(car_id=car3, rate=4)
        CarRate.objects.create(car_id=car3, rate=2)
        CarRate.objects.create(car_id=car3, rate=3)
        CarRate.objects.create(car_id=car3, rate=4)

    def test_popular_view_get(self):
        """
        Gets data properly, sorts them descending by votes.
        """
        data = sorted(Car.objects.all(), key=lambda a: a.votes_cnt, reverse=True)
        serializer = PopularSerializer(data, many=True)
        response = self.client.get(reverse("cars:popular"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_popular_view_get_limit(self):
        """
        Gets data properly, checks if proper ammount of objects is returned base on limit parameter.
        """
        data = sorted(Car.objects.all(), key=lambda a: a.votes_cnt, reverse=True)[:5]
        serializer = PopularSerializer(data, many=True)
        response = self.client.get(reverse("cars:popular_limit", args=[5]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 5)
