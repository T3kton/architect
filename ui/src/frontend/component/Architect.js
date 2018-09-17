import CInP from './cinp';

class Architect
{
  constructor( host )
  {
    this.cinp = new CInP( host );
  };

  login = () =>
  {
    this.cinp.call( '/api/v1/User/Session(login)', { 'username': username, 'password': password } )
      .then(
        function( result )
        {
          resolve( result.data );
        },
        function( reason )
        {
          reject( reason );
        }
      );
  };

  logout = () => {};
  keepalive = () => {};

  projectLoaderRescan = () =>
  {
    return this.cinp.call( '/api/v1/Project/Loader(rescan)')
  };

  applyProjectChange = ( id ) =>
  {
    return this.cinp.call( '/api/v1/Project/Change:' + id + ':(apply)')
  };

  getChangeList = () =>
  {
    return this.cinp.getFilteredObjects( '/api/v1/Project/Change' );
  };

  getPlanList = () =>
  {
    return this.cinp.getFilteredObjects( '/api/v1/Plan/Plan' );
  };

  getInstanceList = () =>
  {
    return this.cinp.getFilteredObjects( '/api/v1/Builder/Instance' );
  };

  getActionList = () =>
  {
    return this.cinp.getFilteredObjects( '/api/v1/Builder/Action' );
  };

  getJobList = () =>
  {
    return this.cinp.getFilteredObjects( '/api/v1/Builder/Job' );
  };

  getPlan = ( id ) =>
  {
    return this.cinp.get( '/api/v1/Plan/Plan:' + id + ':' );
  };

  getInstance = ( id ) =>
  {
    return this.cinp.get( '/api/v1/Builder/Instance:' + id + ':' );
  };

  getAction = ( id ) =>
  {
    return this.cinp.get( '/api/v1/Builder/Action:' + id + ':' );
  };

  getJob = ( id ) =>
  {
    return this.cinp.get( '/api/v1/Builder/Job:' + id + ':' );
  };
}

export default Architect;
