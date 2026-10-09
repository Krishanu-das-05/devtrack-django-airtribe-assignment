from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping),
    path("reporters/", views.reporters),
    path("issues/", views.issues),
]