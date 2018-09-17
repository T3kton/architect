def updateInspection( inspection ):
  member = inspection.member
  new_value = None
  normalized_value = None
  target_count = inspection.target_count
  if member.scaler_type != 'none' and member.tsd_metric is not None:
    #tsd = getTSD()
    new_value = 130#tsd.getValue( member.tsd_metric, 10 )

    value_list = inspection.state.get( 'value_list', [] )
    value_list.insert( 0, new_value )
    while len( value_list ) < 5:
      value_list.insert( 0, new_value )

    inspection.state[ 'value_list' ] = value_list[ :5 ]

    print( 'value_list: {0}'.format( value_list ) )

    # skip None values in value_list some how
    normalized_value = ( member.a_value * value_list[0] ) + ( member.b_value * value_list[1] ) + ( ( 1 - ( member.a_value + member.b_value ) ) * value_list[2] )  # is this the right order?

    if member.scaler_type == 'liner':
      target_count = int( normalized_value * member.p_value )

    elif member.scaler_type == 'step':
      if normalized_value > member.step_threshold:
        target_count += 1
      elif normalized_value < -member.step_threshold:
        target_count -= 1

    else:
      raise Exception( 'Unknown scaler_type "{0}"'.format(  member.scaler_type ) )

    if target_count > inspection.target_count:
      if not member.can_grow:
        target_count = inspection.target_count
      elif target_count > member.max_instances:
        target_count = member.max_instances

    elif target_count < inspection.target_count:
      if not member.can_shrink:
        target_count = inspection.target_count
      elif target_count < member.min_instances:
        target_count = member.min_instances

  if member.min_instances is not None and target_count < member.min_instances:
    target_count = member.min_instances
  elif member.max_instances is not None and target_count > member.max_instances:
    target_count = member.max_instances

  if target_count != inspection.target_count:
    inspection.target_count = target_count
    inspection.clean()
    inspection.save()

  return ( new_value, normalized_value )
