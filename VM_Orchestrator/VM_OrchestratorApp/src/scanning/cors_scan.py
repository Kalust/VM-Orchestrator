# pylint: disable=import-error
from VM_OrchestratorApp.src.utils import slack, utils, mongo, redmine
from VM_OrchestratorApp.src import constants
from VM_OrchestratorApp.src.objects.vulnerability import Vulnerability

import os
import subprocess
import json
import uuid
import copy
from datetime import datetime

MODULE_NAME = 'CORS module'

MODULE_IDENTIFIER = 'cors_module'
SLACK_NOTIFICATION_CHANNEL = '#vm-cors'

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
    print('Module CORS Scan starting against %s alive urls from %s' % (str(len(info['target'])), info['domain']))
    slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'start')

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    # We first put all the urls with http/s into a txt file
    random_filename = uuid.uuid4().hex
    FILE_WITH_URLS = ROOT_DIR + '/tools_output/' + random_filename + '.txt'
    for subdomain in info['target']:
        scan_info = copy.deepcopy(info)
        scan_info['target'] = subdomain
        with open(FILE_WITH_URLS, 'w') as f:
            f.write("%s\n" % subdomain)
        # Call scan target with the file
        scan_target(scan_info, FILE_WITH_URLS)
        # Delete all created files
        cleanup(FILE_WITH_URLS)

    print('Module CORS Scan finished against %s' % info['domain'])
    slack.send_module_end_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'end')
    return


def handle_single(info):
    info = copy.deepcopy(info)
    print('Module CORS Scan starting against %s' % info['target'])
    slack.send_module_start_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'start')

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Put urls in a single file
    random_filename = uuid.uuid4().hex
    FILE_WITH_URL = ROOT_DIR + '/tools_output/' + random_filename + '.txt'
    cleanup(FILE_WITH_URL)
    with open(FILE_WITH_URL, 'w') as f:
        f.write("%s\n" % info['target'])

    # Call scan target
    scan_target(info, FILE_WITH_URL)

    # Delete all created files
    cleanup(FILE_WITH_URL)

    print('Module CORS Scan finished against %s' % info['target'])
    slack.send_module_end_notification_to_channel(info, MODULE_NAME, SLACK_NOTIFICATION_CHANNEL)
    send_module_status_log(info, 'end')
    return


def add_vulnerability(scan_info, vuln):
    specific_info = copy.deepcopy(scan_info)
    vulnerability = Vulnerability(constants.CORS, specific_info, 'Found CORS %s with origin %s' % (vuln['type'], vuln['origin']))
    slack.send_vuln_to_channel(vulnerability, SLACK_NOTIFICATION_CHANNEL)
    vulnerability.id = mongo.add_vulnerability(vulnerability)
    redmine.create_new_issue(vulnerability)


def scan_target(scan_info, file_name):

    # Call the tool with the previous file
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    random_filename = uuid.uuid4().hex
    FILE_WITH_JSON_RESULT = ROOT_DIR + '/tools_output/' + random_filename + '.json'
    TOOL_DIR = ROOT_DIR + '/tools/CORScanner/cors_scan.py'
    cleanup(FILE_WITH_JSON_RESULT)
    subprocess.run(
        ['python3', TOOL_DIR, '-i', file_name, '-o', FILE_WITH_JSON_RESULT], capture_output=True)
    with open(FILE_WITH_JSON_RESULT) as json_file:
        vulns = json.load(json_file)

    if not vulns:
        cleanup(FILE_WITH_JSON_RESULT)
        return

    for vuln in vulns:
        add_vulnerability(scan_info, vuln)

    cleanup(FILE_WITH_JSON_RESULT)
    return
