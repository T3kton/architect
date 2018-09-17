import string

# for now we are going to barrow parsimonious from contractor
from architect.tcalc.parsimonious import Grammar, ParseError, IncompleteParseError


# TODO: make sure a distrubution function is used

tcalc_grammar = """
script              = line*
line                = definition? nl
definition          = ws ( blueprint / variable ) ws ":" expression
expression          = ws ( function / infix / boolean / not_ / external / ts_value / blueprint / variable / number_float / number_int ) ws

not_                = ~"[Nn]ot" expression

number_float        = ~"[-+]?[0-9]+\.[0-9]+"
number_int          = ~"[-+]?[0-9]+"
boolean             = ~"[Tt]rue" / ~"[Ff]alse"

function            = label "(" ( expression "," )* expression ")"
external            = ( "*INDEX*" / "*TOTAL*" / "*COST*" / "*AVAILABILITY*" / "*RELIABILITY*" )
variable            = label !"("

infix               = "(" expression ( "^" / "*" / "/" / "%" / "+" / "-" / "&" / "|" / "and"/ "or" / "==" / "!=" / "<=" / ">=" / ">" / "<" ) expression ")"

label               = ~"[a-zA-Z][a-zA-Z0-9_\-]*"
ts_value            = ~"@[a-zA-Z][a-zA-Z0-9_\-]*"
blueprint           = ~"#[a-zA-Z0-9][a-zA-Z0-9_\-]*"
ws                  = ~"[ \t]*"
nl                  = ~"[\\r\\n]*"
"""

external_lookup = {
                    'init': { '*TOTAL*': ( '_T_', False ), '*COST*': ( '_C_', True ), '*AVAILABILITY*': ( '_A_', True ), '*RELIABILITY*': ( '_R_', True ) },  # there is not *INDEX* for the init function
                    'main': { '*INDEX*': ( '_I_', False ), '*TOTAL*': ( '_T_', False ), '*COST*': ( '_C_', False ), '*AVAILABILITY*': ( '_A_', False ), '*RELIABILITY*': ( '_R_', False ) },
                  }


class ParserError( Exception ):
  def __init__( self, column, msg ):
    self.column = column
    self.msg = msg

  def __str__( self ):
    return 'ParseError, column: {0}, "{1}"'.format( self.column, self.msg )


def lint( script ):
  parser = Parser()
  return parser.lint( script )


def parse( script ):
  parser = Parser()
  return parser.parse( script )


# TODO: subsetting needs to be 100%, otherwise the user dosen't know the maxvalue with out to much work.

# NOTE: Function paramaters must be numbered, so that the number of required
# functions is correctly detected
function_map = {
                  # distrubution
                  'periodic': '( {0} ) if not bool( {0} % {1} ) else False',
                  # 'linear': 'bool( {0} == math.ceil( math.floor( ( {0} * ( {1} / _T_ ) ) + 0.00000000001 ) * ( _T_ / {1} ) ) )',
                  'linear': '( {0} ) if ( {0} ) in linear_slots_{ID} else False',
                  'weighted': '( {0} ) if ( {0} ) in weighted_slots_{ID} else False',

                  # subsetting
                  'above': '( {0} ) if ( {0} ) > ( {1} ) and {0} is not False and {1} is not False else False',
                  'below': '( {0} ) if ( {0} ) < ( {1} ) and {0} is not False and {1} is not False else False',
                  'above_inclusive': '( {0} ) if ( {0} ) >= ( {1} ) and {0} is not False and {1} is not False else False',
                  'below_inclusive': '( {0} ) if ( {0} ) <= ( {1} ) and {0} is not False and {1} is not False else False',
                  'filter': '( {0} ) if ( {1} ) else False',
                }

function_init_map = {
                      'linear': """
  import math
  global linear_slots_{ID}
  if {1} > _T_ or {1} < 1:
    raise ValueError( 'Count should be more than 0 and less than the number of slots' )

  linear_slots_{ID} = [ math.ceil( i * safe_div( _T_, {1} ) ) for i in range( 0, int( {1} ) ) ]
""",

                      'weighted': """
  import math
  global weighted_slots_{ID}

  avg_weight = float( sum( {2} ) ) / len( {2} )
  counter = 0
  weighted_slots_{ID} = []
  for i in range( 0, int( {1} ) ):
    bucket = int( counter / SLOTS_PER_BUCKET )
    try:
      interval = ( _T_ * ( avg_weight / {2}[ bucket ] ) ) / {1}
      interval = min( interval, SLOTS_PER_BUCKET )
    except ( ZeroDivisionError, TypeError ):
      interval = SLOTS_PER_BUCKET

    if interval < 1:
      raise ValueError( 'interval drops below 1' )

    counter += interval
    if counter > _T_:
      raise ValueError( 'Counter exceted total' )

    weighted_slots_{ID}.append( math.ceil( counter ) )
"""
}

"""
Functions:
  number per complex : number of  instances per complex = X % ( buckets per complex / count )
  weighted distrubution : = weighted value of curent complex / take the avertage of all the weights values -> factor that into even distrubution

  complex subset: prune down to bucekts that are in or out of list of complexes

for a/b testing: need above, below, every X


periodic: should produce the same result as [ INDEX for INDEX in range( 0, total_slots ) if not bool( INDEX % _PARAM_ ) ]  where *INDEX* is the first paramater
def periodic( i ):
  return not bool( i % PARAM )

( for non pre-computed version )
linear: should produce the same result as [ math.ceil( INDEX * ( total_slots / _PARAM_ ) ) for INDEX in range( 0, _PARAM_ ) ]  where *INDEX* is the first paramater
def linear( i ):
  return i == math.ceil( math.floor( ( i * ( COUNT / slot_count ) ) + 0.00000000001 ) * ( slot_count / COUNT ) )

NOTE: the magic number is to compensate for some small round down during the division
NOTE2: it is important that ( COUNT / slot_count ) be >= 1
"""

# TODO: how to do a dirivitave or integrated value....
# some kind of remember last value for a function
# mabey all the functions should exist in the same
# blob, and have a save for next time value per index
# if the functions get to involved we are going to need macros
# mabey for the first round we skip the PD controller and just scale
# with historsis


class Script():
  def __init__( self, code ):
    super().__init__()
    self.code = code
    self.slots_per_bucket = None
    self.ts_value_map = None

  def setBuckets( self, slots_per_bucket, bucket_cost, bucket_availability, bucket_reliability ):
    if not isinstance( slots_per_bucket, int ) or slots_per_bucket < 1 or slots_per_bucket > 10000:
      raise ValueError( 'slots_per_bucket must be int and from 1 to 10000' )
    if not isinstance( bucket_cost, list ) or not isinstance( bucket_availability, list ) or not isinstance( bucket_reliability, list ):
      raise ValueError( 'bucket_cost, bucket_availability, and bucket_reliability must be list' )
    if len( bucket_cost ) != len( bucket_availability ) != len( bucket_reliability ) or len( bucket_cost ) < 1 or len( bucket_cost ) > 1000:
      raise ValueError( 'bucket_cost, bucket_availability, and bucket_reliability must be the same size, and length from 1 to 1000' )

    self.slots_per_bucket = slots_per_bucket
    self.bucket_cost = bucket_cost
    self.bucket_availability = bucket_availability
    self.bucket_reliability = bucket_reliability
    self.total_slots = len( self.bucket_cost ) * self.slots_per_bucket

  def setTimeSeriesValues( self, ts_value_map ):
    if not isinstance( ts_value_map, dict ):
      raise ValueError( 'external_value_map must be a dict' )
    self.ts_value_map = ts_value_map

  def _evaluate( self, bucket, index ):
    try:
      value_map = self.code[ 'main' ]( index, self.total_slots, self.bucket_cost[ bucket ], self.bucket_availability[ bucket ], self.bucket_reliability[ bucket ], self.ts_value_map )
    except KeyError as e:
      raise ValueError( 'value "{0}" not defined'.format( e.args[0] ) )

    return dict( zip( value_map.keys(), [ i >= 0 and i is not False and i is not None for i in value_map.values() ] ) )  # yes this is a bit odd, however '0' is a valid bucket/offset

  def evaluate( self ):
    if self.slots_per_bucket is None:
      raise ValueError( 'bucket info has not been set' )
    if self.ts_value_map is None:
      raise ValueError( 'timeseries values have not been set' )

    self.code[ '__builtins__' ][ 'SLOTS_PER_BUCKET' ] = self.slots_per_bucket

    self.code[ 'init' ]( self.total_slots, self.bucket_cost, self.bucket_availability, self.bucket_reliability, self.ts_value_map )

    result_name_list = self._evaluate( 0, 0 ).keys()
    result = dict( zip( result_name_list, [ [] for i in result_name_list ] ) )

    index = 0
    for bucket in range( 0, len( self.bucket_cost ) ):
      for offset in range( 0, self.slots_per_bucket ):
        tmp = self._evaluate( bucket, index )
        for key, value in tmp.items():
          if value:
            result[ key ].append( index )

        index += 1

    return result


class Parser():
  def __init__( self ):
    super().__init__()
    self.grammar = Grammar( tcalc_grammar )
    self.function_initer_list = []
    self.mode = 'main'

  def lint( self, script ):
    self.function_initer_list = []
    self.mode = 'main'
    try:
      ast = self.grammar.parse( script )
    except IncompleteParseError as e:
      return 'Incomplete Parsing at column: {0}'.format( e.column() )
    except ParseError as e:
      return 'Error Parsing at column: {0}'.format( e.column() )

    try:
      self._eval( ast )
    except Exception as e:
      return 'Exception Parsing "{0}"'.format( e )

    return None

  def parse( self, script ):
    self.function_initer_list = []
    self.mode = 'main'
    try:
      ast = self.grammar.parse( script )
    except IncompleteParseError as e:
      raise ParserError( e.column(), 'Incomplete Parse' )
    except ParseError as e:
      raise ParserError( e.column(), 'Error Parsing' )

    init = ''

    body = self._eval( ast )

    init = """import sys
def safe_div( numerator, denominator ):
  if denominator == 0:
    return sys.maxsize

  return numerator / denominator

def init( _T_, _C_, _A_, _R_, ts_map ):
"""
    if self.function_initer_list:
      for name, init_id, paramaters in self.function_initer_list:
        init += function_init_map[ name ].format( *paramaters, ID=init_id )
    else:
      init += '  pass'

    script = init + """

def main( _I_, _T_, _C_, _A_, _R_, ts_map ):
  b_map = {}
  v_map = {}

""" + body + """

  return b_map
"""

    print( '*****************\n{0}\n*******************'.format( script ) )

    tmp = {}
    exec( compile( script, '<string>', 'exec' ), tmp )

    return Script( tmp )

  def _eval( self, node ):
    if node.expr_name in ( 'ws', 'nl' ):  # ignore wite space
      return ''

    if node.expr_name == '':
      return self._eval( node.children[0] )

    try:
      handler = getattr( self, node.expr_name )
    except AttributeError:
      raise Exception( 'Unable to find handler for "{0}"'.format( node.expr_name ) )

    return handler( node )

  def script( self, node ):
    if not node.children:
      return ''

    definition_list = [ self._eval( child ) for child in node.children ]
    return '\n'.join( definition_list )

  def line( self, node ):
    if len( node.children[0].children ) == 0:
      return ''

    return self._eval( node.children[0] )

  def definition( self, node ):
    target = self._eval( node.children[1] )
    value = self._eval( node.children[4] )

    return '  {0} = {1}'.format( target, value )

  def expression( self, node ):
    return self._eval( node.children[1] )

  def number_float( self, node ):
    return '{0}'.format( float( node.text ) )

  def number_int( self, node ):
    return '{0}'.format( float( node.text ) )

  def boolean( self, node ):
    return '{0}'.format( True if node.text.lower() == 'true' else False )

  def external( self, node ):
    name = node.text

    try:
      lookup = external_lookup[ self.mode ][ name ]
    except KeyError:
      raise ValueError( 'External "{0}" not allowed here'.format( name ) )

    if lookup[1]:
      return '[ {0} ]'.format( lookup[0] )
    else:
      return lookup[0]

  def ts_value( self, node ):
    name = node.text

    return 'ts_map[ \'{0}\' ]'.format( name[ 1: ] )

  def variable( self, node ):
    name = node.text

    if self.mode == 'init':
      raise ValueError( 'Unable to refrence values in init' )

    return 'v_map[ \'{0}\' ]'.format( name )

  def blueprint( self, node ):
    name = node.text

    if self.mode == 'init':
      raise ValueError( 'Unable to refrence values in init' )

    return 'b_map[ \'{0}\' ]'.format( name[ 1: ] )

  def infix( self, node ):
    left = self._eval( node.children[1] )
    right = self._eval( node.children[3] )
    left_list = False
    right_list = False
    if left[0] == '[':
      left_list = True
      left = left[ 1:-1 ]

    if right[0] == '[':
      right_list = True
      right = right[ 1:-1 ]

    operator = node.children[2].text

    if operator == '/':
      if left_list and right_list:
        if len( left_list ) != len( right_list ):
          raise ValueError( 'left and right lists are not the same length' )

        return '[ safe_div( {0[i]}, {2}[i] ) for i in range( 0, len( {0} ) ) ]'.format( left, '', right )
      elif left_list:
        return '[ safe_div( i, {2} ) for i in {0} ]'.format( left, '', right )
      elif right_list:
        return '[ safe_div( {0}, i ) for i in {2} ]'.format( left, '', right )

      return 'safe_div( {0}, {1} )'.format( left, right )

    else:
      value = '( {0} {1} {2} )'
      if left_list and right_list:
        if len( left_list ) != len( right_list ):
          raise ValueError( 'left and right lists are not the same length' )

        value = '[ {0}[ i ] {1} {2}[ i ] for i in range( 0, len( {0} ) ) ]'
      elif left_list:
        value = '[ i {1} {2} for i in {0} ]'
      elif right_list:
        value = '[ {0} {1} i for i in {2} ]'

    return value.format( left, operator, right )

  def not_( self, node ):
    return 'not bool( {0} )'.format( self._eval( node.children[1] ) )

  def function( self, node ):
    name = node.children[0].text

    param_value_list = []
    children = list( node.children[2] )
    children.append( node.children[3] )
    for child in children:
      param_value_list.append( self._eval( child ) )

    try:
      func_body = function_map[ name ]
    except KeyError:
      raise ValueError( 'Unknown function "{0}"'.format( name ) )

    init_id = None
    if name in function_init_map:
      self.mode = 'init'

      used_parm_list = _getFormatIds( function_init_map[ name ] )

      init_param_value_list = []
      for i in range( 0, len( children ) ):
        if i not in used_parm_list:
          init_param_value_list.append( None )

        else:
          child = children[i]
          value = self._eval( child )
          if value.startswith( '[ _' ):
            value = value[ 1:-1 ]
          init_param_value_list.append( value )

      init_id = 'id{0}'.format( len( self.function_initer_list ) )
      self.function_initer_list.append( ( name, init_id, init_param_value_list ) )
      self.mode = 'main'

    max_paramater = max( [0] + _getFormatIds( func_body ) )
    if init_id is not None:
      max_paramater = max( [ max_paramater ] + _getFormatIds( function_init_map[ name ] ) )

    max_paramater += 1

    if len( param_value_list ) != max_paramater:
      raise ValueError( 'Expected {0} paramaters, got {1}'.format( max_paramater, len( param_value_list ) ) )

    if init_id is not None:
      return function_map[ name ].format( *param_value_list, ID=init_id )
    else:
      return function_map[ name ].format( *param_value_list )


def _getFormatIds( scriptlet ):
  return [ int( v[1] ) for v in string.Formatter().parse( scriptlet ) if v[1] is not None and v[1] not in ( 'ID', ) ]
