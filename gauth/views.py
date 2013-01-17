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

GOOGLE_GET_ENDPOINT_URL = 'https://www.google.com/accounts/o8/id'

def login_view( request ):
    # Login form submitted
    if request.method == 'POST':
        error_msg = ''
        try:
            user = User.objects.get( username=request.POST['username'] )
            if user.check_password( request.POST['password'] ) and user.is_active:
                user.backend = 'mongoengine.django.auth.MongoEngineBackend'
                login( request, user )
                return HttpResponseRedirect( reverse('login_success') )
            else:
                error_msg = 'invalid login'
        except User.DoesNotExist:
            error_msg = 'invalid login'
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

def google_login( request ):
    import urllib2
    from urllib import urlencode
    from xml.dom import minidom
    from xml.parsers.expat import ExpatError

    ########################################
    def get_endpoint():
        '''
        Get Google's authentication endpoint.
        returns the url as a string

        '''
        # Get discovery URL
        try:
            response = urllib2.urlopen( GOOGLE_GET_ENDPOINT_URL )
        except urllib2.URLError:
            HttpResponse( "couldn't send discovery request to google" )

        # Parse XML response
        try:
            parsed = minidom.parseString( response.read() )
        except ExpatError as error:
            HttpResponse( "invalid xml: %s" % error.strerror() )
        URI = parsed.getElementsByTagName( 'URI' )
        if len(URI) <= 0 or len(URI[0].childNodes) <= 0:
            HttpResponse( "couldn't find endpoint URI in google's response" )

        return URI[0].childNodes[0].toxml()
    ########################################

    endpoint = str( get_endpoint() )
    params = {
        'openid.mode' : 'checkid_setup',
        'openid.ns' : 'http://specs.openid.net/auth/2.0',
        'openid.claimed_id' : 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.identity' : 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.return_to' : 'http://llovett.cs.oberlin.edu:8050'+reverse('google_login_success'),
#        'openid.assoc_handle' : ASSOC_HANDLE,  # TODO: figure this out
        'openid.realm' : 'http://llovett.cs.oberlin.edu:8050',

        'openid.ns.ax' : 'http://openid.net/srv/ax/1.0',
        'openid.ax.mode': 'fetch_request',
        'openid.ax.type.email' : 'http://axschema.org/contact/email',
        'openid.ax.type.firstname' : 'http://axschema.org/namePerson/first',
        'openid.ax.type.lastname' : 'http://axschema.org/namePerson/last',
        'openid.ax.required' : 'email,firstname,lastname'
    }

    return render_to_response( 'google_login.html',
                               locals(),
                               context_instance=RequestContext(request) )

def google_login_success( request ):
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    values = { p.split('.')[-1] : params[p] for p in params.keys() if 'value' in p }    
    
    mode = values['openid.mode']
    if mode != 'id_res':
        # The user declined to sign in at Google
        return HttpResponse( "could not complete authentication" )

    email = values['email']
    firstname = values['firstname']
    lastname = values['lastname']
    handle = params['openid.claimed_id']

    # Break apart the handle to find the user's ID
    # Assumes there are no other parameters attached to URL in 'openid.claimed_id'
    userid = handle.split("?")[-1].split("=")[-1]

    # TODO: Create a new user in database (if nonexistent), or log in

    return render_to_response( 'google_login_success.html',
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
        stub = UserLoginStub.objects.get( activationCode=key )
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
    return render_to_response( 'success.html',
                               locals(),
                               context_instance=RequestContext(request) )

@login_required
def user_logout( request ):
    logout( request )
    return HttpResponseRedirect( reverse('main_page') )
