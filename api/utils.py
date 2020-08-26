import requests
from rest_framework.exceptions import APIException


class ModelDoesNotExist(APIException):
    status_code = 400
    default_detail = "Requested model does not exist."
    default_code = "invalid_model"


class MakeDoesNotExist(APIException):
    status_code = 400
    default_detail = "Requested make does not exist."
    default_code = "invalid_make"


class ConnectionErrorHandler(APIException):
    status_code = 500
    default_detail = "Could not reach external API. Check your Internet connection."
    default_code = "connection_failure"


def verify_car(make, model):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{str(make)}?format=json"

    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise ConnectionErrorHandler()

    result = response.json()
    if len(result["Results"]) > 0:
        if any(i["Model_Name"].upper() == model.upper() for i in result["Results"]):
            return
        raise ModelDoesNotExist()
    raise MakeDoesNotExist()
