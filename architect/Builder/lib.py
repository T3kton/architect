from datetime import datetime, timedelta, timezone

from architect.Builder.models import ComplexInstance, TypedInstance, Instance, Action


def cleanUp( age ):
  for instance in Instance.objects.filter( state='destroyed', updated__lt=datetime.now( timezone.utc ) - timedelta( seconds=age ) ):
    print( 'Cleaning up destroyed "{0}"...'.format( instance ) )
    instance.delete()


def applyChanges( plan, change_list ):
  for change in change_list:
    if change[0] == 'create':
      if change[1] == 'complex':
        instance = ComplexInstance.create( plan, *change[ 2: ] )
      elif change[1] == 'typed':
        instance = TypedInstance.create( plan, *change[ 2: ] )
      else:
        raise ValueError( 'Unknown instance type "{0}"'.format( change[1] ) )

      Action.create( instance, 'build' )
      print( 'new instance "{0}"'.format( instance ) )

    elif change[0] == 'destroy':
      _, instance = change
      if instance.state == 'destroyed':
        print( 'Instance "{0}" allready destroyed, ignorning' )

      else:
        try:
          action = instance.action
        except AttributeError:
          action = None

        if action is not None:
          if action.state == {}:
            print( 'delete unused instance "{0}"'.format( instance ) )
            instance.action.delete()
            instance.delete()

          else:
            print( 'action is still busy, ignoring request to destroy' )

        else:
          print( 'unrequesting "{0}"'.format( instance ) )
          Action.create( instance, 'destroy' )

    elif change[0] == 'move':
      if instance.__class__.__name__ != 'ComplexInstance':
        raise ValueError( 'Can Only Move ComplexInstance' )

      _, instance, complex_name = change
      print( 'moving "{0}" to "{1}"'.format( instance, complex_name ) )
      if instance.state == 'destroyed':
        print( '  Instance "{0}" allready destroyed, ignorning' )

      else:
        try:
          action = instance.action
        except AttributeError:
          action = None

        if action is not None:
          if action.state == {}:
            print( ' delete unused instance "{0}"'.format( instance ) )
            blueprint_name = instance.blueprint_name
            instance.action.delete()
            instance.delete()

            instance = Instance.create( plan, complex_name, blueprint_name )
            Action.create( instance, 'build' )
            print( '  new instance "{0}"'.format( instance ) )

          else:
            print( 'action is still busy, ignoring request to move' )

        else:
          Action.create( instance, 'move', complex_name )

    else:
      raise ValueError( 'Unknown change "{0}"'.format( change ) )
