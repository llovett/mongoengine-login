from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from forms import LoginForm, RegisterForm
from mongoengine.django.auth import User
from authentication import settings
from models import UserLoginStub

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

def register( request ):
    # Cannot register if logged in already
    if request.user.is_authenticated():
        return HttpResponseRedirect( reverse('login_url') )

    # The registration form
    form = None

    # Form has been submitted
    if request.method == 'POST':
        form = RegisterForm( request.POST )

        # Validate the registration form
        if form.is_valid():
            user = User.create_user( form.cleaned_data['username'],
                                     form.cleaned_data['password1'] )
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.is_active = False
            user.save()
            
            stub = UserLoginStub.objects.create( user=user )

            # TODO: send confirmation email
            return HttpResponse("your user has been created as inactive")

    # Form needs to be rendered
    else:
        form = RegisterForm()

    # Render the form (possibly with errors if form did not validate)
    return render_to_response( 'register.html', locals(), context_instance=RequestContext(request) )

@login_required
def user_show( request ):
    username = request.user.username
    return render_to_response( 'success.html', context_instance=RequestContext(request) )

@login_required
def user_logout( request ):
    logout( request )
    return HttpResponseRedirect( reverse('main_page') )
