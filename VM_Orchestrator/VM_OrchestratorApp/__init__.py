# pylint: disable=import-error
from VM_Orchestrator.settings import MONGO_INFO, settings

import pymongo
from slack import WebClient
from elasticsearch import Elasticsearch
from ssl import create_default_context

ELASTIC_CLIENT = None
if settings['ELASTIC']['IP'] != '':
    if settings['ELASTIC']['USER'] == '':
        ELASTIC_CLIENT = Elasticsearch([{'host':settings['ELASTIC']['IP'],'port':settings['ELASTIC']['PORT']}])
    else:
        pathCertificate = settings['ELASTIC']["ELASTICCERTIFICATE"]
        host = "{}:{}".format(settings['ELASTIC']['IP'],settings['ELASTIC']['PORT'])
        ELASTIC_CLIENT = Elasticsearch([host], use_ssl=True, ssl_assert_hostname=False,
                        verify_certs=True, ca_certs=pathCertificate, http_auth=(settings['ELASTIC']['USER'], settings['ELASTIC']['SECRET']))
MONGO_CLIENT = pymongo.MongoClient(MONGO_INFO['CLIENT_URL'], connect=False)
if settings['SLACK']['INTERNAL_SLACK_KEY'] != '':
    INTERNAL_SLACK_WEB_CLIENT = WebClient(settings['SLACK']['INTERNAL_SLACK_KEY'])
else:
    INTERNAL_SLACK_WEB_CLIENT = None