# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import requests

from requests.exceptions import ConnectTimeout, ProxyError, SSLError
from flask import Blueprint, render_template, request, redirect, session, url_for
from . import proxy_utils

SAVE_SUCCESS_MESSAGE = 'Saved Successfully!'
SAVE_FAILURE_MESSAGE = 'Save Failed!'

PROXY_ERROR_MESSAGE = 'A proxy error occurred!'
SSL_ERROR_MESSAGE = 'An SSL error occurred!'
TIMEOUT_ERROR_MESSAGE = 'Timed out trying to connect to proxy!'

SESSION_SAVE_STATUS = 'save_status'

PROXY_HTML_TEMPLATE = 'proxy.html'
REQUEST_TIMEOUT_IN_SECS = 2

# pylint: disable=invalid-name
viewsbp = Blueprint('viewsbp', __name__, url_prefix='/')


@viewsbp.route('/')
@viewsbp.route('/get_proxy_settings')
def get_proxy_settings():
    save_status = get_save_status_from_session()
    proxy_settings = proxy_utils.get_proxy_settings_from_json()
    url = request.args.get('address')
    if url:
        return perform_url_request(url, proxy_settings, save_status)
    return render_template(PROXY_HTML_TEMPLATE, proxy_settings=proxy_settings, save_status=save_status)


@viewsbp.route('/save_proxy_settings', methods=['POST'])
def save_proxy_settings():
    proxy_settings = proxy_utils.get_proxy_settings_from_form()
    if proxy_utils.write_proxy_settings_to_json(proxy_settings):
        proxy_utils.set_proxy_env_variables(proxy_settings)
        session[SESSION_SAVE_STATUS] = SAVE_SUCCESS_MESSAGE
    else:
        session[SESSION_SAVE_STATUS] = SAVE_FAILURE_MESSAGE
    return redirect(url_for('viewsbp.get_proxy_settings'), code=303)


def get_save_status_from_session():
    save_status = None
    if SESSION_SAVE_STATUS in session:
        save_status = session[SESSION_SAVE_STATUS]
    session.pop(SESSION_SAVE_STATUS, None)
    return save_status


def process_url_response(proxy_settings, save_status, url, result, status_code):
    return render_template(PROXY_HTML_TEMPLATE,
                           proxy_settings=proxy_settings,
                           save_status=save_status,
                           url=url,
                           result=result,
                           status_code=status_code)


def perform_url_request(url, proxy_settings, save_status):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_IN_SECS)
    except ProxyError as proxy_error:
        return process_url_response(proxy_settings, save_status, url, PROXY_ERROR_MESSAGE, str(proxy_error))
    except SSLError as ssl_error:
        return process_url_response(proxy_settings, save_status, url, SSL_ERROR_MESSAGE, str(ssl_error))
    except ConnectTimeout as timeout_error:
        return process_url_response(proxy_settings, save_status, url, TIMEOUT_ERROR_MESSAGE, str(timeout_error))
    return process_url_response(proxy_settings, save_status, url, response.text, response.status_code)
