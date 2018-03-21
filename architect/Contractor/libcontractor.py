from cinp.client import CInP

from django.conf import settings


def getContractor():
  return Contractor( settings.CONTRACTOR_HOST, settings.CONTRACTOR_ROOT_PATH, settings.CONTRACTOR_PORT, settings.CONTRACTOR_PROXY )


class Contractor():
  def __init__( self, host, root_path, port, proxy=None ):
    super().__init__()
    self.cinp = CInP( host, root_path, port )

  # Site functions
  def getSiteList( self ):
    return self.cinp.getFilteredURIs( '/api/v1/Site/Site' )

  def createSite( self, name, **value_map ):
    data = { 'name': name }
    for name in ( 'description', 'config_values' ):
      try:
        data[ name ] = value_map[ name ]
      except KeyError:
        pass

    self.cinp.create( '/api/v1/Site/Site', data )

  def getSite( self, id ):
    return self.cinp.get( '/api/v1/Site/Site:{0}:'.format( id ) )

  def updateSite( self, id, **value_map ):
    data = {}
    for name in ( 'description', 'config_values' ):
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
      self.cinp.update( '/api/v1/Utilities/AddressBlock:{0}:'.format( id ), data )

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

      for offset in dynamic_offset_list - current:
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

  # Instance Functions
  # for now we are going to assume these instances are created atominically with both foundation and structure, so pull the structures, that is what we are really after anyway
  def getInstanceMap( self, site_id ):
    result = {}
    foundation_map = {}
    for uri, foundation in self.cinp.getFilteredObjects( '/api/v1/Building/Foundation', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      foundation_map[ uri ] = foundation

    for uri, structure in self.cinp.getFilteredObjects( '/api/v1/Building/Structure', 'site', { 'site': '/api/v1/Site/Site:{0}:'.format( site_id ) } ):
      address_list = list( self.cinp.getFilteredObjects( '/api/v1/Utilities/Address', 'structure', { 'structure': uri } ) )
      print( address_list )
      foundation = foundation_map[ structure[ 'foundation' ] ]
      tmp = {}
      tmp[ 'type' ] = foundation[ 'type' ]
      tmp[ 'blueprint' ] = structure[ 'blueprint' ].split( ':' )[1]
      tmp[ 'address_list' ] = [ { 'address_block': i[1][ 'address_block' ].split( ':' )[1], 'offset': i[1][ 'offset' ] } for i in address_list ]
      result[ structure[ 'hostname' ] ] = tmp

    return result

  def createInstance( self, site_id, name, **value_map ):
    # def createFoundationStructure( self, foundation_type, site_id, blueprint, hostname, config_values, address_block_id, address_offest ):
    address = value_map[ 'address_list' ][0]
    data = {}
    data[ 'site' ] = '/api/v1/Site/Site:{0}:'.format( site_id )
    data[ 'locator' ] = name
    if value_map[ 'type' ] == 'Manual':
      data[ 'blueprint' ] = '/api/v1/BluePrint/FoundationBluePrint:generic-manual:'
      foundation = self.cinp.create( '/api/v1/Manual/ManualFoundation'.format( complex ), data )[0]

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

    data = {}
    data[ 'networked' ] = '/api/v1/Utilities/Networked:{0}:'.format( structure_id )
    data[ 'address_block' ] = '/api/v1/Utilities/AddressBlock:{0}:'.format( address[ 'address_block' ] )
    data[ 'offset' ] = address[ 'offset' ]
    data[ 'interface_name' ] = 'eth0'
    data[ 'vlan' ] = 0
    data[ 'is_primary' ] = True
    address = self.cinp.create( '/api/v1/Utilities/Address', data )[0]

    print( '************************  created "{0}" and "{1}({2})"'.format( foundation, structure, address ) )

  def updateInstance( self, id, **value_map ):
    raise ValueError( 'Instance is not update-able' )

  # Complex functions
  def getComplexes( self ):
    for ( id, complex ) in self.cinp.getFilteredObjects( '/api/v1/Building/Complex' ):
      if complex[ 'state' ] != 'built':
        continue

      yield self.cinp.uri.extractIds( id )[0]

  def getBluePrints( self ):
    return self.cinp.getFilteredURIs( '/api/v1/BluePrint/StructureBluePrint' )

  def getComplex( self, id ):
    complex = self.cinp.get( '/api/v1/Building/Complex:{0}:'.format( id ) )
    complex[ 'site' ] = self.cinp.uri.extractIds( complex[ 'site' ] )[0]
    return complex

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
