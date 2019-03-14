__author__ = 'nilayshah'

from flask import Flask, render_template, request, redirect, url_for, jsonify
import json, time, logging, os, pprint
import threading
import socket
# import ACI_Info as aci_local
import ACI_Local as aci_local
import AppDInfoData as AppDConnect
import AppD_Alchemy as Database
import generate_d3 as d3
import RecommendedDNObjects as Recommend
from multiprocessing import Process
app = Flask(__name__, template_folder="../UIAssets", static_folder="../UIAssets/public")
app.debug = True
# appd_object = AppDConnect.AppD('10.23.239.14', 'user1', 'customer1', 'welcome')
# appd_object = AppDConnect.AppD('192.168.132.125', 'user1', 'customer1', 'Cisco!123')

# To run anywhere other than APIC
# aci_object = aci_local.ACI("10.23.239.23", "admin", "cisco123")
# aci_object = aci_local.ACI("192.168.130.10", "admin", "Cisco!123")
database_object = Database.Database()
d3Object = d3.generateD3Dict()


def  getInstanceName():
    instance_path = '/home/app/data/credentials.json' # On APIC
    instance_exists = os.path.isfile(instance_path)
    if instance_exists:
        try:
            with open(instance_path, 'r') as creds:
                instance_creds = json.load(creds)
                instanceName = str(str(instance_creds['appd_ip']).split('//')[1])
                #print "AppD Controller = "+ instanceName
                return instanceName
        except:
            instanceName = "N/A"
            pass
    else:
        return "N/A"

@app.route('/check.json', methods=['GET', 'POST'])
def checkFile():
    app.logger.info('Checking if File Exists')
    path = '/home/app/data/credentials.json'
    # path = "/Users/nilayshah/Desktop/AppD_cisco23lab/Cisco_AppIQ/Service/credentials.json"
    file_exists = os.path.isfile(path)
    # print file_exists
    if not file_exists:
        return json.dumps({"payload": "File does not exists", "status_code": "300",
                           "message": "AppDynamics is not configured. Please login!"})
        # return 'False'
    else:
        try:
            with open(path, 'r') as creds:
                # with open('/Users/nilayshah/Desktop/AppD_cisco23lab/Cisco_AppIQTest/Service/credentials.json', 'w+') as creds:
                app_creds = json.load(creds)
                appd_ip = app_creds["appd_ip"]
                appd_port = app_creds["appd_port"]
                appd_user = app_creds["appd_user"]
                appd_account = app_creds["appd_account"]
                appd_pw = app_creds["appd_pw"]
            # print appd_ip
            appd_object = AppDConnect.AppD(appd_ip, appd_port, appd_user, appd_account, appd_pw)
            status = appd_object.check_connection()
            # print status - Change it to app.logger
            if status == 200 or status == 201:
                return json.dumps({"payload": "Signed in", "status_code": "200", "message": "OK"})
            else:
                return json.dumps({"payload": "Not signed in", "status_code": str(status),
                                   "message": "Exited with code: " + str(
                                       status) + ". Please verify AppDynamics connection"})
        except Exception as e:
            return json.dumps({"payload": "Not logged in", "status_code": "300",
                               "message": str(e) + ". Please re-configure AppDynamics Controller!"})


def parseHost(ip):
    print "Printing Host"
    try:
        parsed_host = socket.gethostbyname(ip)
        if parsed_host:
            return ip
    except:
        return ""


@app.route('/login.json', methods=['GET', 'POST'])
def login(appd_creds):
    app.logger.info('Entered Login')
    host = str(appd_creds["appd_ip"])
    appd_port = str(appd_creds["appd_port"])
    appd_user = str(appd_creds["appd_user"])
    appd_account = str(appd_creds["appd_account"])
    appd_pw = str(appd_creds["appd_pw"])
    if 'http://' in host or 'https://' in host:
        parsed_ip = host.split('://')[1]
        if '/' in parsed_ip:
            ip = parsed_ip.split('/')[0]
        else:
            ip = parsed_ip
        valid_ip = parseHost(ip)
        proto = host.split('://')[0]
        appd_ip = proto + "://"+valid_ip
    else:
        appd_ip = "https://"+parseHost(host)
    # parsed_host = parseHost(appd_ip)
    credentials = {'appd_ip': appd_ip, 'appd_port': appd_port, 'appd_user': appd_user, 'appd_account': appd_account,
                   'appd_pw': appd_pw}
    appd_object = AppDConnect.AppD(appd_ip, appd_port, appd_user, appd_account, appd_pw)
    try:
        login_check = appd_object.check_connection()
        # print login_check
        login_resp = dict()

        if login_check == 200 or login_check == 201:
            # path = "/Users/nilayshah/Desktop/AppD_cisco23lab/Cisco_AppIQ/Service/credentials.json"
            path = "/home/app/data/credentials.json"
            Process(target=appd_object.main).start()
            #threading.Thread(target=appd_object.main).start()
            # with open('/home/app/credentials/credentials.json', 'w+') as creds:
            with open(path, 'w+') as creds:
                creds.seek(0)
                creds.truncate()
                json.dump(credentials, creds)
                creds.close()
            app.logger.info('Login Successful!')
            #threading.Thread(target=appd_object.main).start()#appd_object.main()
            time.sleep(4)
            return json.dumps({"payload": "Connection Successful", "status_code": "200",
                               "message": "Credentials Saved!"})  # login_resp
        else:
            app.logger.info("login failed:"+str(login_check))
            return json.dumps({"payload": "Login to AppDynamics Failed", "status_code": str(login_check),
                                "message": "Login to AppDynamics failed, exited with code: " + str(
                                    login_check) + ". Please verify AppDynamics connection"})

    except Exception as e:
        return json.dumps({"payload": "Not signed in", "status_code": "300",
                           "message": "An error occured while saving AppDynamics Credentials. Please try again! Error: "+str(e)})


# payload = [{}]
# json.dumps({"payload":payload,"status_code":"200","message":"OK"})



@app.route('/apps.json',
           methods=['GET'])  # This shall be called from /check.json, for Cisco Live this is the first/start Route
def apps(tenant):
    try:
        #time.sleep(1)
        appsList = database_object.getappList()
        #app.logger.info('List of apps:'+ str(appsList))
        app_dict = {}
        app_list = []
        for each in appsList:
            temp_dict = {'appProfileName': each['appName'], 'isViewEnabled': each['isViewEnabled'],
                         'health': str(each['appHealth']), 'appId': each['appId']}
            app_list.append(temp_dict)
            if each.get('isViewEnabled') == True:
                mapped_objects = mapping(tenant,each['appId'])
        app_dict['app'] = app_list
        #time.sleep(5)
        return json.dumps({"instanceName":getInstanceName(),"payload": app_dict, "status_code": "200", "message": "OK"})
        # return json.dumps(dict)
    except Exception as e:
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not fetch applications from databse. Error: "+str(e)})




@app.route('/mapping.json', methods=['GET'])
def mapping(tenant, appDId):
    try:
        #time.sleep(1)
        appId = str(appDId) + str(tenant)
        mapping_dict = {"source_cluster": [], "target_cluster": []}
        
        # returns the mapping from Mapping Table
        already_mapped_data = database_object.returnMapping(appId)
        #app.logger.info('Already Mapped Data:'+str(already_mapped_data))
        rec_object = Recommend.Recommend()
        mapped_objects = rec_object.correlate_ACI_AppD(tenant, appDId)
        app.logger.info('Post correlation of ACI and AppD')
        #app.logger.info(mapped_objects)
        if not mapped_objects:
            app.logger.info('Empty Mapping dict for appDId:'+str(appDId))
            return json.dumps({"instanceName":getInstanceName(),"payload": mapping_dict, "status_code": "200","message": "OK"})
        if already_mapped_data != None:
            app.logger.info('Mapping to target cluster already exists')
            mapping_dict['target_cluster'] = already_mapped_data
        else:
            app_list = database_object.getappList()
            app.logger.info('AppD App List for Mapping after already mapped: '+str(app_list))
            for each in app_list:
                if each.get('appId') == appDId and each.get('isViewEnabled') == True:
                    app.logger.info("Mapping Empty!")
                    target = []
                    for each in mapped_objects:
                        # print each
                        for entry in each['domains']:
                            if entry['recommended'] == True:
                                target.append({'domainName': entry['domainName'], 'ipaddress': each['ipaddress']})
                                mapping_dict['target_cluster'] = target
                    data_list = []
                    app.logger.info('Target mapping for app:'+str(appDId))
                    for mapping in target:
                        data_list.append({'ipaddress': mapping['ipaddress'], 'domainName': mapping['domainName']})
                    database_object.checkIfExistsandUpdate('Mapping', [appId, data_list])
                    #                    saveMapping(appId,target)
                    view_enabled = enableView(appId, True)
        if mapped_objects:
            for new in mapped_objects:
                mapping_dict['source_cluster'].append(new)
        return json.dumps({"instanceName":getInstanceName(),"payload": mapping_dict, "status_code": "200",
                           "message": "OK"})  # {"source_cluster": mapped_objects, "target_cluster": {{dn:IP},{dn:IP}}}
    except Exception as e:
        app.logger.info('Exception in Mapping, Error:'+str(e))
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not fetch mappings from the database. Error: "+str(e)})


@app.route('/saveMapping.json', methods=['POST'])
def saveMapping(appDId, tenant, mappedData):
    try:
        appId = str(appDId) + str(tenant)
        app.logger.info('Saving Mappings for app:'+str(appId))
        mappedData_dict = json.loads(
            (str(mappedData).strip("'<>() ").replace('\'', '\"')))  # new implementation for GraphQL
        data_list = []
        for mapping in mappedData_dict:
            data_list.append({'ipaddress': mapping['ipaddress'], 'domainName': mapping['domains'][0]['domainName']})
        if not data_list:
            database_object.deleteEntry('Mapping', appId)
            #enableView(appDId, False)
            return json.dumps({"payload": "Saved Mappings", "status_code": "200", "message": "OK"})
        else:
            database_object.deleteEntry('Mapping', appId)
            database_object.checkIfExistsandUpdate('Mapping', [appId, data_list])
            enableView(appDId, True)
            return json.dumps({"payload": "Saved Mappings", "status_code": "200", "message": "OK"})
    except Exception as e:
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not save mappings to the database. Error: "+str(e)})


# This will be called from the UI - after the Mappings are completed
@app.route('/enableView.json')
def enableView(appid, bool):
    try:
        return database_object.enableViewUpdate(appid, bool)
    except Exception as e:
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not enable the view. Error: "+str(e)})


@app.route('/run.json')
def tree(tenantName, appId):
    try:
        #time.sleep(1)
        app.logger.info('Rendering tree view')
        merged_data = merge_aci_appd(tenantName, appId)
        #app.logger.info("Merged data"+str(merged_data))
        response = json.dumps(d3Object.generate_d3_compatible_dict(merged_data))
        return json.dumps({"instanceName":getInstanceName(),"payload": response, "status_code": "200", "message": "OK"})
    except Exception as e:
        app.logger.exception("Error while run.json" + str(e))
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not load the View. Error: "+str(e)})



def merge_aci_appd(tenant, appDId):
    app.logger.info('Merging objects for Tenant:'+str(tenant)+', app_id'+str(appDId))
    try:
        # To change to ACI LOCAL
        aci_local_object = aci_local.ACI_Local(tenant)
        aci_login = aci_local_object.login()
        aci_data = aci_local_object.main()

        # To run anywhere other than on the APIC
        # aci_login = aci_object.apic_login()
        # aci_data = aci_object.main(tenant)
        # aci_object = aci_local.ACI("192.168.130.10", "admin", "Cisco!123")
        # aci_object = aci_local.ACI("10.23.239.23", "admin", "cisco123")
        # aci_data = aci_object.main(tenant)
        # pprint.pprint(aci_data)
        appId = str(appDId) + str(tenant)
        mappings = database_object.returnMapping(appId)
        merge_list = []
        merged_eps = []
        epg_list = []
        total_epg_count = {}
        merged_epg_count = {}
        non_merged_ep_dict = {}
        non_merged_eps = []
        for aci in aci_data:
            if aci['EPG'] not in epg_list:
                epg_list.append(aci['EPG'])
                total_epg_count[aci['EPG']] = 1
            else:
                total_epg_count[aci['EPG']] += 1
            #     epg_count[aci['EPG']] = 1
            if mappings:
                for each in mappings:
                    if aci['IP'] == each['ipaddress'] and each['domainName'] == str(aci['dn']):
                        appd_data = getappD(appDId, aci['IP'])
                        if appd_data:
                            for each in appd_data:
                                each.update(aci)
                                merge_list.append(each)
                                if aci['IP'] not in merged_eps:
                                    merged_eps.append(aci['IP'])
                                    if aci['EPG'] not in merged_epg_count:
                                        merged_epg_count[aci['EPG']] = [aci['IP']]
                                    else:
                                        merged_epg_count[aci['EPG']].append(aci['IP'])
        for aci in aci_data:
            if aci['IP'] not in merged_eps:
                if aci['EPG'] not in non_merged_ep_dict:
                    non_merged_ep_dict[aci['EPG']] = {aci['CEP-Mac']: str(aci['IP'])}
                else:
                    if not non_merged_ep_dict[aci['EPG']]:
                        non_merged_ep_dict[aci['EPG']] = {}
                    if aci['CEP-Mac'] in non_merged_ep_dict[aci['EPG']].keys():
                        multipleips = non_merged_ep_dict[aci['EPG']][aci['CEP-Mac']]+", " + str(aci['IP'])
                        non_merged_ep_dict[aci['EPG']].update({aci['CEP-Mac']: multipleips})
                    else:
                        non_merged_ep_dict[aci['EPG']].update({aci['CEP-Mac']: str(aci['IP'])})
        final_non_merged = {}
        if non_merged_ep_dict:
            for key,value in non_merged_ep_dict.items():
                if not value:
                    continue
                final_non_merged[key] = value
        fractions = {}
        if total_epg_count:
            for epg in total_epg_count.keys():
                #fractions[epg] = str(len(merged_epg_count.get(epg, [])))+"/"+str(total_epg_count.get(epg, []))
                un_map_eps = int(total_epg_count.get(epg, [])) - len(merged_epg_count.get(epg, []))
                fractions[epg] = int(un_map_eps)
                app.logger.info('Total Unmapped Eps (Inactive):'+str(un_map_eps))
        updated_merged_list = []
        if fractions:
            for key, value in fractions.iteritems():
                for each in merge_list:
                    if key == each['EPG']:
                        each['fraction'] = value
                        each['Non_IPs'] = final_non_merged.get(key, {})
                        updated_merged_list.append(each)
        final_list = []
        for each in updated_merged_list:
            if 'fraction' not in each.keys():
                each['fraction'] = '0'
                each['Non_IPs'] = {}
            final_list.append(each)
        app.logger.info('Merge complete. Total objects correlated :'+str(len(final_list)))
        return final_list#updated_merged_list#,total_epg_count # TBD for returning values
    except Exception as e:
        app.logger.exception("Error while merge_aci_data"+str(e))
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not load the Merge ACI and AppDynamics objects. Error: "+str(e)})





def getappD(appId, ep):
    try:
        app = database_object.returnApplication('appId', appId)
        tiers = database_object.returnTiers('appId', appId)
        hevs = database_object.returnHealthViolations('appId', appId)
        aci_ips_list = []
        appd_list = []
        appd_each_dict = {}
        for application in app:
            hev = database_object.returnHealthViolations('appId', application.appId)
            for tier in tiers:
                seps = database_object.returnServiceEndpoints('tierId', tier.tierId)
                sepList = []
                for sep in seps:
                    if isinstance(sep.sep, dict):
                        sepList.append(sep.sep)
                hevList = []
                hevs = database_object.returnHealthViolations('tierId', tier.tierId)
                for hev in hevs:
                    if (int(hev.violationId) >= 0):
                        hevList.append({"Violation Id": (hev.violationId), "Start Time": str(hev.startTime),
                                        'Affected Object': str(hev.businessTransaction),
                                        'Description': str(hev.description), 'Severity': str(hev.severity)})
                nodes = database_object.returnNodes('tierId', tier.tierId)
                #print "hevList"
                #print hevList
                for node in nodes:
                    if ep in node.ipAddress:
                        appd_list.append({'appId': application.appId, 'appName': str(application.appName), 'appHealth': str(
                            application.appMetrics['data'][0]['severitySummary']['performanceState']),
                                          'tierId': tier.tierId, 'tierName': str(tier.tierName),
                                          'tierHealth': str(tier.tierHealth),
                                          'nodeId': node.nodeId, 'nodeName': str(node.nodeName),
                                        'nodeHealth': str(node.nodeHealth), 'ipAddressList': node.ipAddress,
                                        'serviceEndpoints': sepList, 'tierViolations': hevList})
        return appd_list
    except Exception as e:
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not load the View. Error: "+str(e)})



@app.route('/details.json')  # Will take tenantname and appId as arguments
def get_details(tenant, appId):
    try:
        #time.sleep(1)
        details_list = []
        merged_data = merge_aci_appd(tenant, appId)

        # To run on APIC
        aci_local_object = aci_local.ACI_Local(tenant)

        # To run anywhere other than APIC
        # aci_local_object = aci_local.ACI("192.168.130.10", "admin", "Cisco!123")

        for each in merged_data:
            epg_health = aci_local_object.get_epg_health(str(tenant), str(each['AppProfile']), str(each['EPG']))
            details_list.append(
                {'IP':each['IP'],'epgName': each['EPG'], 'epgHealth': epg_health, 'endPointName': each['VM-Name'],
                'tierName': each['tierName'],
                'tierHealth': each['tierHealth']})
        details = [dict(t) for t in set([tuple(d.items()) for d in details_list])]
        return json.dumps({"instanceName":getInstanceName(),"payload": details, "status_code": "200", "message": "OK"})
    except Exception as e:
        return json.dumps({"payload": {}, "status_code": "300", "message": "Could not load the Details. Error: "+str(e)})

    # return json.dumps(details_list)


# Need to remove the below codes
@app.route('/index')
def renderindex():
    return render_template('app.html')


@app.route('/mappings.html', methods=['GET', 'POST'])
def renderMapping():
    appId = request.args.get('appId')
    return render_template('mapping.html', appId=appId)


@app.route('/tree.html', methods=['GET', 'POST'])
def renderTree():
    # appd_ip, appd_port, appd_user, appd_account, appd_pw = ""
    try:
        # path = "/Users/nilayshah/Desktop/AppD_cisco23lab/Cisco_AppIQ/Service/credentials.json"
        # path = "/home/app/credentials/credentials.json"
        # with open(path, 'r') as creds:
        #     app_creds = json.loads(creds)
        #     appd_ip = app_creds["appd_ip"]
        #     appd_port = app_creds["appd_port"]
        #     appd_user = app_creds["appd_user"]
        #     appd_account = app_creds["appd_account"]
        #     appd_pw = app_creds["appd_pw"]
        # appd_object = AppDConnect.AppD(appd_ip, appd_port, appd_user, appd_account, appd_pw)
        # appd_object.main()
        return render_template('tree.html')
    except:
        return render_template('login.html')

#
#


# ######################################################################################################################
# Test codes for URLs
# merge_aci_appd('AppDynamics')
# -1. Create the database
# database_object.createTables()
# 0. Fill in the database
# appd_object = AppDConnect.AppD('192.168.132.125', 'user1', 'customer1', 'Cisco!123')
# appd_object.main('Start')
# 1. List apps:
# pprint.pprint(apps())
# time.sleep(3)
# 2. Select app = appId (5,8)
# appId = 5

# 3. Get current mappings
# pprint.pprint(mapping(appId))
# time.sleep(3)
# 4. Select mapped objects and save
# mapped_data = []
# mapped_data = [{'domainName': 'uni/tn-AppDynamics/ap-AppD-AP1-EcommerceApp/epg-AppD-Ord',
#                      'ipaddress': '10.10.10.18'},{'domainName': 'uni/tn-AppDynamics/ap-AppD-AP1-EcommerceApp/epg-AppD-Ord',
#                      'ipaddress': '10.10.10.19'}]
# mapped_data = [{'domainName': 'uni/tn-AppDynamics/ap-AppD-AP2-Jeti/epg-AppD-Jeti1',
#                 'ipaddress': '20.20.20.11'},
#                {'domainName': 'uni/tn-AppDynamics/ap-AppD-AP2-Jeti/epg-AppD-Jeti2', 'ipaddress': '20.20.20.12'}]
# pprint.pprint(saveMapping(appId, mapped_data))
# time.sleep(3)
# 5. show if app is enabled:
# pprint.pprint(apps())
# time.sleep(3)
# 6. Show current mappings
# pprint.pprint(mapping(appId))
# time.sleep(3)

# 7. Show merged data
# pprint.pprint(tree(appId))
# time.sleep(3)
# 8. Show d3 compatible data



# ######################################################################################################################
#
# Steps to take: This guide i to provide a step by step instructions for the code flow:
#     0. Initialize all vars and create database tables and autopopulate any variables
#     1. App login: use /login route
#         a. If not loggged in already> Load login page
#         b. Once submitted, start the thread and load database tables
#         c. populate it with AppD data
#         d. Run it every 30 seconds and insert new data or update existing data
#
#     2. (First view of the app) List of AppD applications. Use /apps route
#         a. List will show total number of apps and app health, app Name, app Id for each app
#         b. There will be two buttons for each app: i. Mapping ii. View
#         c. The Mapping will always be clickable, the View will be clickable once mapping is complete by the user
#         d. Once mapping is complete app table will be populated with 'isViewEnabled' = True (defaults to False)
#         e. To change from False to True use /enableView route - this will be called from mapping view upon save
#
#     3. (Second view of the app) This will be the mapping view for the clicked app
#         a. The route to populate the details for the clicked app will be /mapping route
#         b. The mapping table will show the IPs and their corresponding dns for a given tenant for the given app
#             a. The IPs will be taken by correlating IPs in the App and IPs in the given tenant
#         c. There is one table with three columns:
#             i. IP address
#             ii. dn object - One IP address can have two or more dn object
#                 1. For this case, show two dns for the same IP address (row)
#                 2. Show the recommended one - if the IP exists for the same app profile and same epg,
#                     it is the recommended one else if the same app profile, else same tenant
#                 3. Based of the 1st, 2nd or the 3rd case - put out the recommendation - 1, then 2, then 3
#             iii. Radio button for each of the dn
#         d. Once the radio buttons are selected and the save button is clicked, run a route /saveMapping
#         e. This mapping will be saved in a table with appId for the given app and primary key as the dn
#         f. The save will change isViewEnabled value in the app table and redirect the page to the First View '/apps'
#
#     4. The Tree(View) button will be enabled for the apps that have mapping complete and show the tree structure and
#         upon clicking the button, the UI will redirect to app view tree structure diagram (html)
#         a. The tree will consists of the app node, tier node, and Node node as already has been developed
#         b. The backend will give the data as previously done
#         c. The route /tree will be run for the data fetch
#         d. This will be run in the background every some seconds until user goes back to the app view
#
#     5. The user comes back again to the app, the /check route checks if the app is configured or not,
#         and redirects it to /login route or the /apps route depending on the return value
#
#
# *if there are two same IPs for handle them in mapping view
#
# NOTE: The following is the user interaction and its process from UI to backend and then backend to UI
# User Interaction with the App |  AppRoute to the backend |  Data UI passes to backend |  Data Backend gives to the front end
# 1. Click on the App             |  /apps.json              |  tenantName                |  [{'appName': u'EComm-NPM-Demo', 'isViewEnabled': True, 'appHealth': 'WARNING', 'appId': 5}, {'appName': u'NPMApplication', 'isViewEnabled': True, 'appHealth': 'NORMAL', 'appId': 8}]
# 2. Click on Mapping button      | /mapping.json            |  appId, tenantName         |  # mappings = [{'IP': IP1, 'dns': [{'dn': dn1_1, 'isRecommended': True}, {{'dn': dn1_2, 'isRecommended': False}}]},
# 3. User Adds & exits the mapping view |  /saveMapping.json |  appId, mappedData = [{'IP': IP, 'dn': dn}, {'IP': IP2, 'dn': dn2}] |  None
# 4. User Clicks on Tree view for an app | /tree.json        |  tenant, appId             | d3 compatible dict
#
# #######################################################################################################################

# if __name__ == '__main__':
#     # Setup logging
#     fStr = '%(asctime)s %(levelname)5s %(message)s'
#     # logging.basicConfig(filename='/home/app/log/app.log', format=fStr, level=logging.DEBUG)
#
#     # Run app flask server
#      app.run(host='0.0.0.0', ssl_context='adhoc', port = 443, debug=True)
#     # app.run(host='127.0.0.1', port=5000, threaded=True)
#     database_object.createTables()
#     # appd_object = AppDConnect.AppD('192.168.132.125', 'user1', 'customer1', 'Cisco!123')
#     appd_object = AppDConnect.AppD('10.23.239.14', 'user1', 'customer1', 'welcome')
#
#     appd_object.startThread()
#     # appdThread = threading.Thread(appd_object.main())
#     # appdThread.start()
#     # threading.thread(10, appd_object.main())
#     # appd_object.main()
#     # app.run(host='0.0.0.0', port=80, threaded=True)
#     # appId = 5
#     # mapped_data = [{'domainName': 'uni/tn-AppDynamics/ap-AppD-AP1-EcommerceApp/epg-AppD-Ord',
#     #                  'ipaddress': '10.10.10.18'},{'domainName': 'uni/tn-AppDynamics/ap-AppD-AP1-EcommerceApp/epg-AppD-Ord',
#     #                  'ipaddress': '10.10.10.19'}]
#     # pprint.pprint(saveMapping(appId, mapped_data))
#     app.run()
#
