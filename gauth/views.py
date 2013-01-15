from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from forms import LoginForm
from mongoengine.django.auth import User
from authentication import settings

def login_view( request ):
    # Login form submitted
    if request.method == 'POST':
        error_msg = ''
        try:
            user = User.objects.get( username=request.POST['username'] )
            if user.check_password( request.POST['password'] ):
                user.backend = 'mongoengine.django.auth.MongoEngineBackend'
                login( request, user )
                return HttpResponseRedirect( reverse('login_success') )
            else:
                error_msg = 'password incorrect'
        except User.DoesNotExist:
            error_msg = 'user does not exist'
        form = LoginForm()
        return render_to_response( 'login.html', locals(), context_instance=RequestContext(request) )
    # Login form needs rendering
    else:
        if request.user.is_authenticated():
            return redirect( user_show )
        form = LoginForm()
        return render_to_response( 'login.html',
                                   locals(),
                                   context_instance=RequestContext(request) )

@login_required
def user_show( request ):
    username = request.user.username
    return render_to_response( 'success.html', context_instance=RequestContext(request) )

@login_required
def user_logout( request ):
    logout( request )
    return HttpResponseRedirect( reverse('main_page') )
