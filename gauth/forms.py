from django import forms
import re

class LoginForm( forms.Form ):
    # Username is an email
    username = forms.EmailField()
    password = forms.CharField( widget=forms.PasswordInput(render_value=False),
                                max_length=20 )

class USPhoneNumberField( CharField ):
    '''
    Recognizes, cleans, and validates a US phone number.
    '''
    default_error_messages = {
        'invalid' : _('Not a valid phone number. Be sure to include area code.'),
    }

    PHONE_DIGITS_RE = re.compile(r'^(?:1-?)?(\d{3})[-\.]?(\d{3})[-\.]?(\d{4})$')

    def clean( self, value ):
        super( USPhoneNumberField, self ).clean( value )
        if value in EMPTY_VALUES:
            return ''
        value = re.sub( '(\(|\)|\s+)', '', smart_text(value) )
        mat = USPhoneNumberField.PHONE_DIGITS_RE.search( value )
        if m:
            return "{}-{}-{}".format( m.group(1), m.group(2), m.group(3) )
        raise forms.ValidationError( self.error_messages['invalid'] )

class RegisterForm( forms.Form ):
    # Username is an email
    username = forms.EmailField( label="email" )
    password1 = forms.CharField( widget=forms.PasswordInput(render_value=False),
                                 max_length=20,
                                 label="password" )
    password2 = forms.CharField( widget=forms.PasswordInput(render_value=False),
                                 max_length=20,
                                 label="password (again)" )
    first_name = forms.CharField( label="first name" )
    last_name = forms.CharField( label="last name" )
    phone = USPhoneNumberField()

