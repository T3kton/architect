from datetime import datetime, timezone
from django.apps import apps

from architect.Contractor.Contractor import getContractor


def applyChange( change ):
  if change.type == 'site':
    Site = apps.get_model( 'Project', 'Site' )

    if change.action == 'local_create':
      site = Site( name=change.target_id )
      site.last_load = datetime.now( timezone.utc )
      site.last_load_hash = 'new'
      site.full_clean()
      site.save()

      result = 'Site "{0}" added locally'.format( change.target_id )

    elif change.action == 'remote_create':
      contractor = getContractor()
      contractor.createSite( change.target_id, **change.target_val )

      result = 'Site "{0}" added remotely'.format( change.target_id )

    elif change.action == 'change':
      contractor = getContractor()
      contractor.updateSite( change.target_id, **change.target_val )

      result = 'Site "{0}" updated fields: "{1}"'.format( change.target_id, '", "'.join( change.target_val.keys() ) )

    else:
      raise ValueError( 'Unknown Action "{0}" for site'.format( change.action ) )

  elif change.type == 'address_block':
    if change.action == 'remote_create':
      contractor = getContractor()
      contractor.createAddressBlock( change.site.name, change.target_id, **change.target_val )

      result = 'Address Block "{0}" added remotely'.format( change.target_id )

    elif change.action == 'change':
      contractor = getContractor()
      contractor.updateAddressBlock( change.target_id, **change.target_val )

      result = 'Address Block "{0}" updated fields: "{1}"'.format( change.target_id, '", "'.join( change.target_val.keys() ) )

    else:
      raise ValueError( 'Unknown Action "{0}" for address_block'.format( change.action ) )

  elif change.type == 'structure':
    if change.action == 'remote_create':
      contractor = getContractor()
      contractor.createStructure( change.site.name, change.target_id, **change.target_val )

      result = 'Structure "{0}" added remotely'.format( change.target_id )

    elif change.action == 'change':
      contractor = getContractor()
      contractor.updateStructure( change.target_id, **change.target_val )

      result = 'Structure "{0}" updated fields: "{1}"'.format( change.target_id, '", "'.join( change.target_val.keys() ) )

    else:
      raise ValueError( 'Unknown Action "{0}" for Structure'.format( change.action ) )

  elif change.type == 'complex':
    Complex = apps.get_model( 'Contractor', 'Complex' )
    if change.action == 'local_create':
      cplx = Complex( name=change.target_id )
      cplx.site = change.site
      cplx.full_clean()
      cplx.save()

      result = 'Complex "{0}" added locally'.format( change.target_id )

    elif change.action == 'remote_create':
      contractor = getContractor()
      contractor.createComplex( change.site.name, change.target_id, **change.target_val )

      result = 'Complex "{0}" added remotely'.format( change.target_id )

    elif change.action == 'change':
      contractor = getContractor()
      contractor.updateComplex( change.target_id, **change.target_val )

      result = 'Complex "{0}" updated fields: "{1}"'.format( change.target_id, '", "'.join( change.target_val.keys() ) )

    else:
      raise ValueError( 'Unknown Action "{0}" for Complex'.format( change.action ) )

  elif change.type == 'plan':
    Plan = apps.get_model( 'Plan', 'Plan' )

    if change.action == 'local_create':
      plan = Plan( name=change.target_id )
      plan.site = change.site

      for key, value in change.target_val.items():
        setattr( plan, key, value )

      plan.full_clean()
      plan.save()

      result = 'Plan "{0}" added locally'.format( change.target_id )

    elif change.action == 'change':
      plan = Plan.objects.get( site=change.site, name=change.target_id )

      for key, value in change.target_val.items():
        setattr( plan, key, value )

      plan.full_clean()
      plan.save()

      result = 'Plan "{0}" updated fields: "{1}"'.format( change.target_id, '", "'.join( change.target_val.keys() ) )

    else:
      raise ValueError( 'Unknown Action "{0}" for Plan'.format( change.action ) )

  else:
    raise ValueError( 'Unknown Action "{0}"'.format( change.type ) )

  return result
