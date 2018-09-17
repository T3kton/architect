#!/usr/bin/env python3
import os

os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'architect.settings' )

import django
django.setup()

import sys
import logging

from gunicorn.app.base import BaseApplication
from cinp.server_werkzeug import WerkzeugServer

from architect.User.models import getUser

DEBUG = True


class GunicornApp( BaseApplication ):
  def __init__( self, application, options=None ):
    self.options = options or {}
    self.application = application
    super().__init__()

  def load_config( self ):
    for ( key, value ) in self.options.items():
      self.cfg.set( key.lower(), value )

  def load( self ):
    return self.application

if __name__ == '__main__':
  logging.basicConfig()
  logger = logging.getLogger()
  if DEBUG:
    logger.setLevel( logging.DEBUG )
  else:
    logger.setLevel( logging.INFO )
  logger.info( 'Starting up...' )

  logger.debug( 'Creating Server...' )
  app = WerkzeugServer( root_path='/api/v1/', root_version='1.0', debug=DEBUG, get_user=getUser, cors_allow_list=[ '*' ] )
  logger.debug( 'Registering Models...' )

  app.registerNamespace( '/', 'architect.User' )
  app.registerNamespace( '/', 'architect.Contractor' )
  app.registerNamespace( '/', 'architect.TimeSeries' )
  app.registerNamespace( '/', 'architect.Builder' )
  app.registerNamespace( '/', 'architect.Plan' )
  app.registerNamespace( '/', 'architect.Project' )
  app.registerNamespace( '/', 'architect.Inspector' )

  logger.info( 'Validating...' )
  app.validate()

  logger.info( 'Starting Server...' )
  GunicornApp( app, { 'bind': '0.0.0.0:8880', 'loglevel': 'info' } ).run()
  # GunicornApp( app, { 'bind': '127.0.0.1:8880', 'loglevel': 'info' } ).run()
  logger.info( 'Server Done...' )
  logger.info( 'Shutting Down...' )
  logger.info( 'Done!' )
  logger.shutdown()
  sys.exit( 0 )
