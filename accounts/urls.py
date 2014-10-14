from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^profile/?$', 'accounts.views.profile', name='profile'),
    url(r'^me/?$', 'accounts.views.me', name='me'),
    url(r'^register/?$', 'accounts.views.register', name='register'),
    url(r'^login/?$', 'accounts.views.login', name='login'),
    url(r'^logout/?$', 'accounts.views.logout', name='logout'),
    url(r'^list/?$', 'accounts.views.list', name='list'),
)
