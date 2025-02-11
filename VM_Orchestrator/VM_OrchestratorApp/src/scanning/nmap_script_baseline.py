# pylint: disable=import-error
from VM_OrchestratorApp.src.utils import slack, utils, mongo, image_creator, redmine
from VM_OrchestratorApp.src import constants
from VM_OrchestratorApp.src.objects.vulnerability import Vulnerability
from VM_Orchestrator.settings import settings

import subprocess
import os
import xmltodict
import json
import base64
import uuid
import copy
from time import sleep
from PIL import Image
from io import BytesIO

MODULE_NAME = 'Nmap Baseline module'
MODULE_IDENTIFIER = 'nmap_baseline_module'
SLACK_NOTIFICATION_CHANNEL = '#vm-nmap-baseline'

def cleanup(path):
    try:
        os.remove(path + '.xml')
        os.remove(path + '.nmap')
        os.remove(path + '.gnmap')
    except FileNotFoundError:
        pass
    return

def send_module_status_log(scan_info, status):
    mongo.add_module_status_log({
            'module_keyword': MODULE_IDENTIFIER,
            'state': status,
            'domain': scan_info['domain'],
            'found': None,
            'arguments': scan_info
        })
    return

def handle_target(info):
    info = copy.deepcopy(info)
    print('Module Nmap baseline starting against %s alive urls from %s' % (str(len(info['target'])), info['domain']))
    slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'start')
    
    scanned_hosts = list()
    for url in info['target']:
        sub_info = copy.deepcopy(info)
        sub_info['target'] = url
        try:
            host = url.split('/')[2]
        except IndexError:
            host = url
        if host not in scanned_hosts:
            basic_scan(sub_info, host)
        scanned_hosts.append(host)

    print('Module Nmap baseline finished against %s' % info['domain'])
    slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'end')

    return


def handle_single(info):
    info = copy.deepcopy(info)
    print('Module Nmap baseline starting against %s' % info['target'])
    slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'start')
    
    # We receive the url with http/https, we will get only the host so nmap works
    host = info['target']
    if info['type'] == 'url':
        host = host.split('/')[2]
    basic_scan(info, host)

    print('Module Nmap baseline finished against %s' % info['target'])
    slack.send_module_end_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'end')
    return

def add_vuln_to_mongo(scan_info, scan_type, description, img_str):
    vuln_name = ""
    if scan_type == 'plaintext_services':
        vuln_name = constants.PLAINTEXT_COMUNICATION
    else:
        vuln_name = constants.UNNECESSARY_SERVICES

    vulnerability = Vulnerability(vuln_name, scan_info, description)

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    random_filename = uuid.uuid4().hex
    output_dir = ROOT_DIR+'/tools_output/' + random_filename + '.png'
    im = Image.open(BytesIO(base64.b64decode(img_str)))
    im.save(output_dir, 'PNG')
    vulnerability.add_attachment(output_dir, 'nmap-result.png')
    slack.send_vuln_to_channel(vulnerability, SLACK_NOTIFICATION_CHANNEL)
    vulnerability.id = mongo.add_vulnerability(vulnerability)
    redmine.create_new_issue(vulnerability)
    os.remove(output_dir)
    return

def check_ports_and_report(scan_info,ports,scan_type,json_scan,img_str):
    message=''
    nmap_ports = list()
    ports_numbers = list()
    try:
        if type(json_scan['nmaprun']['host']['ports']['port']) == list:
            nmap_ports += json_scan['nmaprun']['host']['ports']['port']
            ports_numbers = [port['@portid'] for port in nmap_ports]
        else:
            nmap_ports.append(json_scan['nmaprun']['host']['ports']['port'])
        for port in nmap_ports:
            if port['@portid'] in ports and port['state']['@state'] == 'open':
                message+= 'Port: '+port['@portid']+'\n'
                message+= 'Service: '+port['service']['@name']+'\n'
                if '@product' in port['service']:
                    message+= 'Product: '+port['service']['@product']+'\n'
                if '@version' in port['service']:
                    message+= 'Version: '+port['service']['@version']+'\n\n'
                http_and_https = (port['@portid'] == '80' and all(elem in ports_numbers  for elem in ['80','443']))
                if not http_and_https:
                    add_vuln_to_mongo(scan_info, scan_type, message, img_str)
    except KeyError as e:
        message = None
    return

def basic_scan(scan_info, url_to_scan):
    plaintext_ports=["21","23","80"]
    remote_ports=["135","445","513","514","1433","3306","3389"]
    random_filename = uuid.uuid4().hex
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    output_dir = ROOT_DIR + '/tools_output/'+random_filename
    basic_scan = subprocess.run(['nmap','-Pn','-sV','-vvv','--top-ports=1000','-oA',output_dir,url_to_scan],capture_output=True)
    with open(output_dir + '.xml') as xml_file:
        my_dict = xmltodict.parse(xml_file.read())
    xml_file.close()
    json_data = json.dumps(my_dict)
    json_data = json.loads(json_data)
    img_str = image_creator.create_image_from_file(output_dir + '.nmap')
    try:
        mongo.add_nmap_information_to_subdomain(scan_info, json_data['nmaprun']['host']['ports']['port'])
    except KeyError:
        pass
    check_ports_and_report(scan_info,plaintext_ports,'plaintext_services',json_data,img_str)
    check_ports_and_report(scan_info,remote_ports,'unnecessary_services',json_data,img_str)
    cleanup(output_dir)
    return