from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'rest_server.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^', include('rest_app.urls')),
)
