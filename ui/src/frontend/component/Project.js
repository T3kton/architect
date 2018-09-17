import React from 'react';
import CInP from './cinp';
import { Table, TableHead, TableRow, TableCell, Button } from 'react-toolbox';


class Project extends React.Component
{
  state = {
      change_list: [],
      load_results: ''
  };

  rescan = () =>
  {
    this.props.rescan()
    .then( ( results ) =>
    {
      this.setState( { load_results: results.data } );
      this.update( this.props );
    },
    ( error ) => alert( 'Error Rescanning Project: "' + error.reason + '": "' + error.detail + '"' ) );
  };

  apply = ( id ) =>
  {
    this.props.apply( id )
    .then( ( result ) =>
    {
      this.update( this.props );
    },
    ( error ) => alert( 'Error Applying Change Project: "' + error.reason + '": "' + error.detail + '"' ) );
  };

  componentDidMount()
  {
    this.update( this.props );
  }

  componentWillReceiveProps( newProps )
  {
    this.setState( { change_list: [], load_results: '' } );
    this.update( newProps );
  }

  update( props )
  {
    props.listGet()
      .then( ( result ) =>
      {
        var change_list = [];
        for ( var id in result.data )
        {
          var change = result.data[ id ];
          id = CInP.extractIds( id )[0];
          change_list.push( { id: id,
                              action: change.action,
                              target_id: change.target_id,
                              target_val: change.target_val,
                              current_val: change.current_val,
                              type: change.type,
                              site: change.site,
                              created: change.created,
                              updated: change.updated,
                            } );
        }

        this.setState( { change_list: change_list } );
      } );
  }

  render()
  {
    return (
      <div>
        <Button onClick={ this.rescan }>Rescan</Button>
        <div><strong>{ this.state.load_results }</strong></div>
        <Table selectable={ false } multiSelectable={ false }>
          <TableHead>
            <TableCell></TableCell>
            <TableCell>Id</TableCell>
            <TableCell>Action</TableCell>
            <TableCell>Target Id</TableCell>
            <TableCell>Target Value</TableCell>
            <TableCell>Current Value</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Site</TableCell>
            <TableCell>Created</TableCell>
            <TableCell>Updated</TableCell>
          </TableHead>
          { this.state.change_list.map( ( item, index ) => (
            <TableRow key={ index } >
              <TableCell><Button onClick={ () => { this.apply( item.id ) } }>Apply</Button></TableCell>
              <TableCell>{ item.id }</TableCell>
              <TableCell>{ item.action }</TableCell>
              <TableCell>{ item.target_id }</TableCell>
              <TableCell>{ item.target_val }</TableCell>
              <TableCell>{ item.current_val }</TableCell>
              <TableCell>{ item.type }</TableCell>
              <TableCell>{ item.site }</TableCell>
              <TableCell>{ item.created }</TableCell>
              <TableCell>{ item.updated }</TableCell>
            </TableRow>
          ) ) }
        </Table>
      </div>
    );

  }
};

export default Project;
