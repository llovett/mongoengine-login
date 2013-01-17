from django.conf.urls import patterns, include, url
from gauth import views

urlpatterns = patterns('',
                       url( r'^$', views.user_show, name="main_page" ),
                       url( r'^accounts/login/$', views.login_view, name="login" ),
#                       url( r'^accounts/google/login/$', views.google_login, name="google_login" ),
                       url( r'^accounts/google/success/$', views.google_login_success, name="google_login_success" ),
                       url( r'^accounts/profile/$', views.user_show, name="login_success" ),
                       url( r'^accounts/logout/$', views.user_logout, name="logout" ),
                       url( r'^accounts/register/$', views.register, name="register" ),
                       url( r'^accounts/activate/([A-Fa-f0-9]+)/$', views.activate, name="activate" ),
)
