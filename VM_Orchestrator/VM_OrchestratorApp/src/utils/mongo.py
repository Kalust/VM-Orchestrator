from VM_OrchestratorApp import MONGO_CLIENT
from VM_Orchestrator.settings import MONGO_INFO
from VM_OrchestratorApp.src.utils import slack

from datetime import datetime

resources = MONGO_CLIENT[MONGO_INFO['DATABASE']][MONGO_INFO['RESOURCES_COLLECTION']]
observations = MONGO_CLIENT[MONGO_INFO['DATABASE']][MONGO_INFO['OBSERVATIONS_COLLECTION']]
vulnerabilities = MONGO_CLIENT[MONGO_INFO['DATABASE']][MONGO_INFO['VULNERABILITIES_COLLECTION']]
libraries_versions = MONGO_CLIENT[MONGO_INFO['DATABASE']]['libraries_versions']


def add_vulnerability(vulnerability):
    exists = vulnerabilities.find_one({'domain': vulnerability.target, 'subdomain': vulnerability.scanned_url,
                                          'vulnerability_name': vulnerability.vulnerability_name,
                                          'language': vulnerability.language, 'extra_info': vulnerability.custom_description})
    if exists:
        vulnerabilities.update_one({'_id': exists.get('_id')}, {'$set': {
            'last_seen': vulnerability.time,
            'extra_info': vulnerability.custom_description,
            'image_string': vulnerability.image_string,
            'file_string': vulnerability.file_string
        }})
    else:
        resource = {
            'domain': vulnerability.target,
            'subdomain': vulnerability.scanned_url,
            'vulnerability_name': vulnerability.vulnerability_name,
            'extra_info': vulnerability.custom_description,
            'image_string': vulnerability.image_string,
            'file_string': vulnerability.file_string,
            'date_found': vulnerability.time,
            'last_seen': vulnerability.time,
            'language': vulnerability.language,
            'state': 'open'
        }
        vulnerabilities.insert_one(resource)
    return


# For flagging resources as "scanned"
def add_scanned_resources(urls):
    if urls['type'] == 'domain':
        for url in urls['url_to_scan']:
            resource = resources.find_one({'domain': urls['domain'], 'subdomain': url, 'scanned': False, 'type': urls['type']})
            resources.update_one({'_id': resource.get('_id')},
            {'$set': 
                {
                'scanned': True
                }})
    else:
        resource = resources.find_one({'domain': urls['domain'], 'subdomain': urls['url_to_scan'], 'scanned': False, 'type': urls['type']})
        resources.update_one({'_id': resource.get('_id')},
        {'$set': 
            {
            'scanned': True
            }})

# Removing the scanned flag on all resources
def remove_scanned_flag():
    cursor = resources.find({})
    for document in cursor:
        resources.update_one({'_id': document.get('_id')}, {'$set': {
            'scanned': False
        }})
        print(document)


# This will return every url with http/https
def get_responsive_http_resources(target):
    subdomains = resources.find({'domain': target, 'has_urls': 'True', 'scanned': False})
    subdomain_list = list()
    for subdomain in subdomains:
        for url_with_http in subdomain['responsive_urls'].split(';'):
            if url_with_http:
                current_subdomain = {
                    'domain': subdomain['domain'],
                    'ip': subdomain['ip'],
                    'subdomain': subdomain['subdomain'],
                    'url_with_http': url_with_http
                }
                subdomain_list.append(current_subdomain)
    return subdomain_list

# Searches for vulnerability information in observations collection
def get_observation_for_object(vuln_name,language):
    finding_kb = observations.find_one({'TITLE': vuln_name, 'LANGUAGE': language})
    return finding_kb

def find_last_version_of_librarie(name):
    librarie = libraries_versions.find({'name':name})
    if librarie:
        return librarie[0]['version']
    else:
        return ''

# Returns a list similar to the one generated by the start csv file
def get_data_for_monitor():
    all_data = resources.find({})
    information = list()
    for data in all_data:
        information.append({
            'is_first_run': True,
            'invasive_scans': False,
            'language': 'eng',
            'type': data['type'],
            'priority': data['priority'],
            'exposition': data['exposition'],
            'domain': data['domain']
        })
    information = [dict(t) for t in {tuple(d.items()) for d in information}]

    return information

# ------------------- RECON -------------------
def add_simple_url_resource(scan_info):
    exists = resources.find_one({'domain': scan_info['domain'], 'subdomain': scan_info['url_to_scan']})
    timestamp = datetime.now()
    if not exists:
        resource ={
                'domain': scan_info['domain'].split('/')[2],
                'subdomain': scan_info['domain'],
                'is_alive': True,
                'ip': None,
                'additional_info':{
                    'isp': None,
                    'asn': None,
                    'country': None,
                    'region': None,
                    'city': None,
                    'org': None,
                    'lat': None,
                    'lon': None,
                },
                'first_seen': timestamp,
                'last_seen': timestamp,
                'scanned': False,
                'type': scan_info['type'],
                'priority': scan_info['priority'],
                'exposition': scan_info['exposition']
        }
        resources.insert_one(resource)
    else:
        resources.update_one({'_id': exists.get('_id')},
         {'$set': 
            {
            'last_seen': timestamp
            }})

def add_simple_ip_resource(scan_info):
    exists = resources.find_one({'domain': scan_info['domain'], 'subdomain': scan_info['url_to_scan']})
    timestamp = datetime.now()
    if not exists:
        resource ={
                'domain': scan_info['domain'],
                'subdomain': scan_info['domain'],
                'is_alive': True,
                'ip': scan_info['domain'],
                'additional_info':{
                    'isp': None,
                    'asn': None,
                    'country': None,
                    'region': None,
                    'city': None,
                    'org': None,
                    'lat': None,
                    'lon': None,
                },
                'first_seen': timestamp,
                'last_seen': timestamp,
                'scanned': False,
                'type': scan_info['type'],
                'priority': scan_info['priority'],
                'exposition': scan_info['exposition']
        }
        resources.insert_one(resource)
    else:
        resources.update_one({'_id': exists.get('_id')},
         {'$set': 
            {
            'last_seen': timestamp
            }})


def add_resource(url_info, scan_info):
    exists = resources.find_one({'domain': url_info['domain'], 'subdomain': url_info['url']})
    timestamp = datetime.now()
    if not exists:
        resource ={
                'domain': url_info['domain'],
                'subdomain': url_info['url'],
                'is_alive': url_info['is_alive'],
                'ip': url_info['ip'],
                'additional_info':{
                    'isp': url_info['isp'],
                    'asn': url_info['asn'],
                    'country': url_info['country'],
                    'region': url_info['region'],
                    'city': url_info['city'],
                    'org': url_info['org'],
                    'lat': url_info['lat'],
                    'lon': url_info['lon'],
                },
                'first_seen': timestamp,
                'last_seen': timestamp,
                'scanned': False,
                'type': scan_info['type'],
                'priority': scan_info['priority'],
                'exposition': scan_info['exposition']
        }
        if not scan_info['is_first_run']:
            slack.send_new_resource_found("New resource found! %s" % url_info['url'])
            print('New resource found!!\n')
            print(str(resource))
        resources.insert_one(resource)
    else:
        resources.update_one({'_id': exists.get('_id')},
         {'$set': 
            {
            'is_alive': url_info['is_alive'],
            'ip': url_info['ip'],
            'additional_info':{
                    'isp': url_info['isp'],
                    'asn': url_info['asn'],
                    'country': url_info['country'],
                    'region': url_info['region'],
                    'city': url_info['city'],
                    'org': url_info['org'],
                    'lat': url_info['lat'],
                    'lon': url_info['lon'],
                },
            'last_seen': timestamp
            }})
    return


def get_alive_subdomains_from_target(target):
    subdomains = resources.find({'domain': target, 'is_alive': 'True', 'scanned': False})
    subdomain_list = list()
    for subdomain in subdomains:
        current_subdomain = {
            'domain': subdomain['domain'],
            'subdomain': subdomain['subdomain']
        }
        subdomain_list.append(current_subdomain)
    return subdomain_list

def add_urls_to_subdomain(subdomain, has_urls, url_list):
    subdomain = resources.find_one({'subdomain': subdomain})
    resources.update_one({'_id': subdomain.get('_id')}, {'$set': {
        'has_urls': str(has_urls),
        'responsive_urls': url_list}})

    return


def add_images_to_subdomain(subdomain, http_image, https_image):
    subdomain = resources.find_one({'subdomain': subdomain})
    resources.update_one({'_id': subdomain.get('_id')}, {'$set': {
        'http_image': http_image,
        'https_image': https_image}})
    return