import json
import os

import requests_mock

from tests import settings


def register_uris(requirements, requests_mocker):
    """
    Registers each fixture with the given mocker. Loads the fixture from
    the corresponding fixtures json file.
    :param requirements: a dictionary with keys corresponding to the fixture filenames and values corresponding to
     the top-level keys in that particular file.
    :type requirements: dict
    :param requests_mocker: the mocker to register the json responses to.
    :type requests_mocker: requests_mock.mocker.Mocker
    """
    for fixture, objects in requirements.items():
        with open(os.path.join(os.path.dirname(__file__), f'fixtures/{fixture}.json')) as file:
            data = json.loads(file.read())

        if not isinstance(objects, set):
            raise TypeError(f'{objects} is not a set.')

        for obj_name in objects:
            obj = data.get(obj_name)

            if obj is None:
                raise ValueError('{} does not exist in {}.json'.format(
                    obj_name.__repr__(),
                    fixture
                ))

            method = requests_mock.ANY if obj['method'] == 'ANY' else obj['method']
            if obj['path'] == 'ANY':
                url = requests_mock.ANY
            else:
                url = settings.BASE_URL_WITH_VERSION + obj['path']

            if 'compose' in obj:
                response_json = []
                for key in obj.get('compose'):
                    response_json.append(data[key]['body'])
            elif 'body' in obj:
                response_json = obj.get('body')

            requests_mocker.register_uri(
                method,
                url,
                json=response_json,
                status_code=obj.get('status', 200),
                headers=obj.get('headers', {})
            )
