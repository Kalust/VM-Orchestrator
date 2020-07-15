from VM_Orchestrator.settings import settings
from VM_OrchestratorApp import INTERNAL_SLACK_WEB_CLIENT, EXTERNAL_SLACK_WEB_CLIENT


### NEW Notification area ###
def send_message_to_channel(message, channel):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=channel, text=message)
        except Exception as e:
            print("Slack error" + str(e))
            
def send_module_start_notification_to_channel(scan_info, module_name, channel):
    if scan_info['scan_type'] == 'target':
        message = "%s started against target: %s. %d alive resources found" \
        % (module_name, scan_info['domain'], len(scan_info['url_to_scan']))
    else:
        message = "%s started against %s" % (module_name, scan_info['domain'])

    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=channel, text=message)
        except Exception as e:
            print("Slack error" + str(e))

def send_module_end_notification_to_channel(scan_info, module_name, channel):
    if scan_info['scan_type'] == 'target':
        message = "%s finished against target: %s. %d alive resources were found" \
        % (module_name, scan_info['domain'], len(scan_info['url_to_scan']))
    else:
        message = "%s finished against %s" % (module_name, scan_info['domain'])

    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=channel, text=message)
        except Exception as e:
            print("Slack error" + str(e))

def send_error_to_channel(message, channel):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=channel, text=message)
        except Exception as e:
            print("Slack error" + str(e))

def send_vuln_to_channel(vulnerability, channel):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            message = 'Found vulnerability \" %s \" at %s from resource %s. \n %s' % \
            (vulnerability.vulnerability_name, vulnerability.scanned_url, vulnerability.target, vulnerability.custom_description)
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=channel, text=message)
        except Exception as e:
            print("Slack error" + str(e))
### END ###



def send_simple_message(message):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text=str(message))
        except Exception as e:
            print("Slack error" + str(e))

def send_vulnerability(vulnerability):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        message = 'Found vulnerability \" %s \" at %s from resource %s. \n %s' % \
         (vulnerability.vulnerability_name, vulnerability.scanned_url, vulnerability.target, vulnerability.custom_description)
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text=str(message))
        except Exception as e:
            print("Slack error" + str(e))

def send_new_resource_found(msg):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text=str(msg))
        except Exception as e:
            print("Slack error" + str(e))
    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text=str(msg))
        except Exception as e:
            print("Slack error" + str(e))

# Information will contain something along the lines of {'resource': domain_name, 'type': 'domain'}
# Can also be something like {'resource': '127.0.0.1', 'type': 'ip'}
def send_recon_start_notification(information):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text="Recon started against %s!" % information['domain'])
        except Exception as e:
            print("Slack error" + str(e))

    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text="Recon started against %s!" % information['domain'])
        except Exception as e:
            print("Slack error" + str(e))

# The idea here is to send something the client can verify
def send_recon_end_notification():
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text="Recon ended!")
        except Exception as e:
            print("Slack error" + str(e))
    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text="Recon ended!")
        except Exception as e:
            print("Slack error" + str(e))

def send_monitor_recon_start_notification():
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text='Monitor recon started!')
        except Exception as e:
            print("Slack error" + str(e))

def send_monitor_scan_start_notification():
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text='Monitor scan started')
        except Exception as e:
            print("Slack error" + str(e))

def send_project_start_recon_start_notification():
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text='Project started, executing recon...')
        except Exception as e:
            print("Slack error" + str(e))

    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text='Project started, executing recon...')
        except Exception as e:
            print("Slack error" + str(e))
    
def send_project_start_scan_start_notification():
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text='Starting vuln scan against found resources')
        except Exception as e:
            print("Slack error" + str(e))

    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text='Starting vuln scan against found resources')
        except Exception as e:
            print("Slack error" + str(e))

def send_log_message(msg):
    if INTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            INTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['INTERNAL_SLACK_CHANNEL'], text=str(msg))
        except Exception as e:
            print("Slack error" + str(e))

    if EXTERNAL_SLACK_WEB_CLIENT is not None:
        try:
            EXTERNAL_SLACK_WEB_CLIENT.chat_postMessage(channel=settings['SLACK']['EXTERNAL_SLACK_CHANNEL'], text=str(msg))
        except Exception as e:
            print("Slack error" + str(e))