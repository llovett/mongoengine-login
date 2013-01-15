from django import forms

class LoginForm( forms.Form ):
    # Username is an email
    username = forms.EmailField()
    password = forms.CharField( widget=forms.PasswordInput(render_value=False),
                                max_length=10 )
