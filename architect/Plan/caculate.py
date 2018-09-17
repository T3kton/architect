import random

from architect.Builder.models import Instance
from architect.tcalc.parser import parse


def caculateCounts( plan, complex_name_list, complex_cost_list, complex_availability_list, complex_reliability_list ):
  result = {}

  ts_map = {}

  for pts in plan.plantimeseries_set.all():
    ts_map[ pts.script_name ] = pts.timeseries.last_value

  print( ts_map )

  calc = parse( plan.script )
  calc.setBuckets( plan.slots_per_complex, complex_cost_list, complex_availability_list, complex_reliability_list )
  calc.setTimeSeriesValues( ts_map )
  slot_list_map = calc.evaluate()

  for blueprint_name in slot_list_map:
    slot_list = slot_list_map[ blueprint_name ]
    target_counts = [ 0 ] * len( complex_name_list )
    for slot in slot_list:
      target_counts[ int( slot / plan.slots_per_complex ) ] += 1

    target_map = dict( ( complex_name_list[ i ], target_counts[ i ] ) for i in range( 0, len( complex_name_list ) ) )

    result[ blueprint_name ] = target_map

  return result


def _instanceProvider( plan, blueprint_name, complex_name_list ):
  wrk_list = []
  while len( complex_name_list ) > 0:
    complex_name = complex_name_list.pop()
    wrk_list += Instance.objects.filter( plan=plan, blueprint__name=blueprint_name, complex__contractor_id=complex_name, state='built' )
    while len( wrk_list ) > 0:
      yield ( complex_name, wrk_list.pop() )


def caculateChangePlan( plan, complex_name_list, target, current ):
  result = []
  diff_map = {}
  for blueprint_name in target:
    target_map = target[ blueprint_name ]
    current_map = current[ blueprint_name ]

    diff_map = {}
    for complex_name in complex_name_list:
      diff_map[ complex_name ] = current_map.get( complex_name, 0 ) - target_map.get( complex_name, 0 )

    print( 'diff' )
    print( diff_map )

    if plan.can_move:
      positive_list = []
      negative_list = []

      for complex_name, diff in diff_map.items():
        if diff > 0:
          positive_list.append( complex_name )
        elif diff < 0:
          negative_list.append( complex_name )

      if len( positive_list ) != 0 and len( negative_list ) != 0:
        random.shuffle( positive_list )
        random.shuffle( negative_list )

        doners = _instanceProvider( plan, blueprint_name, negative_list )
        done = False

        while len( positive_list ) > 0 and not done:
          recipient_complex_name = positive_list.pop()
          while diff_map[ recipient_complex_name ] > 0 and not done:
            done = True
            for doner_complex_name, instance in doners:
              done = False
              result.append( ( 'move', instance, recipient_complex_name ) )
              diff_map[ doner_complex_name ] += 1
              diff_map[ recipient_complex_name ] -= 1

    for complex_name in complex_name_list:
      diff = diff_map[ complex_name ]
      if diff == 0:
        pass

      elif diff < 0 and plan.can_build:
        for _ in range( diff, 0 ):
          result.append( ( 'create', 'complex', complex_name, blueprint_name ) )

      elif diff > 0 and plan.can_destroy:
        # first find anything that hasn't been built, this techinically just reduces some thrashing
        unbuilt = Instance.objects.filter( plan=plan, blueprint__name=blueprint_name, complex__contractor_id=complex_name, action__state={}, state='new' ).order_by( '?' )[ :diff ]
        for instance in unbuilt:
          result.append( ( 'destroy', instance ) )
          diff -= 1

        # now to take out what is all ready built
        built = Instance.objects.filter( plan=plan, blueprint__name=blueprint_name, complex__contractor_id=complex_name, action__isnull=True, state='built' ).order_by( '?' )[ :diff ]
        for instance in built:
          result.append( ( 'destroy', instance ) )

  return result

# TODO: also move, probably need a move flag
# TODO: and a move only flag
