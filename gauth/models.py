import mongoengine as mdb
from random import choice
from datetime import datetime

class UserLoginStub( mdb.Document ):
    '''
    Models a User about to login
    '''
    user = mdb.ReferenceField( 'mongoengine.django.auth.User' )
    activationCode = mdb.StringField( max_length=100 )
    date = mdb.DateTimeField()

    def save( self, *args, **kwargs ):
        # Assign a random activation code
        self.activationCode = ''.join([choice('abcdef1234567890') for i in xrange(80)])
        # Use current time
        self.date = datetime.now()
        super( UserLoginStub, self ).save( *args, **kwargs )

    # Special handling in the database:
    # No more than 10,000 documents,
    # No more than 20,000,000 bytes (20 MB)
    meta = { 'max_documents':10000, 'max_size':20000000 }
        
