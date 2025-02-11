# pylint: disable=import-error
from VM_OrchestratorApp.src.utils import slack, utils, mongo, redmine
from VM_OrchestratorApp.src import constants
from VM_OrchestratorApp.src.objects.vulnerability import Vulnerability
from VM_Orchestrator.settings import settings,FFUF_LIST

import subprocess
import os
import json
import uuid
import copy
from datetime import datetime

MODULE_NAME = 'FFUF module'
MODULE_IDENTIFIER = 'ffuf_module'
SLACK_NOTIFICATION_CHANNEL = '#vm-ffuf'

def cleanup(path):
    try:
        os.remove(path)
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
    if FFUF_LIST:
        print('Module ffuf starting against %s alive urls from %s' % (str(len(info['target'])), info['domain']))
        slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
        send_module_status_log(info, 'start')

        for url in info['target']:
            sub_info = copy.deepcopy(info)
            sub_info['target'] = url
            scan_target(sub_info, sub_info['target'])

        print('Module ffuf finished against domain %s' % info['domain'])
        slack.send_module_end_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
        send_module_status_log(info, 'end')

    return


def handle_single(info):
    info = copy.deepcopy(info)
    if FFUF_LIST:
        print('Module ffuf starting against %s' % info['target'])
        slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
        send_module_status_log(info, 'start')

        scan_target(info, info['target'])
        slack.send_module_end_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
        send_module_status_log(info, 'end')
        print('Module ffuf finished against %s' % info['target'])
    return


def add_vulnerability(scan_info, affected_resource, description):
    vulnerability = Vulnerability(constants.ENDPOINT, scan_info, description)

    slack.send_vuln_to_channel(vulnerability, SLACK_NOTIFICATION_CHANNEL)
    vulnerability.id = mongo.add_vulnerability(vulnerability)
    redmine.create_new_issue(vulnerability)


def scan_target(scan_info, url_with_http):
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    TOOL_DIR = ROOT_DIR + '/tools/ffuf'
    WORDLIST_DIR = ROOT_DIR + '/tools/ffuf_wordlist.txt'
    random_filename = uuid.uuid4().hex
    JSON_RESULT = ROOT_DIR + '/tools_output/' + random_filename + '.json'
    cleanup(JSON_RESULT)

    if url_with_http[-1] != '/':
        url_with_http = url_with_http + '/'

    subprocess.run(
        [TOOL_DIR, '-w', WORDLIST_DIR, '-u', url_with_http + 'FUZZ', '-maxtime', '300', '-timeout', '3', '-c', '-v', '-ac','-mc', '200,403',
         '-o', JSON_RESULT], capture_output=True)

    with open(JSON_RESULT) as json_file:
        json_data = json.load(json_file)

    count = 0
    with open(WORDLIST_DIR, 'r') as f:
        for line in f:
            count += 1

    vulns = json_data['results']

    #If more than half of the endpoints are found, the result is discarded
    if len(vulns) > count/2:
        return

    valid_codes = [200, 403]
    one_found = False
    extra_info_message = ""
    for vuln in vulns:
        if vuln['status'] in valid_codes:
            extra_info_message = extra_info_message + "%s\n"% vuln['input']['FUZZ']
            one_found = True

    if one_found:
        description = "The following endpoints were found:\n %s" % (extra_info_message)
        add_vulnerability(scan_info, url_with_http, description)

    cleanup(JSON_RESULT)
    return
