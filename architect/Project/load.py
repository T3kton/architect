import os
import string
import toml
import re


hostname_regex = re.compile( '^[a-z0-9][a-z0-9\-]*[a-z0-9]$' )
name_regex = re.compile( '^[a-zA-Z0-9][a-zA-Z0-9_\-]*$' )
item_list = ( 'address_block', 'structure', 'complex', 'plan' )


def _sub_load( filepath, paramater_map ):
  template = string.Template( open( filepath, 'r' ).read() )

  config = toml.loads( template.substitute( paramater_map ) )

  result = {}
  for item in item_list:
    try:
      result[ item ] = config[ item ]
    except KeyError:
      result[ item ] = {}

  return result


def _sub_find_load( filename, paramater_map, project_path ):
  filepath = os.path.join( project_path, filename ) + '.toml'
  if os.path.isfile( filepath ):
    return _sub_load( filepath, paramater_map )

  raise ValueError( 'Unable to find include "{0}"'.format( filename ) )


def _prep_paramaters( paramater_map ):
  for name in paramater_map:
    if isinstance( paramater_map[ name ], str ):
      paramater_map[ name ] = '\'{0}\''.format( paramater_map[ name ] )


def _fix_types( data ):
  if isinstance( data, dict ):
    for key, value in data.items():
      if type( value ).__name__ == 'DynamicInlineTableDict':
        data[ key ] = dict( value )

      _fix_types( value )

  elif isinstance( data, list ):
    for index in range( 0, len( data ) ):
      value = data[ index ]
      if type( value ).__name__ == 'DynamicInlineTableDict':
        data[ index ] = dict( value )

      _fix_types( value )

  elif isinstance( data, ( str, int ) ):
    return

  else:
    raise ValueError( 'Unknown type "{0}"'.format( type( data ).__name__ ) )


def loadProject( project_path ):
  config = toml.load( os.path.join( project_path, 'architect.toml' ) )
  result = {}

  for name in config[ 'site' ]:
    site = config[ 'site' ][ name ]
    result[ name ] = site
    for item in item_list:
      try:
        result[ name ][ item ] = config[ item ][ name ]
      except KeyError:
        result[ name ][ item ] = {}

    for filename, paramater_map in site.get( '__include__', {} ).items():
      paramater_map[ 'site' ] = name
      _prep_paramaters( paramater_map )
      for item in item_list:
        sub = _sub_find_load( filename, paramater_map, project_path )
        result[ name ][ item ].update( sub[ item ] )

    try:
      del site[ '__include__' ]
    except KeyError:
      pass

  _fix_types( result )

  return result

SITE_PATTERN = {
                 'description': str,
                 'parent': ( str, None ),
                 'config_values': ( dict, {} )
               }

ADDRESSBLOCK_PATTERN = {
                        'subnet': str,
                        'prefix': int,
                        'gateway_offset': int,
                        'reserved_offset_list': [ int ],
                        'dynamic_offset_list': [ int ]
                       }


STRUCTURE_PATTERN = {
                      'address_list': [ { 'address_block': str, 'offset': int } ],
                      'type': str,
                      'config_values': ( dict, None )
                   }

STRUCTURE_PATTERN_MAP = {
                          'Manual': { 'blueprint': str },
                          'AMT': { 'blueprint': str, 'amt_interface': { 'mac': str, 'offset': int } },
                          'Vcenter': { 'blueprint': str, 'complex': str },
                          'Docker': { 'blueprint': str, 'complex': str }
                         }

COMPLEX_PATTERN = {
                    'type': str,
                    'description': str,
                    'built_percentage': ( int, None ),
                    'member_list': [ str ]
                  }

PLAN_PATTERN = {
                 'description': str,
                 'script': str,
                 'timeseries_map': dict,
                 'enabled': ( bool, None ),
                 'change_cooldown': ( int, None ),
                 'config_values': ( dict, {} ),
                 'max_inflight': ( int, None ),
                 'hostname_pattern': ( str, None ),
                 'slots_per_complex': ( int, None ),
                 'can_move': ( bool, None ),
                 'can_destroy': ( bool, None ),
                 'can_build': ( bool, None )
               }


def _validate_item( location, item, pattern ):
  itype = type( item )

  if isinstance( pattern, type ):
    rtype = pattern
  else:
    rtype = type( pattern )

  if itype != rtype:
    raise ValueError( '"{0}", is the wrong type, expected "{1}", got "{2}"'.format( location, rtype.__name__, itype.__name__ ) )

  if isinstance( pattern, type ):  # the pattern dosen't have any children to iterate into
    return

  if rtype == dict:
    for name, sub_pattern in pattern.items():
      if isinstance( sub_pattern, tuple ):
        try:
          _validate_item( '{0}.{1}'.format( location, name ), item[ name ], sub_pattern[0] )
        except KeyError:
          if sub_pattern[1] is not None:
            item[ name ] = sub_pattern[1]

      else:
        try:
          _validate_item( '{0}.{1}'.format( location, name ), item[ name ], sub_pattern )
        except KeyError:
          raise ValueError( '"{0}" missing from "{1}"'.format( name, location ) )

  elif rtype == list:
    for row in item:
      _validate_item( location, row, pattern[0] )


def validateProject( config ):
  for site in config:
    if not name_regex.match( site ):
      raise ValueError( 'Invalid Site Name "{0}"'.format( site ) )

    _validate_item( 'site.{0}'.format( site ), config[ site ], SITE_PATTERN )

    for uid in config[ site ][ 'address_block' ]:
      _validate_item( 'address_block.{0}.{1}'.format( site, uid ), config[ site ][ 'address_block' ][ uid ], ADDRESSBLOCK_PATTERN )

    for hostname in config[ site ][ 'structure' ]:
      if not hostname_regex.match( hostname ):
        raise ValueError( 'Invalid hostname "{0}" in "{1}"'.format( hostname, site ) )

      _validate_item( 'structure.{0}.{1}'.format( site, hostname ), config[ site ][ 'structure' ][ hostname ], STRUCTURE_PATTERN )

      try:
        ftype = config[ site ][ 'structure' ][ hostname ][ 'type' ]
      except KeyError:
        raise ValueError( 'structure "{0}" in "{1}" missing type'.format( hostname, site ) )

      _validate_item( 'structure.{0}.{1}'.format( site, hostname ), config[ site ][ 'structure' ][ hostname ], STRUCTURE_PATTERN_MAP[ ftype ] )

    for name in config[ site ][ 'complex' ]:
      _validate_item( 'complex.{0}.{1}'.format( site, name ), config[ site ][ 'complex' ][ name ], COMPLEX_PATTERN )

    for name in config[ site ][ 'plan' ]:
      _validate_item( 'plan.{0}.{1}'.format( site, name ), config[ site ][ 'plan' ][ name ], PLAN_PATTERN )
