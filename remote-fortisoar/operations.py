"""
Copyright start
MIT License
Copyright (c) 2024 Fortinet Inc
Copyright end
"""

from connectors.core.connector import get_logger, ConnectorError
import json
import time
import logging
from .utils import invoke_rest_endpoint, upload_file_remote
from .constants import LOGGER_NAME
import os
from django.conf import settings
from connectors.cyops_utilities.builtins import download_file_from_cyops

logger = get_logger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)


def make_api_call(config, params, *args, **kwargs):
    endpoint = params.get('iri')
    method = params.get('method')
    headers = params.get('headers', None)
    body = params.get('body', None)
    param = params.get('params', None)
    if not endpoint or not method:
        logger.warning('Got an endpoint: {endpoint}\Body: {body}'.format(endpoint=endpoint, body=json.dumps(body)))
        raise ConnectorError('Missing required input')

    api_response = invoke_rest_endpoint(config, endpoint, method, headers, body, param)
    return api_response

def upload_file(config, params, *args, **kwargs):
    file_iri = params.get('file_iri')
    create_attachment = params.get('create_attachment')
    if not file_iri:
        logger.warning('Got file_iri: {file_iri}'.format(endpoint=file_iri))
        raise ConnectorError('Missing required input')
    dw_file_md = download_file_from_cyops(file_iri)
    tmp_file_path = dw_file_md.get('cyops_file_path')
    file_name = dw_file_md.get('filename')
    logger.info('file_name = {0}'.format(file_name))
    file_path = os.path.join(settings.TMP_FILE_ROOT, tmp_file_path)
    api_response = upload_file_remote(config, open(file_path, 'rb'), dw_file_md, create_attachment)
    return api_response


def invoke_agent(config, params, *args, **kwargs):
    poll_interval = 10
    max_attempts = 20 # default wait time will be ~3min
    agent_name = params.get('agent_name')
    body = params.get('body')
    if not isinstance(body, dict):
        raise ConnectorError('Agent payload must be a JSON object')

    trigger_endpoint = '/ai/agents/{0}/trigger'.format(agent_name)
    trigger_response = invoke_rest_endpoint(config, trigger_endpoint, 'POST', body=body)
    task_id = trigger_response.get('task_id')
    if not task_id:
        logger.warning('Agent trigger response did not contain a task_id: {0}'.format(trigger_response))
        raise ConnectorError('Agent trigger response did not contain a task_id')

    status = None
    for attempt in range(max_attempts):
        status_response = invoke_rest_endpoint(config, '/ai/agents/{0}/status'.format(task_id), 'GET')
        status = status_response.get('status', None)
        if status == 'completed':
            break
        if status in ['failed', 'error', None]:
            raise ConnectorError('Agent execution failed with status: {0}'.format(status))
        time.sleep(poll_interval)
    else:
        raise ConnectorError('Timed out waiting for agent completion')

    return invoke_rest_endpoint(config, '/ai/agents/{0}/result'.format(task_id), 'GET')