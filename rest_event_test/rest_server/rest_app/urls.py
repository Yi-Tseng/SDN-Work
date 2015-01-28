from django.conf.urls import url
from rest_app.views import HelloView

urlpatterns = [
    url(r'^hello$', HelloView.as_view()),
]
