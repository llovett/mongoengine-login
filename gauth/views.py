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
import smtplib
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
            hostname = settings.HOSTNAME if 'HOSTNAME' in dir(settings) else 'localhost'
            activate_uri = '/accounts/activate/'
            activate_link = 'http://{}{}{}'.format( hostname, activate_uri, stub.activationCode )
            email_subject = "Welcome to Obietaxi!"
            email_from = 'noreply@{}'.format( hostname )
            email_to = form.cleaned_data['username']
            msg_body = "Welcome to Obietaxi! Your account has already been created with this email address, now all you need to do is confirm your accout by clicking on the link below. If there is no link, you should copy & paste the address into your browser's address bar and navigate there.\n\n{}".format( activate_link )
            email_message = "\r\n".join( ["From: {}".format(email_from),
                                          "To: {}".format(email_to),
                                          "Subject: {}".format(email_subject),
                                          "",
                                          msg_body] )
            server = smtplib.SMTP( 'localhost' )
            server.sendmail( email_from, [email_to], email_message )
            server.quit()
            
            return HttpResponse("your user has been created as inactive")
        
    # Form needs to be rendered
    else:
        form = RegisterForm()

    # Render the form (possibly with errors if form did not validate)
    return render_to_response( 'register.html', locals(), context_instance=RequestContext(request) )

def activate( request, key ):
    # Try to find the user/stub to activate
    try:
        stub = UserLoginStub.objects( activationCode=key )
    except UserLoginStub.DoesNotExist:
        return HttpResponse("Invalid activation key.")

    # Activate the user, lose the stub
    user = stub.user
    user.is_active = True
    user.save()
    stub.delete()
    return HttpResponseRedirect( reverse('login_success') )

@login_required
def user_show( request ):
    username = request.user.username
    return render_to_response( 'success.html', context_instance=RequestContext(request) )

@login_required
def user_logout( request ):
    logout( request )
    return HttpResponseRedirect( reverse('main_page') )
