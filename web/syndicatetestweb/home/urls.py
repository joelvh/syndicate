from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
                       url(r'^$', 'home.views.home'),
                       url(r'^allvolumes/+$', 'home.views.allvolumes'),
                       url(r'^myvolumes/+$', 'home.views.myvolumes'),
                       url(r'^settings/+$', 'home.views.settings'),
                       url(r'^downloads/+$','home.views.downloads'),
)
