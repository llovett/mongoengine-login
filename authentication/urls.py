from django.conf.urls import patterns, include, url
from gauth import views

urlpatterns = patterns('',
                       url( r'^$', views.user_show, name="main_page" ),
                       url( r'^accounts/login/$', views.login_view ),
                       url( r'^accounts/profile/$', views.user_show, name="login_success" ),
                       url( r'^accounts/logout/$', views.user_logout, name="logout_url" ),
)
