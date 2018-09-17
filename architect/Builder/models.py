import string
import random

from django.db import models

from cinp.orm_django import DjangoCInP as CInP
from django.core.exceptions import ValidationError

from architect.fields import JSONField
from architect.Contractor.models import Complex, BluePrint
from architect.Plan.models import Plan

from architect.Contractor.Contractor import getContractor

cinp = CInP( 'Builder', '0.1', doc="""This is where the Instances genenerated
from the plan, as well as the models to support the handeling of the Instances
are handled.
""" )

INSTANCE_STATE_CHOICES = ( 'new', 'built', 'destroyed', 'processing' )
ACTION_ACTION_CHOICES = ( 'build', 'destroy', 'rebuild', 'move' )
JOB_TARGET_CHOICES = ( 'foundation', 'structure' )
JOB_TASK_CHOICES = ( 'build', 'destroy', 'move' )
JOB_STATE_CHOICES = ( 'new', 'waiting', 'done', 'error' )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'UPDATE', 'CALL' ], property_list=( 'type', ), constant_set_map={ 'state': INSTANCE_STATE_CHOICES } )
class Instance( models.Model ):
  plan = models.ForeignKey( Plan, on_delete=models.PROTECT )
  state = models.CharField( max_length=10, choices=zip( INSTANCE_STATE_CHOICES, INSTANCE_STATE_CHOICES ) )
  blueprint = models.ForeignKey( BluePrint, on_delete=models.PROTECT )
  hostname = models.CharField( max_length=200, unique=True )
  foundation_id = models.IntegerField( null=True, blank=True, unique=True )  # Contractor foundation id
  structure_id = models.IntegerField( null=True, blank=True, unique=True )  # Contractor structure id
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  @property
  def subclass( self ):
    try:
      return self.typedinstance
    except AttributeError:
      pass

    try:
      return self.complexinstance
    except AttributeError:
      pass

    return self

  @property
  def type( self ):
    real = self.subclass
    if real != self:
      return real.type

    return 'Unknown'

  @staticmethod
  def create( *args ):
    raise Exception( 'Generic Instance not Createable' )

  def destroy( self ):
    self.setUnrequested()

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    if not self.foundation_id:
      self.foundation_id = None

    if not self.structure_id:
      self.structure_id = None

    errors = {}

    if errors:
      raise ValidationError( errors )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return Instance.objects.filter( plan=plan )

  @cinp.list_filter( name='complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_complex( complex ):
    return Instance.objects.filter( complex=complex )

  @cinp.list_filter( name='plan_complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_plan_complex( plan, complex ):
    return Instance.objects.filter( plan=plan, complex=complex )

  @cinp.list_filter( name='plan_state', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'String', 'choice_list': INSTANCE_STATE_CHOICES } ] )
  @staticmethod
  def filter_plan_state( plan, state ):
    return Instance.objects.filter( plan=plan, state=state )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Instance({0}) "{1}" of "{2}"'.format( self.pk, self.hostname, self.plan.name )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'UPDATE', 'CALL' ], property_list=( 'type', ), constant_set_map={ 'state': INSTANCE_STATE_CHOICES } )
class TypedInstance( Instance ):
  site_id = models.CharField( max_length=40 )
  foundation_type = models.CharField( max_length=50 )
  address_block_id = models.IntegerField()
  address_offset = models.IntegerField()

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Typed'

  @staticmethod
  def create( plan, site_id, foundation_type, blueprint_name, hostname, address_block_id, address_offset ):
    print(  plan, foundation_type, blueprint_name, hostname )
    result = TypedInstance( site_id=site_id, plan=plan, foundation_type=foundation_type, blueprint=BluePrint.objects.get( name=blueprint_name ) )
    result.state = 'new'
    result.address_block_id = address_block_id
    result.address_offset = address_offset
    result.hostname = hostname
    result.full_clean()
    result.save()
    return result

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return TypedInstance.objects.filter( plan=plan )

  @cinp.list_filter( name='complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_complex( complex ):
    return TypedInstance.objects.filter( complex=complex )

  @cinp.list_filter( name='plan_complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_plan_complex( plan, complex ):
    return TypedInstance.objects.filter( plan=plan, complex=complex )

  @cinp.list_filter( name='plan_state', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'String', 'choice_list': INSTANCE_STATE_CHOICES } ] )
  @staticmethod
  def filter_plan_state( plan, state ):
    return TypedInstance.objects.filter( plan=plan, state=state )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'TypedInstance({0}) "{1}" of "{2}"'.format( self.pk, self.hostname, self.plan.name )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'UPDATE', 'CALL' ], property_list=( 'type', ), constant_set_map={ 'state': INSTANCE_STATE_CHOICES } )
class ComplexInstance( Instance ):
  """
  A Deployment Instance, These are created and destroyed when the plan is evaluated.
  Actions are created to change the state of each Instance.
  """
  nonce = models.CharField( max_length=26, unique=True )
  complex = models.ForeignKey( Complex, on_delete=models.PROTECT )

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Complex'

  @staticmethod
  def create( plan, complex_tsname, blueprint_name ):
    result = Instance( plan=plan, complex=Complex.objects.get( tsname=complex_tsname ), blueprint=BluePrint.objects.get( name=blueprint_name ) )
    result.state = 'new'
    result.nonce = plan.dynamicplan.nextNonce()
    result.hostname = plan.dynamicplan.hostname_pattern.format( **{ 'plan': plan.name, 'compex': complex_tsname, 'blueprint': blueprint_name, 'site': result.complex.site_id, 'nonce': result.nonce } )
    result.full_clean()
    result.save()
    return result

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return ComplexInstance.objects.filter( plan=plan )

  @cinp.list_filter( name='complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_complex( complex ):
    return ComplexInstance.objects.filter( complex=complex )

  @cinp.list_filter( name='plan_complex', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'Model', 'model': 'architect.Contractor.models.Complex' } ] )
  @staticmethod
  def filter_plan_complex( plan, complex ):
    return ComplexInstance.objects.filter( plan=plan, complex=complex )

  @cinp.list_filter( name='plan_state', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' }, { 'type': 'String', 'choice_list': INSTANCE_STATE_CHOICES } ] )
  @staticmethod
  def filter_plan_state( plan, state ):
    return ComplexInstance.objects.filter( plan=plan, state=state )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'ComplexInstance({0}) "{1}" of "{2}" in "{3}"'.format( self.pk, self.hostname, self.plan.name, self.complex )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'UPDATE', 'CALL' ], property_list=( 'progress', ), constant_set_map={ 'action': ACTION_ACTION_CHOICES } )
class Action( models.Model ):
  """
  Actions are in flight action that is building, destroying, rebuilding or moving an
  Instance.
  """
  instance = models.OneToOneField( Instance, on_delete=models.PROTECT )
  action = models.CharField( max_length=10, choices=zip( ACTION_ACTION_CHOICES, ACTION_ACTION_CHOICES ) )
  state = JSONField( default={}, blank=True )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  @property
  def progress( self ):
    if not self.state:
      return 'Not Started'

    if self.state[ 'done' ] is True:
      return 'Done'

    return '{0:3.2f}'.format( ( self.state[ 'count' ] - len( self.state[ 'todo' ] ) ) * 100.0 / ( self.state[ 'count' ] + 1 ) )  # +1 is so it dosen't reach 100% when the todo is empty, ie: on the last thing

  @staticmethod
  def create( instance, action ):
    action = Action( instance=instance, action=action, state={} )
    action.full_clean()
    action.save()

  def start( self ):
    instance = self.instance.subclass
    if self.action == 'build' and ( instance.foundation_id is None or instance.structure_id is None ):
      contractor = getContractor()
      if instance.type == 'Complex':
        if instance.foundation_id is None:
          instance.foundation_id = contractor.createComplexFoundation( instance.complex.contractor_id, instance.blueprint.contractor_id, instance.hostname )

        if instance.structure_id is None:
          instance.structure_id = contractor.createComplexStructure( instance.site_id, instance.foundation_id, instance.blueprint.contractor_id, instance.hostname, instance.plan.config_values, instance.address_block_id, instance.offset )

      elif instance.type == 'Typed':
        if instance.foundation_id is None:
          if instance.structure_id is not None:
            raise ValueError( 'non ComplexInstance is missing foundation id but not structure id' )

          instance.foundation_id, instance.structure_id = contractor.createFoundationStructure( instance.foundation_type, instance.site_id, instance.blueprint.contractor_id, instance.hostname, instance.plan.config_values, instance.address_block_id, instance.address_offset )
          instance.state = 'processing'
          instance.full_clean()
          instance.save()

          self.state[ 'todo' ] = []
          self.state[ 'count' ] = 0
          self.state[ 'current' ] = None
          self.state[ 'done' ] = False
          self.full_clean()
          self.save()
          return

      else:
        raise ValueError( 'Unknown instance type "{0}"'.format( self.instance.type ) )

    print( "---------{0}--------".format( self.instance.pk ) )

    instance.state = 'processing'
    instance.full_clean()
    instance.save()

    if self.action == 'build':
      self.state[ 'todo' ] = [ ( 'build', 'foundation' ), ( 'build', 'structure' ) ]

    elif self.action == 'destroy':
      self.state[ 'todo' ] = [ ( 'destroy', 'structure' ), ( 'destroy', 'foundation' ) ]

    elif self.action == 'rebuild':
      self.state[ 'todo' ] = [ ( 'destroy', 'structure' ), ( 'destroy', 'foundation' ), ( 'build', 'foundation' ), ( 'build', 'structure' ) ]

    elif self.action == 'move':
      self.state[ 'todo' ] = [ ( 'move', 'foundation' ) ]

    self.state[ 'count' ] = len( self.state[ 'todo' ] )
    self.state[ 'current' ] = None
    self.state[ 'done' ] = False
    self.full_clean()
    self.save()

  def run( self ):
    if not self.state:
      return

    print( '^^^^^^^^^^^^^^^^ {0}'.format( self.state ) )

    if self.state[ 'done' ] is True:
      if self.action == 'build':
        self.instance.state = 'built'
        self.instance.full_clean()
        self.instance.save()

      elif self.action == 'destroy':
        self.instance.foundation_id = None
        self.instance.structure_id = None
        self.instance.state = 'destroyed'
        self.instance.full_clean()
        self.instance.save()

      self.delete()

    if self.state[ 'current' ] is None:
      if len( self.state[ 'todo' ] ) == 0:
        self.state[ 'done' ] = True
        self.state[ 'current' ] = ''

      else:
        ( task, target ) = self.state[ 'todo' ].pop( 0 )
        job = Job( action=self, target=target, task=task )
        job.state = 'new'
        job.full_clean()
        job.save()
        self.state[ 'current' ] = '{0} {1}'.format( task, target )

      self.full_clean()
      self.save()

  def jobComplete( self, job ):
    self.state[ 'current' ] = None
    self.full_clean()
    self.save()
    job.delete()

  @cinp.list_filter( name='instance', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Builder.models.Instance' } ] )
  @staticmethod
  def filter_instance( instance ):
    return Action.objects.filter( instance=instance )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return Action.objects.filter( instance__plan=plan )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Action({0}) ""{1}" for "{2}"'.format( self.pk, self.action, self.instance )


@cinp.model( not_allowed_verb_list=[ 'DELETE', 'CREATE', 'UPDATE' ], hide_field_list=[ 'web_hook_token' ], constant_set_map={ 'target': JOB_TARGET_CHOICES, 'task': JOB_TASK_CHOICES, 'state': JOB_STATE_CHOICES } )
class Job( models.Model ):
  """
  Job is the individual step for each action.  Contracor breaks up each deployable
  unit into two parts, a Foundation and Structure.  These Jobs track Contractor's
  progress in destroy/createing/moving each of these parts.
  """
  action = models.OneToOneField( Action, on_delete=models.PROTECT )
  target = models.CharField( max_length=10, choices=zip( JOB_TARGET_CHOICES, JOB_TARGET_CHOICES ) )
  task = models.CharField( max_length=7, choices=zip( JOB_TASK_CHOICES, JOB_TASK_CHOICES ) )
  state = models.CharField( max_length=7, choices=zip( JOB_STATE_CHOICES, JOB_STATE_CHOICES ) )
  web_hook_token = models.CharField( max_length=40, blank=True, null=True )
  updated = models.DateTimeField( auto_now=True )
  created = models.DateTimeField( auto_now_add=True )

  def _registerWebHook( self, contractor ):
    self.web_hook_token = ''.join( random.choice( string.ascii_letters ) for _ in range( 40 ) )
    self.state = 'waiting'
    self.full_clean()
    contractor.registerWebHook( self.target, self.pk, ( self.action.instance.foundation_id if self.target == 'foundation' else self.action.instance.structure_id ), self.web_hook_token )
    self.save()

  def run( self ):
    if self.state == 'done':
      self.action.jobComplete( self )
      return

    contractor = getContractor()
    if self.state == 'new':
      if self.task == 'build':
        if self.target == 'foundation':
          contractor.buildFoundation( self.action.instance.foundation_id )
        else:
          contractor.buildStructure( self.action.instance.structure_id )

      elif self.task == 'destroy':
        if self.target == 'foundation':
          contractor.destroyFoundation( self.action.instance.foundation_id )
        else:
          contractor.destroyStructure( self.action.instance.structure_id )

    else:
      raise Exception( 'Not implemented' )

    self._registerWebHook( contractor )

    # ignore every other state

  @cinp.action( return_type='String', paramater_type_list=[ 'String', 'String', 'String', 'String', 'Integer', 'Integer' ] )
  def jobNotify( self, token, target, script, at, foundation=None, structure=None ):
    if token != self.web_hook_token or target != self.target:
      return 'invalid token and/or target'

    if ( self.target == 'foundation' and foundation != self.action.instance.foundation_id ) or ( self.target == 'structure' and structure != self.action.instance.structure_id ):
      return 'invalid id'

    self.web_hook_token = None
    self.state = 'done'
    self.full_clean()
    self.save()

    return 'thanks'

  @cinp.list_filter( name='action', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Builder.models.Action' } ] )
  @staticmethod
  def filter_action( action ):
    return Job.objects.filter( action=action )

  @cinp.list_filter( name='instance', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Builder.models.Instance' } ] )
  @staticmethod
  def filter_instance( instance ):
    return Job.objects.filter( action__instance=instance )

  @cinp.list_filter( name='plan', paramater_type_list=[ { 'type': 'Model', 'model': 'architect.Plan.models.Plan' } ] )
  @staticmethod
  def filter_plan( plan ):
    return Job.objects.filter( action__instance__plan=plan )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def __str__( self ):
    return 'Job({0}) for {1}'.format( self.pk, self.action )
