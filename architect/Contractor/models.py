import re

from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

SCALER_CHOICES = ( ( 'none', 'None' ), ( 'step', 'Step' ), ( 'linear', 'Linear' ) )

name_regex = re.compile( '^[a-zA-Z0-9][a-zA-Z0-9_\-]*$' )

cinp = CInP( 'Contractor', '0.1' )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'CALL' ] )
class Complex( models.Model ):   # TODO: ReadOnly from API
  name = models.CharField( max_length=40, primary_key=True )  # also the id on contractor
  site = models.ForeignKey( 'Project.Site' )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )

    errors = {}
    if self.name is not None and not name_regex.match( self.name ):
      errors[ 'name' ] = '"{0}" is invalid'.format( self.name )

    if errors:
      raise ValidationError( errors )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Complex "{0}" in "{1}"'.format( self.name, self.site_id )


@cinp.model( not_allowed_verb_list=[ 'UPDATE', 'DELETE', 'CREATE', 'CALL' ] )
class BluePrint( models.Model ):   # TODO: ReadOnly from API
  contractor_id = models.CharField( max_length=40, unique=True, blank=True, null=True )
  name = models.CharField( max_length=50, unique=True, blank=True, null=True )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    if not self.name:
      self.name = None

    if not self.contractor_id:
      self.contractor_id = None

    errors = {}
    if self.name is not None and not name_regex.match( self.name ):
      errors[ 'name' ] = '"{0}" is invalid'.format( self.name )

    if errors:
      raise ValidationError( errors )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'BluePrint "{0}" name: "{1}"'.format( self.contractor_id, self.name )
