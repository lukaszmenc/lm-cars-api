# Cars-API
Backend REST API which allows to add existing car models to database. It allows users to vote for their favourite cars and provides model popularity information. This app gets required data from vpic.nhtsa.dot.gov API.

## Installation
Create the ```.env``` file in the root of the project and insert your key/value pairs in the format shown in ```.env.example``` file.

You can also use default values from ```.env.example``` file by changing its name to ```.env```.

## Usage


### Run Cars-API
Run Cars-API locally using: 
```
docker-compose up --build
```
App will run on ```https://localhost:8000/```

### API endpoints

| Endpoint                  | HTTP method | Result                                                       | Parameters                                  |
| :------------------------ |:----------: | :----------------------------------------------------------: | :-----------------------------------------: |
| ```/api/cars```           | GET         | provide all cars entries                                     |                                             |
| ```/api/cars```           | POST        | add new car to database                                      | ```make```, ```model```                     |
| ```/api/rate```           | POST        | add rate to chosen car (from 1 to 5)                         | ```car_id```, ```rate```                    |
| ```/api/popular```        | GET         | provide all cars entries ordered by votes received           |                                             |
| ```/api/popular/:limit``` | GET         | provide n cars entries ordered by votes received, n = limit  |                                             |

## Tests
To run tests locally, simply run `python manage.py test`.

Note: Before running tests locally, install required packages using `pip install -r requirements`.

To run tests in docker container: `docker exec -it lm-cars-api_web_1 python manage.py test`