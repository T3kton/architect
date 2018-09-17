import hashlib
import base64

from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from architect.Project.models import Site
from architect.TimeSeries.models import CostTS, AvailabilityTS, ReliabilityTS, RawTimeSeries
from architect.Contractor.models import Complex, BluePrint
from architect.fields import MapField, script_name_regex, plan_name_regex
from architect.tcalc.parser import lint

cinp = CInP( 'Plan', '0.1', doc="""This is where the Deployment Plans and the
Models that relate the Plans to BluePrints and TimeSeries data
""" )


@cinp.model( not_allowed_verb_list=[ 'CALL' ], read_only_list=[ 'nonce_counter', 'last_change' ] )
class Plan( models.Model ):
  """
  Deployment Plan.  We can source multiple data streams and build for multiple
  BluePrints.  The values exported via the script (ie: the # values), will be matched
  to the Blueprint by matching the exported name to the BluePrint's name.  TimeSeries
  data (other than the TimmeSeries data from the Complex's attributes), are imported
  with the script_name as defined in the PlanTimeSeries model.
  hostname_pattern -> python.format format,
                       {plan} -> plan name (up to 50 chars)
                       {compex} -> complex name (up to 50 chars)
                       {blueprint} -> blueprint name (up to 50 chars)
                       {site} -> site name (up to 40 chars)
                       {nonce} -> nonce (random one-time use string, 26 chars)
    the target hostname is length 200 chars

  slots_per_complex -> NOTE: changing this value can cause a lot of Instances to be
  created/destroyed/moved.
  """

  name = models.TextField( max_length=200, primary_key=True )
  site = models.ForeignKey( Site, on_delete=models.CASCADE )
  description = models.CharField( max_length=200 )
  enabled = models.BooleanField( default=False )  # enabled to be scanned and updated that is, any existing resources will not be affected
  change_cooldown = models.IntegerField( default=300, help_text='number of seconds to wait after a change before re-evaluating the plan' )
  config_values = MapField( blank=True, help_text='Contracor style config values, which are loaded into Contractor\'s Structure model when the Structure is created' )
  last_change = models.DateTimeField( auto_now_add=True )
  max_inflight = models.IntegerField( default=2, help_text='number of things that can be changing at the same time' )

  hostname_pattern = models.CharField( max_length=100, default='{plan}-{blueprint}-{nonce}' )
  script = models.TextField()
  complex_list = models.ManyToManyField( Complex, through='PlanComplex' )
  blueprint_list = models.ManyToManyField( BluePrint, through='PlanBluePrint' )
  timeseries_list = models.ManyToManyField( RawTimeSeries, through='PlanTimeSeries' )
  slots_per_complex = models.IntegerField( default=100 )
  nonce_counter = models.IntegerField( default=1 )  # is hashed (with other stuff) to be used as the nonce string, https://stackoverflow.com/questions/4567089/hash-function-that-produces-short-hashes
  can_move = models.BooleanField( default=False )
  can_destroy = models.BooleanField( default=False )
  can_build = models.BooleanField( default=True )

  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def nextNonce( self ):
    plan = Plan.objects.select_for_update().get( name=self.name )
    counter = plan.nonce_counter
    plan.nonce_counter += 1
    plan.save()

    # nonce must be hostname safe and lowercase
    nonce = hashlib.md5()
    nonce.update( '{0:20d}'.format( counter ).encode() )
    nonce.update( self.name.encode() )

    return base64.b32encode( nonce.digest() ).strip( b'=' ).lower().decode()

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not plan_name_regex.match( self.name ):
      errors[ 'name' ] = '"{0}" is invalid'.format( self.name )

    if self.slots_per_complex < 1 or self.slots_per_complex > 5000:
      errors[ 'slots_per_complex' ] = 'must be from 1 to 5000'

    result = lint( self.script )
    if result is not None:
      errors[ 'script' ] = result

    if errors:
      raise ValidationError( errors )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Plan "{0}"'.format( self.name )


@cinp.model( not_allowed_verb_list=[] )
class PlanComplex( models.Model ):
  """
  Attaches a Plan to a Complex.
  """
  plan = models.ForeignKey( Plan, on_delete=models.CASCADE )
  complex = models.ForeignKey( Complex, on_delete=models.PROTECT )  # deleting this will cause the indexing to get messed up, have to deal with that before deleting
  cost = models.ForeignKey( CostTS, related_name='+', on_delete=models.PROTECT )  # 0 -> large value
  availability = models.ForeignKey( AvailabilityTS, related_name='+', on_delete=models.PROTECT )  # 0.0 -> 1.0
  reliability = models.ForeignKey( ReliabilityTS, related_name='+', on_delete=models.PROTECT )  # 0.0 -> 1.0
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  @cinp.action( return_type={ 'type': 'Map' }, paramater_type_list=[ { 'type': 'Integer', 'doc': 'number of seconds of data to retreieve' } ] )
  def graph_data( self, duration=3600 ):
    result = { 'graph': {}, 'value': {} }
    result[ 'graph' ][ 'cost' ] = self.cost.graph_data( duration )
    result[ 'graph' ][ 'availability' ] = self.availability.graph_data( duration )
    result[ 'graph' ][ 'reliability' ] = self.reliability.graph_data( duration )
    result[ 'value' ][ 'cost' ] = self.cost.last_value
    result[ 'value' ][ 'availability' ] = self.availability.last_value
    result[ 'value' ][ 'reliability' ] = self.reliability.last_value

    return result

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return PlanComplex.objects.filter( plan=plan )

  @cinp.list_filter( name='complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_complex( plan ):
    return PlanComplex.objects.filter( complex=complex )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}
    if errors:
      raise ValidationError( errors )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PlanComplex for Plan "{0}" to "{1}"'.format( self.plan, self.complex )

  class Meta:
    unique_together = ( ( 'plan', 'complex' ), )


@cinp.model( not_allowed_verb_list=[ 'CALL' ] )
class PlanBluePrint( models.Model ):
  """
  Attaches a Plan to a BluePrint
  """
  plan = models.ForeignKey( Plan, on_delete=models.CASCADE )
  blueprint = models.ForeignKey( BluePrint, on_delete=models.PROTECT  )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}
    if self.blueprint.name is None:
      errors[ 'blueprint' ] = 'Blueprint must have an assigned name'

    if errors:
      raise ValidationError( errors )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return PlanBluePrint.objects.filter( plan=plan )

  @cinp.list_filter( name='blueprint', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Contractor.models.BluePrint' } ] )
  @staticmethod
  def filter_blueprint( blueprint ):
    return PlanBluePrint.objects.filter( blueprint=blueprint )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PlanBluePrint for Plan "{0}" to "{1}" '.format( self.plan, self.blueprint.name )

  class Meta:
    unique_together = ( ( 'plan', 'blueprint' ), )


@cinp.model( not_allowed_verb_list=[ 'CALL' ] )
class PlanTimeSeries( models.Model ):
  """
  Attaches a Plan to a TimeSeries values (this is not the Cost/Availablilty/Reliability)
  values for a complex.  Can be pretty much any value, will apear in the Plan's
  Script with as the variable @<script_name>
  """
  plan = models.ForeignKey( Plan, on_delete=models.CASCADE )
  timeseries = models.ForeignKey( RawTimeSeries, related_name='+', on_delete=models.PROTECT )
  script_name = models.CharField( max_length=50 )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}
    if not script_name_regex.match( self.script_name ):
      errors[ 'script_name' ] = '"{0}" is invalid'.format( self.script_name )

    if errors:
      raise ValidationError( errors )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return PlanTimeSeries.objects.filter( plan=plan )

  @cinp.list_filter( name='timeseries', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.TimeSeries.models.RawTimeSeries' } ] )
  @staticmethod
  def filter_timeseries( timeseries ):
    return PlanTimeSeries.objects.filter( timeseries=timeseries )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'PlanTimeSeries for Plan "{0}" to "{1}" with name "{2}"'.format( self.plan, self.timeseries, self.script_name )

  class Meta:
    unique_together = ( ( 'plan', 'timeseries' ), )
