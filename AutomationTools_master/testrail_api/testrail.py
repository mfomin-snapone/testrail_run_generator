#
# TestRail API binding for Python 2.x (API v2, available since
# TestRail 3.0)
# Compatible with TestRail 3.0 and later.
#
# Learn more:
#
# http://docs.gurock.com/testrail-api2/start
# http://docs.gurock.com/testrail-api2/accessing
#
# Copyright Gurock Software GmbH. See license.md for details.
#

import requests
import json
import base64
from sys import version_info


class APIClient:
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'
        self.current_python_version = version_info.major

    def send_get(self, uri, filepath=None):
        """
        Send Get.
        Issues a GET request (read) against the API and returns the result
        (as Python dict).

        :param uri: The API method to call including parameters (e.g. get_case/1)
        :param filepath: The path and file name for attachment download
                         Used only for 'get_attachment/:attachment_id'
        :return:
        """
        return self.__send_request('GET', uri, filepath)

    def send_post(self, uri, data):
        """
        Send POST
        Issues a POST request (write) against the API and returns the result
        (as Python dict).

        :param uri: The API method to call including parameters (e.g. add_case/1)
        :param data: The data to submit as part of the request (as
                    Python dict, strings must be UTF-8 encoded)
                    If adding an attachment, must be the path
                    to the file
        :return:
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        """
        This is the function that handles comms with testrail.  It checks the python version this is being run against
        first and uses the correct code for each.
        """
        url = self.__url + uri

        if self.current_python_version == 2:
            # if using python version 2.x
            # print('using python 2 __send_request')

            auth = base64.b64encode('%s:%s' % (self.user, self.password))
            headers = {'Authorization': 'Basic ' + auth}

            if method == 'POST':
                if uri[:14] == 'add_attachment':    # add_attachment API method
                    files = {'attachment': (open(data, 'rb'))}
                    response = requests.post(url, headers=headers, files=files)
                    files['attachment'].close()
                else:
                    headers['Content-Type'] = 'application/json'
                    payload = bytes(json.dumps(data))
                    response = requests.post(url, headers=headers, data=payload)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.get(url, headers=headers)

            if response.status_code > 201:
                try:
                    error = response.json()
                    raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
                except:     # response.content not formatted as JSON
                    raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, response.content))
            else:
                if uri[:15] == 'get_attachment/':  # Expecting file, not JSON
                    try:
                        open(data, 'wb').write(response.content)
                        return (data)
                    except:
                        return ("Error saving attachment.")
                else:
                    try:
                        return response.json()
                    except: # Nothing to return
                        return {}

        elif self.current_python_version == 3:
            # if using python version 3.x
            # print('using python3 __send_request')
            auth = str(
                base64.b64encode(
                    bytes('%s:%s' % (self.user, self.password), 'utf-8')
                ),
                'ascii'
            ).strip()
            headers = {'Authorization': 'Basic ' + auth}

            if method == 'POST':
                if uri[:14] == 'add_attachment':  # add_attachment API method
                    files = {'attachment': (open(data, 'rb'))}
                    response = requests.post(url, headers=headers, files=files)
                    files['attachment'].close()
                else:
                    headers['Content-Type'] = 'application/json'
                    payload = bytes(json.dumps(data), 'utf-8')
                    response = requests.post(url, headers=headers, data=payload)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.get(url, headers=headers)

            if response.status_code > 201:
                try:
                    error = response.json()
                except:  # response.content not formatted as JSON
                    error = str(response.content)
                raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
            else:
                if uri[:15] == 'get_attachment/':  # Expecting file, not JSON
                    try:
                        open(data, 'wb').write(response.content)
                        return (data)
                    except:
                        return ("Error saving attachment.")
                else:
                    try:
                        return response.json()
                    except:  # Nothing to return
                        return {}
        else:
            raise ValueError("unexpected python version: {0}.  check the testrail.APIClient.__send_request and"
                             " add a case for the python version you're running.")

    def add_argument(self, command_uri, argument):
        """
        add an argument to a testrail get or post command.
        :type command_uri: str
        :type argument: str
        :param command_uri:
        :param argument:
        :return:
        """
        new_command = '{0}&{1}'.format(command_uri, argument)
        return new_command


class APIError(Exception):
    pass

if __name__ == '__main__':
    client = APIClient('https://testrail.control4.com/')
    client.user = 'bzuck@control4.com'
    client.password = 'Sg/smgJVo2qI2Ua8ksPy-bjjlc4Ew10.umPr.vCt.'

    response = client.send_get('get_projects')
    print(response)