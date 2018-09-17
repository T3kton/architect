from cinp import client

from django.conf import settings


CONTRACTOR_API_VERSION = '0.9'


def getContractor():
  return Contractor( settings.CONTRACTOR_HOST, settings.CONTRACTOR_PROXY )


class Contractor():
  def __init__( self, host, proxy=None ):
    super().__init__()
    self.cinp = client.CInP( host, '/api/v1/', proxy )
    root = self.cinp.describe( '/api/v1/' )
    if root[ 'api-version' ] != CONTRACTOR_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( CONTRACTOR_API_VERSION, root[ 'api-version' ] ) )

  # Site functions
  def getSiteList( self ):
    return self.cinp.getFilteredURIs( '/api/v1/Site/Site' )

  def createSite( self, name, **value_map ):
    data = { 'name': name }
    try:
      value_map[ 'parent' ] = '/api/v1/Site/Site:{0}:'.format( value_map[ 'parent' ] )
    except KeyError:
      pass

    for name in ( 'description', 'config_values', 'parent' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    self.cinp.create( '/api/v1/Site/Site', data )

  def getSite( self, id ):
    result = self.cinp.get( '/api/v1/Site/Site:{0}:'.format( id ) )
    if result[ 'parent' ] is not None:
      result[ 'parent' ] = result[ 'parent' ].split( ':' )[1]

    return result

  def updateSite( self, id, **value_map ):
    try:
      value_map[ 'parent' ] = '/api/v1/Site/Site:{0}:'.format( value_map[ 'parent' ] )
    except KeyError:
      pass

    data = {}
    for name in ( 'description', 'config_values', 'parent' ):  # do we really want to allow switching parent?
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    if data:
      self.cinp.update( '/api/v1/Site/Site:{0}:'.format( id ), data )

  def deleteSite( self, id ):
    self.cinp.delete( '/api/v1/Site/Site:{0}:'.format( id ) )

  # AddressBlock functions
  def getAddressBlockMap( self, site_id ):
    result = {}
    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Utilities/AddressBlock', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      item[ 'reserved_offset_list' ] = list( self.getAddressBlockReserved( uri ).keys() )
      item[ 'dynamic_offset_list' ] = list( self.getAddressBlockDynamic( uri ).keys() )
      result[ item[ 'name' ] ] = item

    return result

  def createAddressBlock( self, site_id, name, **value_map ):
    data = { 'name': name, 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) }
    for name in ( 'subnet', 'prefix', 'gateway_offset' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    # data[ 'reserved_offset_list' ] = value_map[ 'reserved_offset_list' ]  # for now we will let the up comming update set the reserved_offset_list
    # data[ 'dynamic_offset_list' ] = value_map[ 'dynamic_offset_list' ]  # for now we will let the up comming update set the dynamic_offset_list

    self.cinp.create( '/api/v1/Utilities/AddressBlock', data )

  def updateAddressBlock( self, id, **value_map ):
    uri = '/api/v1/Utilities/AddressBlock:{0}:'.format( id )
    data = {}
    for name in ( 'subnet', 'prefix', 'gateway_offset' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    if data:
      self.cinp.update( uri, data )

    reserved_offset_list = value_map.get( 'reserved_offset_list', None )
    dynamic_offset_list = value_map.get( 'dynamic_offset_list', None )

    if reserved_offset_list is not None:
      reserved_offset_list = set( reserved_offset_list )
      current_map = self.getAddressBlockReserved( uri )
      current = set( current_map.keys() )

      for offset in reserved_offset_list - current:
        data = { 'address_block': uri, 'offset': offset, 'reason': 'Architect Reserved' }
        self.cinp.create( '/api/v1/Utilities/ReservedAddress', data )

      for offset in current - reserved_offset_list:
         self.cinp.delete( current_map[ offset ] )

    if dynamic_offset_list is not None:
      dynamic_offset_list = set( dynamic_offset_list )
      current_map = self.getAddressBlockDynamic( uri )
      current = set( current_map.keys() )

      for offset in dynamic_offset_list - current:
        data = { 'address_block': uri, 'offset': offset }
        self.cinp.create( '/api/v1/Utilities/DynamicAddress', data )

      for offset in current - dynamic_offset_list:
        self.cinp.delete( current_map[ offset ] )

  def deleteAddressBlock( self, id ):
    return self.cinp.delete( '/api/v1/Utilities/AddressBlock:{0}:'.format( id ) )

  def getAddressBlockReserved( self, uri ):
    result = {}
    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Utilities/ReservedAddress', 'address_block', { 'address_block': uri } ):
      result[ int( item[ 'offset' ] ) ] = uri

    return result

  def getAddressBlockDynamic( self, uri ):
    result = {}
    for _, item in self.cinp.getFilteredObjects( '/api/v1/Utilities/DynamicAddress', 'address_block', { 'address_block': uri } ):
      result[ int( item[ 'offset' ] ) ] = uri

    return result

  # Structure Functions - for these the Foundation is a part of the Structure as far as Contractor is concerened
  # for now we are going to assume these instances are created atomically with both foundation and structure, so pull the structures, that is what we are really after anyway
  def getStructureMap( self, site_id ):
    result = {}
    foundation_map = {}
    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Building/Foundation', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      foundation_map[ uri ] = item

    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Building/Structure', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      address_list = list( self.cinp.getFilteredObjects( '/api/v1/Utilities/Address', 'structure', { 'structure': uri } ) )
      foundation = foundation_map[ item[ 'foundation' ] ]
      tmp = {}
      tmp[ 'type' ] = foundation[ 'type' ]
      tmp[ 'blueprint' ] = item[ 'blueprint' ].split( ':' )[1]
      tmp[ 'address_list' ] = [ { 'address_block': i[1][ 'address_block' ].split( ':' )[1], 'offset': i[1][ 'offset' ] } for i in address_list ]
      tmp[ 'config_values' ] = item[ 'config_values' ]
      result[ item[ 'hostname' ] ] = tmp

    return result

  def createStructure( self, site_id, name, **value_map ):
    address_list = value_map[ 'address_list' ]
    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'locator' ] = name
    if value_map[ 'type' ] == 'Manual':
      data[ 'blueprint' ] = '/api/v1/BluePrint/FoundationBluePrint:manual-foundation-base:'
      foundation = self.cinp.create( '/api/v1/Manual/ManualFoundation', data )[0]

    else:
      raise ValueError( 'Unknown foundation type "{0}"'.format( value_map[ 'type' ] ) )

    foundation_id = self.cinp.uri.extractIds( foundation )[0]

    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'foundation' ] = '/api/v1/Building/Foundation:{0}:'.format( foundation_id )
    data[ 'hostname' ] = name
    data[ 'blueprint' ] = '/api/v1/BluePrint/StructureBluePrint:{0}:'.format( value_map[ 'blueprint' ] )
    # data[ 'config_values' ] = value_map[ 'config_values' ]
    data[ 'auto_build' ] = True  # Static stuff builds when it can
    structure = self.cinp.create( '/api/v1/Building/Structure', data )[0]
    structure_id = self.cinp.uri.extractIds( structure )[0]

    address_id_list = []
    is_primary = True
    for address in address_list:
      data = {}
      data[ 'networked' ] = '/api/v1/Utilities/Networked:{0}:'.format( structure_id )
      data[ 'address_block' ] = '/api/v1/Utilities/AddressBlock:{0}:'.format( address[ 'address_block' ] )
      data[ 'offset' ] = address[ 'offset' ]
      data[ 'interface_name' ] = 'eth0'
      data[ 'vlan' ] = 0
      data[ 'is_primary' ] = is_primary
      address_id_list.append( self.cinp.create( '/api/v1/Utilities/Address', data )[0] )
      is_primary = False

    print( '************************  created "{0}" and "{1}({2})"'.format( foundation, structure, address_id_list ) )

  def updateStructure( self, id, **value_map ):
    if list( value_map.keys() ) != [ 'config_values' ]:
      raise ValueError( 'Only config_values of Instance are update-able' )

    structure_data = {}
    for name in ( 'config_values', ):
      try:
        structure_data[ name ] = value_map[ name ]
      except KeyError:
        pass

    if structure_data:
      foundation = self.cinp.get( '/api/v1/Building/Foundation:{0}:'.format( id ) )

      self.cinp.update( foundation[ 'attached_structure' ], structure_data )

  def deleteStructure( self, id ):
    # TODO: submit deconfigure job, if one allready exists, raise ValueError
    raise Exception( 'Not implemented yet' )

  # Complex functions
  #
  # def getComplex( self, id ):
  #   complex = self.cinp.get( '/api/v1/Building/Complex:{0}:'.format( id ) )
  #   complex[ 'site' ] = self.cinp.uri.extractIds( complex[ 'site' ] )[0]
  #   return complex

  def getComplexMap( self, site_id ):
    result = {}
    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Building/Complex', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      item[ 'member_list' ] = self.cinp.uri.extractIds( list( i[1][ 'foundation' ] for i in self.cinp.getFilteredObjects( '/api/v1/Building/Structure', 'complex', { 'complex': uri } ) ) )
      result[ item[ 'name' ] ] = item

    return result

  def createComplex( self, site_id, name, **value_map ):
    data = { 'name': name, 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) }
    for name in ( 'description', 'built_percentage' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    # data[ 'member_list' ] = value_map[ 'member_list' ]  # for now we will let the up comming update set the member_list

    if value_map[ 'type' ] == 'Manual':
      self.cinp.create( '/api/v1/Manual/ManualComplex', data )

    else:
      raise ValueError( 'Unknown foundation type "{0}"'.format( value_map[ 'type' ] ) )

  def updateComplex( self, id, **value_map ):
    uri = '/api/v1/Building/Complex:{0}:'.format( id )
    data = {}
    for name in ( 'description', 'built_percentage' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    if data:
      self.cinp.update( uri, data )

    member_list = value_map.get( 'member_list', None )

    if member_list is not None:
      member_list = set( member_list )
      current_map = self.getComplexMembers( uri )
      current = set( current_map.keys() )

      for member in member_list - current:
        # This is a bit of a hack to find the structure by looking up the foundation by the name, which *SHOULD* match the locator, there should be a better way
        foundation = self.cinp.get( '/api/v1/Building/Foundation:{0}:'.format( member ) )
        structure = foundation[ 'attached_structure' ]
        data = { 'complex': uri, 'structure': structure }
        self.cinp.create( '/api/v1/Building/ComplexStructure', data )

      for member in current - member_list:
         self.cinp.delete( current_map[ member ] )

  def getComplexMembers( self, uri ):
    result = {}
    for uri, item in self.cinp.getFilteredObjects( '/api/v1/Building/ComplexStructure', 'complex', { 'complex': uri } ):
      result[ item[ 'member' ].split( ':', 2 ) ] = uri

    return result

  # functions used by contractor sync
  def getBluePrints( self ):
    return self.cinp.getFilteredURIs( '/api/v1/BluePrint/StructureBluePrint' )

  # functions for the dynamic building from Plans
  def createComplexFoundation( self, complex, blueprint, hostname ):
    foundation = self.cinp.call( '/api/v1/Building/Complex:{0}:(createFoundation)'.format( complex ), { 'hostname': hostname } )
    print( '************************ created "{0}"'.format( foundation ) )

    foundation_id = self.cinp.uri.extractIds( foundation )[0]
    return foundation_id

  def buildFoundation( self, id ):
    # we have to set locate manually b/c the structure is not auto-configure, at
    # this point contractor dosen't autolocate foundations for non auto-configure structures.
    # we are setting Located here so that a job dosen't get auto created before we
    # can trigger the creation event, techinically there is still a  small hole that
    #  a job can be built.  TODO: tweek foundatino so that it isn't auto built,
    # would be nice if that also made it so we didn't have to setLocated
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(setLocated)'.format( id ), {} )
    job_id = self.cinp.call( '/api/v1/Building/Foundation:{0}:(doCreate)'.format( id ), {} )
    print( '------------------------- create Job foundation "{0}"'.format( job_id ) )

  def destroyFoundation( self, id ):
    self.cinp.call( '/api/v1/Building/Foundation:{0}:(doDestroy)'.format( id ), {} )

  def createComplexStructure( self, site_id, foundation_id, blueprint, hostname, config_values ):
    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'foundation' ] = '/api/v1/Building/Foundation:{0}:'.format( foundation_id )
    data[ 'hostname' ] = hostname
    data[ 'blueprint' ] = '/api/v1/BluePrint/StructureBluePrint:{0}:'.format( blueprint )
    data[ 'config_values' ] = config_values
    data[ 'auto_build' ] = False  # architect explicitally starts them
    structure = self.cinp.create( '/api/v1/Building/Structure', data )[0]

    data = {}
    data[ 'structure' ] = structure
    data[ 'interface_name' ] = 'eth0'
    data[ 'is_primary' ] = True
    address = self.cinp.call( '/api/v1/Utilities/AddressBlock:1:(nextAddress)', data )
    print( '************************  created "{0}({1})"'.format( structure, address ) )

    structure_id = self.cinp.uri.extractIds( structure )[0]
    return structure_id

  def buildStructure( self, id ):
    job_id = self.cinp.call( '/api/v1/Building/Structure:{0}:(doCreate)'.format( id ), {} )
    print( '------------------------- create Job structure "{0}"'.format( job_id ) )

  def destroyStructure( self, id ):
    self.cinp.call( '/api/v1/Building/Structure:{0}:(doDestroy)'.format( id ), {} )

  def registerWebHook( self, target, job_id, target_id, token ):
    data = {}
    data[ target ] = '/api/v1/Building/{0}:{1}:'.format( target.title(), target_id )
    data[ 'one_shot' ] = True
    data[ 'extra_data' ] = { 'token': token, 'target': target }
    data[ 'type' ] = 'call'
    data[ 'url' ] = 'http://127.0.0.1:8880/api/v1/Builder/Job:{0}:(jobNotify)'.format( job_id )
    if target == 'foundation':
      self.cinp.create( '/api/v1/PostOffice/FoundationBox', data )
    else:
      self.cinp.create( '/api/v1/PostOffice/StructureBox', data )
