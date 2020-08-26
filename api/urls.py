from django.urls import path

from . import views


app_name = "cars"
urlpatterns = [
    path("cars/", views.CarList.as_view(), name="car_list"),
    path("rate/", views.RateView.as_view(), name="rate"),
    path("popular/", views.PopularList.as_view(), name="popular"),
    path("popular/<int:limit>/", views.PopularList.as_view(), name="popular_limit"),
]
