# pylint: disable=import-error
from VM_Orchestrator.settings import settings, redmine_client
from VM_Orchestrator.settings import REDMINE_IDS
from VM_OrchestratorApp.src.objects.vulnerability import Vulnerability

import urllib3
from datetime import datetime
from contextlib import suppress

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_id_for_custom_issue(issue_id, identifier_custom_id, new_id):
    redmine_client.issue.update(issue_id, custom_fields=[
        {'id': identifier_custom_id, 'value': new_id}
    ])

def get_issues_from_project():
    if redmine_client is None:
        return []
    return redmine_client.issue.filter(project_id=settings['REDMINE']['project_name'], status_id='*')

def issue_already_exists(vuln):
    timestamp = datetime.now()
    issues = redmine_client.issue.filter(project_id=settings['REDMINE']['project_name'], status_id='*')
    if isinstance(vuln, Vulnerability):
        id_to_use = vuln.id
    else:
        id_to_use = vuln['_id']

    for issue in issues:
        #Web case
        if issue.tracker.id == REDMINE_IDS['WEB_FINDING']['FINDING_TRACKER']:
            if(id_to_use == issue.custom_fields.get(REDMINE_IDS['WEB_FINDING']['IDENTIFIER']).value):
                # This means the issue already exists in redmine. We will update the description and last seen
                # If the status of the issue is set as resolved, we will also send an alert and change the status
                if issue.status.id == REDMINE_IDS['STATUS_SOLVED']:
                    redmine_client.issue.update(issue.id, description=vuln.custom_description,status_id=REDMINE_IDS['STATUS_REOPENED'],
                    custom_fields=[
                    {'id': REDMINE_IDS['WEB_FINDING']['DOMAIN'], 'value': vuln.domain},
                    {'id': REDMINE_IDS['WEB_FINDING']['RESOURCE'], 'value': vuln.target},
                    {'id': REDMINE_IDS['WEB_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))}
                    ])
                    return True
                # Delete attachments so we can add new ones
                with suppress(Exception):
                    for attachment in issue.attachments:
                        redmine_client.attachment.delete(attachment.id)
                redmine_client.issue.update(issue.id, description=vuln.custom_description,
                uploads=vuln.attachments,
                custom_fields=[
                {'id': REDMINE_IDS['WEB_FINDING']['DOMAIN'], 'value': vuln.domain},
                {'id': REDMINE_IDS['WEB_FINDING']['RESOURCE'], 'value': vuln.target},
                {'id': REDMINE_IDS['WEB_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))}
                ])
                return True
        #Infra case
        elif issue.tracker.id == REDMINE_IDS['INFRA_FINDING']['FINDING_TRACKER']:
            if(id_to_use == issue.custom_fields.get(REDMINE_IDS['INFRA_FINDING']['IDENTIFIER']).value):
                if issue.status.id == REDMINE_IDS['STATUS_SOLVED']:
                    redmine_client.issue.update(issue.id, description=vuln.custom_description,status_id=REDMINE_IDS['STATUS_NEW'],
                    custom_fields=[
                    {'id': REDMINE_IDS['INFRA_FINDING']['DOMAIN'], 'value': vuln.domain},
                    {'id': REDMINE_IDS['INFRA_FINDING']['RESOURCE'], 'value': vuln.target},
                    {'id': REDMINE_IDS['INFRA_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))}
                    ])
                    return True
                with suppress(Exception):
                    for attachment in issue.attachments:
                        redmine_client.attachment.delete(attachment.id)
                redmine_client.issue.update(issue.id, description=vuln.custom_description,
                uploads=vuln.attachments,
                custom_fields=[
                {'id': REDMINE_IDS['INFRA_FINDING']['DOMAIN'], 'value': vuln.domain},
                {'id': REDMINE_IDS['INFRA_FINDING']['RESOURCE'], 'value': vuln.target},
                {'id': REDMINE_IDS['INFRA_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))}
                ])
                return True
        #Code case
        elif issue.tracker.id == REDMINE_IDS['CODE_FINDING']['FINDING_TRACKER']:
            if(id_to_use == issue.custom_fields.get(REDMINE_IDS['CODE_FINDING']['IDENTIFIER']).value):
                if issue.status.id == REDMINE_IDS['STATUS_REJECTED']:
                    redmine_client.issue.update(issue.id, description=vuln['Description'],status_id=REDMINE_IDS['STATUS_NEW_VERIFY'],
                    custom_fields=[
                    {'id': REDMINE_IDS['CODE_FINDING']["LINE"], 'value': vuln['Line']},
                    {'id': REDMINE_IDS['CODE_FINDING']["LAST_COMMIT"], 'value': vuln['Commit']},
                    {'id': REDMINE_IDS['CODE_FINDING']['LAST_SEEN'], 'value': str(timestamp.strftime("%Y-%m-%d"))}
                    ])
                    return True
                redmine_client.issue.update(issue.id, description=vuln['Description'],
                custom_fields=[
                {'id': REDMINE_IDS['CODE_FINDING']["LINE"], 'value': vuln['Line']},
                {'id': REDMINE_IDS['CODE_FINDING']["LAST_COMMIT"], 'value': vuln['Commit']},
                {'id': REDMINE_IDS['CODE_FINDING']['LAST_SEEN'], 'value': str(timestamp.strftime("%Y-%m-%d"))}
                ])
                return True
    return False

def create_new_issue(vuln):
    if vuln.vuln_type == 'web':
        create_new_web_issue(vuln)
    elif vuln.vuln_type == 'ip':
        create_new_infra_issue(vuln)

def create_new_web_issue(vuln):
    if redmine_client is None:
        return
    if issue_already_exists(vuln):
        return
    issue = redmine_client.issue.new()
    issue.project_id = settings['REDMINE']['project_name']
    issue.subject = vuln.vulnerability_name
    issue.tracker_id = REDMINE_IDS['WEB_FINDING']['FINDING_TRACKER']
    issue.description = vuln.custom_description
    issue.status_id = vuln.status
    issue.priority_id = vuln.resolve_priority()
    issue.assigned_to_id = REDMINE_IDS['ASSIGNED_USER']
    issue.watcher_user_ids = REDMINE_IDS['WATCHERS']
    issue.custom_fields= [
    {'id': REDMINE_IDS['WEB_FINDING']['IDENTIFIER'], 'value': vuln.id},
    {'id': REDMINE_IDS['WEB_FINDING']['DOMAIN'], 'value': vuln.domain},
    {'id': REDMINE_IDS['WEB_FINDING']['RESOURCE'], 'value': vuln.target},
    {'id': REDMINE_IDS['WEB_FINDING']['DATE_FOUND'], 'value': str(vuln.time.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['WEB_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['WEB_FINDING']['CVSS_SCORE'], 'value': vuln.cvss},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_DESCRIPTION'], 'value': str(vuln.observation.observation_title)},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_DESCRIPTION_NOTES'], 'value': str(vuln.observation.observation_note)},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_IMPLICATION'], 'value': str(vuln.observation.implication)},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_RECOMMENDATION'], 'value': str(vuln.observation.recommendation_title)},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_RECOMMENDATION_NOTES'], 'value': str(vuln.observation.recommendation_urls)}
    ]
    issue.uploads = vuln.attachments
    try:
        issue.save()
    except Exception as e:
        print("Redmine error" + str(e))

def create_new_infra_issue(vuln):
    if redmine_client is None:
        return
    if issue_already_exists(vuln):
        return
    issue = redmine_client.issue.new()
    issue.project_id = settings['REDMINE']['project_name']
    issue.subject = vuln.vulnerability_name
    issue.tracker_id = REDMINE_IDS['INFRA_FINDING']['FINDING_TRACKER']
    issue.description = vuln.custom_description
    issue.status_id = vuln.status
    issue.priority_id = vuln.resolve_priority()
    issue.assigned_to_id = REDMINE_IDS['ASSIGNED_USER']
    issue.watcher_user_ids = REDMINE_IDS['WATCHERS']
    issue.custom_fields= [
    {'id': REDMINE_IDS['INFRA_FINDING']['IDENTIFIER'], 'value': vuln.id},
    {'id': REDMINE_IDS['INFRA_FINDING']['DOMAIN'], 'value': vuln.domain},
    {'id': REDMINE_IDS['INFRA_FINDING']['RESOURCE'], 'value': vuln.target},
    {'id': REDMINE_IDS['INFRA_FINDING']['DATE_FOUND'], 'value': str(vuln.time.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['INFRA_FINDING']['LAST_SEEN'], 'value': str(vuln.time.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['INFRA_FINDING']['CVSS_SCORE'], 'value': vuln.cvss},
    {'id': REDMINE_IDS['INFRA_FINDING']['KB_DESCRIPTION'], 'value': str(vuln.observation.observation_title)},
    {'id': REDMINE_IDS['INFRA_FINDING']['KB_DESCRIPTION_NOTES'], 'value': str(vuln.observation.observation_note)},
    {'id': REDMINE_IDS['INFRA_FINDING']['KB_IMPLICATION'], 'value': str(vuln.observation.implication)},
    {'id': REDMINE_IDS['INFRA_FINDING']['KB_RECOMMENDATION'], 'value': str(vuln.observation.recommendation_title)},
    {'id': REDMINE_IDS['INFRA_FINDING']['KB_RECOMMENDATION_NOTES'], 'value': str(vuln.observation.recommendation_urls)}
    ]
    issue.uploads = vuln.attachments
    try:
        issue.save()
    except Exception as e:
        print("Redmine error" + str(e))

def create_new_code_issue(vuln):
    if redmine_client is None:
        return
    if issue_already_exists(vuln):
        return
    priority_dict = {'INFORMATIONAL': REDMINE_IDS['SEVERITY']['INFORMATIONAL'],
         'LOW': REDMINE_IDS['SEVERITY']['LOW'], 'MEDIUM': REDMINE_IDS['SEVERITY']['MEDIUM'],
          'HIGH': REDMINE_IDS['SEVERITY']['HIGH'], 'CRITICAL': REDMINE_IDS['SEVERITY']['CRITICAL']}
    priority_id = priority_dict[vuln['observation']['severity'].upper()]
    timestamp = datetime.now()
    issue = redmine_client.issue.new()
    issue.project_id = settings['REDMINE']['project_name']
    issue.subject = vuln['Title']
    issue.tracker_id = REDMINE_IDS['CODE_FINDING']['FINDING_TRACKER']
    issue.description = vuln['Description']
    issue.status_id = REDMINE_IDS['STATUS_NEW']
    issue.priority_id = priority_id
    issue.assigned_to_id = REDMINE_IDS['ASSIGNED_USER']
    issue.watcher_user_ids = REDMINE_IDS['WATCHERS']
    issue.custom_fields= [
    {'id': REDMINE_IDS['CODE_FINDING']['IDENTIFIER'], 'value': vuln['_id']},
    {'id': REDMINE_IDS['CODE_FINDING']["COMPONENT"], 'value': vuln['Component']},
    {'id': REDMINE_IDS['CODE_FINDING']["LINE"], 'value': vuln['Line']},
    {'id': REDMINE_IDS['CODE_FINDING']["AFFECTED_CODE"], 'value': vuln['Affected_code']},
    {'id': REDMINE_IDS['CODE_FINDING']["FIRST_COMMIT"], 'value': vuln['Commit']},
    {'id': REDMINE_IDS['CODE_FINDING']["LAST_COMMIT"], 'value': vuln['Commit']},
    {'id': REDMINE_IDS['CODE_FINDING']["USERNAME"], 'value': vuln['Username']},
    {'id': REDMINE_IDS['CODE_FINDING']["PIPELINE_NAME"], 'value': vuln['Pipeline_name']},
    {'id': REDMINE_IDS['CODE_FINDING']["BRANCH_NAME"], 'value': vuln['Branch']},
    {'id': REDMINE_IDS['CODE_FINDING']["TOOL_SEVERITY"], 'value':vuln['Severity_tool']},
    {'id': REDMINE_IDS['CODE_FINDING']['DATE_FOUND'], 'value': str(timestamp.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['CODE_FINDING']['LAST_SEEN'], 'value': str(timestamp.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['CODE_FINDING']['CVSS_SCORE'], 'value': vuln['cvss_score']},
    {'id': REDMINE_IDS['CODE_FINDING']['KB_DESCRIPTION'], 'value': vuln['observation']['observation_title']},
    {'id': REDMINE_IDS['CODE_FINDING']['KB_DESCRIPTION_NOTES'], 'value': vuln['observation']['observation_note']},
    {'id': REDMINE_IDS['CODE_FINDING']['KB_IMPLICATION'], 'value': vuln['observation']['implication']},
    {'id': REDMINE_IDS['CODE_FINDING']['KB_RECOMMENDATION'], 'value': vuln['observation']['recommendation_title']},
    {'id': REDMINE_IDS['CODE_FINDING']['KB_RECOMMENDATION_NOTES'], 'value': vuln['observation']['recommendation_note']}
    ]
    try:
        issue.save()
    except Exception as e:
        print("Redmine error" + str(e))

def create_new_web_issue_bis(vuln):
    if redmine_client is None:
        return
    priority_dict = {'INFORMATIONAL': REDMINE_IDS['SEVERITY']['INFORMATIONAL'],
         'LOW': REDMINE_IDS['SEVERITY']['LOW'], 'MEDIUM': REDMINE_IDS['SEVERITY']['MEDIUM'],
          'HIGH': REDMINE_IDS['SEVERITY']['HIGH'], 'CRITICAL': REDMINE_IDS['SEVERITY']['CRITICAL']}
    priority_id = priority_dict[vuln['observation']['severity'].upper()]
    issue = redmine_client.issue.new()
    issue.project_id = settings['REDMINE']['project_name']
    issue.subject = vuln['Title']
    issue.tracker_id = REDMINE_IDS['WEB_FINDING']['FINDING_TRACKER']
    issue.description = vuln['Description']
    issue.status_id = REDMINE_IDS['STATUS_NEW']
    issue.priority_id = priority_id
    issue.assigned_to_id = REDMINE_IDS['ASSIGNED_USER']
    issue.watcher_user_ids = REDMINE_IDS['WATCHERS']
    timestamp = datetime.now()
    issue.custom_fields= [
    {'id': REDMINE_IDS['WEB_FINDING']['IDENTIFIER'], 'value': vuln['_id']},
    {'id': REDMINE_IDS['WEB_FINDING']['DOMAIN'], 'value': vuln['Domain']},
    {'id': REDMINE_IDS['WEB_FINDING']['RESOURCE'], 'value': vuln['Resource']},
    {'id': REDMINE_IDS['WEB_FINDING']['DATE_FOUND'], 'value': str(timestamp.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['WEB_FINDING']['LAST_SEEN'], 'value': str(timestamp.strftime("%Y-%m-%d"))},
    {'id': REDMINE_IDS['WEB_FINDING']['CVSS_SCORE'], 'value': vuln['cvss_score']},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_DESCRIPTION'], 'value': str(vuln['observation']['observation_title'])},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_DESCRIPTION_NOTES'], 'value': str(vuln['observation']['observation_note'])},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_IMPLICATION'], 'value': str(vuln['observation']['implication'])},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_RECOMMENDATION'], 'value': str(vuln['observation']['recommendation_title'])},
    {'id': REDMINE_IDS['WEB_FINDING']['KB_RECOMMENDATION_NOTES'], 'value': str(vuln['observation']['recommendation_note'])}
    ]
    try:
        issue.save()
    except Exception as e:
        print("Redmine error" + str(e))
    return

def update_code_issues_by_state(data):
    if redmine_client is None:
        return
    if data['Status'] != 'End':
        return
    issues = redmine_client.issue.filter(project_id=settings['REDMINE']['project_name'], status_id='*')
    for issue in issues:
        if issue.tracker.id == REDMINE_IDS['CODE_FINDING']['FINDING_TRACKER']:
            # We dont check ID, we have to update all
            # We receive and "End" commit, every issue that does not have that commit will get updated
            if (issue.custom_fields.get(REDMINE_IDS['CODE_FINDING']['PIPELINE_NAME']).value == data['Pipeline_name'] and
                issue.custom_fields.get(REDMINE_IDS['CODE_FINDING']['BRANCH_NAME']).value == data['Branch'] and
                issue.custom_fields.get(REDMINE_IDS['CODE_FINDING']['LAST_COMMIT']).value != data['Commit']):
                if issue.status.id == REDMINE_IDS['STATUS_CONFIRMED'] or issue.status.id == REDMINE_IDS['STATUS_NEW']:
                    redmine_client.issue.update(issue.id,status_id=REDMINE_IDS['STATUS_NEW_VERIFY'])
    return