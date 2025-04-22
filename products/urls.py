from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CarsListView,
    CarCreateView,
    CarUpdateView,
    CarDetailView,
    CarDeleteView,
    CarsViewSets
    )

urlpatterns = [
    path('', CarsListView.as_view()),
    path('create', CarCreateView.as_view()),
    path('update/<int:pk>', CarUpdateView.as_view()),
    path('detail/<int:pk>', CarDetailView.as_view()),
    path('delete/<int:pk>', CarDeleteView.as_view()),
]

# router = DefaultRouter()
# router.register(r'all-methods/view-sets', CarsViewSets, basename='cars')
# urlpatterns += router.urls