import React from 'react'
import AppInfo from './AppInfo'
import Toolbar from './Toolbar'
import { strictEqual } from 'assert';
import { stringify } from 'querystring';
import Header from './Header'
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import AppTable from "./AppTable"
import './style2.css'

function getCookieVal(offset) {
    var endstr = document.cookie.indexOf(";", offset);
    if (endstr == -1) {
        endstr = document.cookie.length;
    }
    return unescape(document.cookie.substring(offset, endstr));
}

function getCookie(name) {
    var arg = name + "=";
    var alen = arg.length;
    var clen = document.cookie.length;
    var i = 0;
    var j = 0;
    while (i < clen) {
        j = i + alen;
        if (document.cookie.substring(i, j) == arg) {
            return getCookieVal(j);
        }
        i = document.cookie.indexOf(" ", i) + 1;
        if (i === 0) {
            break;
        }
    }
    return null;
}

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
    vars[key] = value;
    });
    return vars;
}

var jsonData;
var headerInstanceName;

class Container extends React.Component {
    constructor(props) {
        super(props);
        this.sortField = "appProfileName";
        this.sortType = "asc";
        var urlToParse = location.search;
        let urlParams = {};
        urlToParse.replace(
            new RegExp("([^?=&]+)(=([^&]*))?", "g"),
            function ($0, $1, $2, $3) {
                urlParams[$1] = $3;
            }
        );
        let result = urlParams;

        const rx = /Tenants:(.*)\|/g;
        const topUrl = top.location;
        const tenantNames = rx.exec(topUrl);
        
        this.tenantName = tenantNames[1];

        this.notify = this.notify.bind(this);
        this.getData = this.getData.bind(this);
        this.getStaticData = this.getStaticData.bind(this);

        this.getData();
        // this.getStaticData();
        this.state = {
            "jsonData": jsonData
        }

        this.reloading = this.reloading.bind(this);
        this.handleLoginClick = this.handleLoginClick.bind(this);

        if(getUrlVars()['gqlerror'] != undefined) {
            const messages = JSON.parse(localStorage.getItem('message'));
            if(messages != null) {
                messages.map(item=>{
                    this.notify(item.message);
                });
            }
        localStorage.removeItem('message')
        }

        let reloader = setInterval(this.reloading, 30000);
    }

    shouldComponentUpdate(nextProps, nextState) {
        if (JSON.stringify(this.state.jsonData) === JSON.stringify(nextState.jsonData) ) {
          return false;
        }
        return true;
    }

    getData() {
        jsonData = [];
        try {
            /**
            * Use this.httpGet to get data from REST API
            */
            let payload = {
                query: 'query{Application(tn:"' + this.tenantName + '"){apps}}'
            }
            let main_data_raw = this.httpGet(document.location.origin + "/appcenter/Cisco/AppIQ/graphql.json", payload);
            const main_data_json = JSON.parse(main_data_raw);

            if('errors' in main_data_json) {
                // Error related to query
                const message_set = true;
                main_data_json.errors.map(item=>{
                    this.notify(item.message);
                });
            }
            else {
                const apps = JSON.parse(JSON.parse(main_data_raw).data.Application.apps);
                if(apps.status_code != "200") {
                    // Problem with backend fetching data
                    const message = {"errors": [{
                        "message": apps.message
                    }]}

                    message.errors.map(item=>{
                        this.notify(item.message);
                    });
                }
                else {
                    // success
                    headerInstanceName = JSON.parse(JSON.parse(main_data_raw).data.Application.apps).instanceName;
                    jsonData = JSON.parse(JSON.parse(main_data_raw).data.Application.apps).payload.app;
                }
            }
        }
        catch(e) {
            // Problem fetching data
            console.log("Error while running GraphQl query." + e);
            this.notify("Error while running fetching data for App list.");
        }
    }

    getStaticData() {
        jsonData =  [
            {
                "health": "NORMAL",
                "appProfileName": "TestApplication1",
                "isViewEnabled": true,
                "appId": 9
            },
            {
                "health": "NORMAL",
                "appProfileName": "EComm-NPM-Demo",
                "isViewEnabled": true,
                "appId": 13
            }
        ];
    }

    /**
    * @param {string} theUrl The URL of the REST API
    *
    * @return {string} The response received from portal
    */
    httpGet(theUrl, payload) {
        window.APIC_DEV_COOKIE = getCookie("app_Cisco_AppIQ_token");
        window.APIC_URL_TOKEN = getCookie("app_Cisco_AppIQ_urlToken");
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("POST", theUrl, false); // false for synchronous request
        xmlHttp.setRequestHeader("Content-type", "application/json");
        xmlHttp.setRequestHeader("DevCookie", window.APIC_DEV_COOKIE);
        xmlHttp.setRequestHeader("APIC-challenge", window.APIC_URL_TOKEN);
        xmlHttp.send(JSON.stringify(payload));
        return xmlHttp.responseText;
    }

    notify(message) {
        toast.error(message, {
            position: toast.POSITION.BOTTOM_CENTER
          });
    }

    /**
    *@param {object} sortData object to sort
    *@param {string} sortField The name of field to sort with
    *@return {object} the sorted object
    */
    sortTable(sortDataObject, sortField) {
        console.log(sortDataObject);
        let sortData = sortDataObject;

        if (this.sortField == sortField) {
            /* toggle asc/desc */
            this.sortType = (this.sortType) == "asc" ? "desc" : "asc";

            /* sort according to new asc/desc */
            if (this.sortType == "asc") {
                sortData.sort(function (a, b) {
                    if (a[sortField] < b[sortField]) {
                        return -1;
                    }
                    if (a[sortField] > b[sortField]) {
                        return 1;
                    }
                    return -1;
                });
            }
            else {
                sortData.sort(function (a, b) {
                    if (a[sortField] > b[sortField]) {
                        return -1;
                    }
                    if (a[sortField] < b[sortField]) {
                        return 1;
                    }

                    // names must be equal
                    return -1;
                });
            }
        }
        else {
            /* sort with sortField in asc : set this.sortType to asc */
            this.sortField = sortField;
            this.sortType = "asc";
            sortData.sort(function (a, b) {
                if (a[sortField] < b[sortField]) {
                    return -1;
                }
                if (a[sortField] > b[sortField]) {
                    return 1;
                }
                return -1;
            });
        }

        sortDataObject = sortData;
        this.setState({
            'jsonData': sortDataObject
        });
    }

    reloading() {
        var urlToParse = location.search;
        let urlParams = {};
        urlToParse.replace(
            new RegExp("([^?=&]+)(=([^&]*))?", "g"),
            function ($0, $1, $2, $3) {
                urlParams[$1] = $3;
            }
        );
        let result = urlParams;
        let payload = {
            query: 'query{Application(tn:"' + this.tenantName + '"){apps}}'
        }

        this.getData();

        // this.getStaticData();

        this.setState({
            "jsonData": jsonData
        })
    }

    handleLoginClick() {
        window.location.href = "login.html?reset=1";
    }

    render() {
        /* retrieve JSON data into 'data' */
        let data = this.state.jsonData;
        /* generate list of AppInfo components with data as props */
        const list = data;
        console.log("list data")
        console.log(list)
        let odd = false;
        let idCounter = 0;
        let appInfoList = list.map((item) => {
            odd = odd == false ? true : false;
            idCounter = idCounter + 1;
            return <AppInfo data={item} key={idCounter} highlight={odd} tenantName={this.tenantName} />
        })



        return (
            <div>
                <Header text=" List of Applications" applinktext="" instanceName={headerInstanceName}/>
                <Toolbar onReload={this.reloading} />
                {/* <DetailsPane/> */}
                {/* <table className="info-table" border="0" width="100%">
                    <th className="sortable" onClick={() => { this.sortTable(data, "appProfileName") }}>Application Name</th>
                    <th className="sortable" onClick={() => { this.sortTable(data, "health") }}>Health</th>
                    <th></th>
                    <th></th>
                    <tbody>
                        {appInfoList}
                    </tbody>
                </table> */}
                <AppTable rows={list} tenantName={this.tenantName}></AppTable>
                <br/>
          <ToastContainer />
            </div>
        )
    }
}

export default Container
