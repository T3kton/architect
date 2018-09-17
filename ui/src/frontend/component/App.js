import React from 'react';
import { Layout, NavDrawer, Panel, Sidebar, Chip, FontIcon, AppBar, Navigation, Button } from 'react-toolbox';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import Home from './Home';
import Project from './Project';
import Plan from './Plan';
import Instance from './Instance';
import Action from './Action';
import Job from './Job';
import ServerError from './ServerError';
import Architect from './Architect';

class App extends React.Component
{
  state = {
    leftDrawerVisable: true,
    autoUpdate: false
  };

  constructor( props )
  {
    super( props );
    this.architect = new Architect( window.API_BASE_URI );
    this.architect.cinp.server_error_handler = this.serverError;
  }

  menuClick = () =>
  {
    this.setState( { leftDrawerVisable: !this.state.leftDrawerVisable } );
  };

  serverError = ( msg, trace ) =>
  {
    this.refs.serverError.show( msg, trace );
  };

  doUpdate = () =>
  {
    this.setState();
  };

  toggleAutoUpdate = () =>
  {
    var state = !this.state.autoUpdate;
    if( state )
    {
      this.timerID = setInterval( () => this.doUpdate(), 10000 );
    }
    else
    {
      clearInterval( this.timerID );
    }
    this.setState( { autoUpdate: state } );
  };

  componentDidMount()
  {
    this.setState( { autoUpdate: false } );
    clearInterval( this.timerID );
  }

  componentWillUnmount()
  {
    clearInterval( this.timerID );
  }

  render()
  {
    return (
<Router>
  <div>
    <ServerError ref="serverError" />
    <div>
      <Layout>
        <NavDrawer pinned={ this.state.leftDrawerVisable }>
          <Navigation type="vertical">
            <Link to="/"><Button icon="home">Home</Button></Link>
            <Link to="/project"><Button icon="business">Project</Button></Link>
            <Link to="/plans"><Button icon="business">Plan</Button></Link>
            <Link to="/instances"><Button icon="business">Instances</Button></Link>
            <Link to="/actions"><Button icon="business">Actions</Button></Link>
            <Link to="/jobs"><Button icon="business">Jobs</Button></Link>
          </Navigation>
        </NavDrawer>
        <Panel>
          <AppBar title="Architect" leftIcon="menu" rightIcon="face" onLeftIconClick={ this.menuClick }>
            <Button icon='update' inverse={ !this.state.autoUpdate } onClick={ this.toggleAutoUpdate } />
            <Button icon='sync' inverse onClick={ this.doUpdate } />
            <Chip><Button icon='settings' disabled /></Chip>
          </AppBar>
          <div ref="content">
            <Route exact={true} path="/" component={ Home }/>
            <Route path="/plan/:id" render={ ( { match } ) => ( <Plan id={ match.params.id } detailGet={ this.architect.getPlan } /> ) } />
            <Route path="/instance/:id" render={ ( { match } ) => ( <Instance id={ match.params.id } detailGet={ this.architect.getInstance } /> ) } />
            <Route path="/action/:id" render={ ( { match } ) => ( <Action id={ match.params.id } detailGet={ this.architect.getAction } /> ) } />
            <Route path="/job/:id" render={ ( { match } ) => ( <Job id={ match.params.id } detailGet={ this.architect.getJob } /> ) } />

            <Route exact={true} path="/project" render={ () => ( <Project listGet={ this.architect.getChangeList } rescan={ this.architect.projectLoaderRescan } apply={ this.architect.applyProjectChange } /> ) } />
            <Route exact={true} path="/plans" render={ () => ( <Plan listGet={ this.architect.getPlanList } /> ) } />
            <Route exact={true} path="/instances" render={ () => ( <Instance listGet={ this.architect.getInstanceList } /> ) } />
            <Route exact={true} path="/actions" render={ () => ( <Action listGet={ this.architect.getActionList } /> ) } />
            <Route exact={true} path="/jobs" render={ () => ( <Job listGet={ this.architect.getJobList } /> ) } />
          </div>
        </Panel>
      </Layout>
    </div>

  </div>
</Router>
);
  }

}

export default App;
