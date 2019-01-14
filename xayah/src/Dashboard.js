import React, { Component } from 'react';
import { Map, TileLayer, Polygon, Tooltip, Circle } from 'react-leaflet';
import Navbar from 'react-bootstrap/lib/Navbar';
import Nav from 'react-bootstrap/lib/Nav';
import './App.css';

class Precinct extends Component {
  constructor(props) {
    super(props)

    this.nodeCoord = this.nodeCoord.bind(this)
  }
  // props:
    // name: name of precinct
    // color: color of precinct
    // map: map to render to
    // vertexes: vertex coordinates of polygon
  nodeCoord() {
    let x_total = 0
    let y_total = 0
    this.props.vertexes.map((item) => {
      x_total += item[0];
      y_total += item[1];

    })
    return [x_total / this.props.vertexes.length, y_total / this.props.vertexes.length];
  }
  render() {
    return (
      <div>
        <Polygon color={this.props.color} positions={this.props.vertexes}>
          <Tooltip direction="bottom" opacity={1}>{this.props.name}</Tooltip>
          <Circle center={this.nodeCoord()} opacity={100} fillcolor={this.props.color} radius={2} />
        </Polygon>
      </div>
    );
  }
}

class PrecinctMap extends Component {
  constructor(props) {
    super(props)
    this.state = {
      showConnectivity: false, // show the connectivity (lines + nodes)
      showPolygons: true, // show the precinct polygons
      edges: [], // node connection lines
      precincts: [], // precincts
      districts: [], // districts, where the index corresponds to an rid and the value is the district
      lat: 0, // camera settings
      lng: 0,
      zoom: 1
    }
  }
  componentDidMount() {
    var ws = new WebSocket("ws://127.0.0.1:3001");
    ws.onmessage = function (event) {
        //event.data
    };
    this.timerID = setInterval(
      () => this.tick(),
      1000
    );
  }
  tick() {
    this.setState({
      precincts: []
    });
  }
  render() {
    const position = [this.state.lat, this.state.lng] // this.state.precincts[0].nodeCoord()
    return (
      <Map center={position} zoom={this.state.zoom} id="mapid" style={{height: "50vh"}}>
        <TileLayer attribution="Shout out to the amazing folks @ <a href='https://openstreetmap.org'>OpenStreetMap</a>" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
        {this.state.precincts}
      </Map>
    );
  }
}

class Dashboard extends Component {
  constructor(props) {
    super(props)
    this.state = {
      currentPage: 0,
      steps: 0,
    }
  }
  render() {
    return (
      <div>
      <Navbar bg="dark" variant="dark">
        <Navbar.Brand>
          <img className="d-inline-block align-top" src="xayah.png" alt="" height="30" width="30"/>
          {' Project Xayah'}
        </Navbar.Brand>
        <Nav className="mr-auto">
          <Nav.Link active={this.state.currentPage === 0}>Visualization</Nav.Link>
          <Nav.Link active={this.state.currentPage === 1}>Rakan Statistics</Nav.Link>
          <Nav.Link active={this.state.currentPage === 2}>Other States</Nav.Link>
        </Nav>
        <Nav>
          <Nav.Link disabled={this.state.steps === 0}>Export {this.state.steps} Steps</Nav.Link>
        </Nav>
      </Navbar>
      <PrecinctMap />
      </div>
    );
  }
}

export default Dashboard;
