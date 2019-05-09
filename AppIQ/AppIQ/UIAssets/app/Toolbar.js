import React from 'react'
import './style.css'
import {IconButton} from "blueprint-react"
class App extends React.Component {
    constructor(props) {
        super(props)
    }

    render() {
        return (
            <div className="row toolbar no-gutters">
             <div className="col-md-12">
               <IconButton
           className="pull-right"
            type="btn--icon btn--gray-ghost"
            size="btn--small"
            icon="icon-refresh"
            onClick={this.props.onReload}
          /></div>
            </div>
        )
    }
}

export default App
