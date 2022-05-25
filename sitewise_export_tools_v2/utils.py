# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0`
import json
import logging
import os
import re
import uuid

logger = logging.getLogger()


def randomize(prefix: str) -> str:
    """
    Generates a random string from prefix, i.e. name0234214
    """
    return cfn_string(prefix) + uuid.uuid4().hex[:8]


def cfn_string(s: str) -> str:
    """
    Converts string to a form accepted by CloudFormation
    """
    return re.sub(r'[^A-Za-z0-9]+', '', s)


def create_json_template(cfn, name='sitewise-assets-and-models'):
    """
    Saves the dictionary as a json file.
    """
    base_export_path = 'cfnexport'
    logger.info(f'CloudFormation template of {len(cfn["Resources"])} resources successfully saved at "{base_export_path}/{name}.json"')

    if not os.path.exists(base_export_path):
        os.makedirs(base_export_path)

    cfn_template = json.dumps(cfn, sort_keys=False, indent=4)
    with open(f'{base_export_path}/{name}.json', "w") as fp:
        fp.write(cfn_template)


def walk_dict_filter(resource, case_handler, **kwargs):
    """
    Goes over the fields & values of a dictionary or list and updates it by camel-casing the field name and applying a
    transformation over each field value.
    """
    if isinstance(resource, dict):
        return {
            k[0].upper() + k[1:]: walk_dict_filter(case_handler(k, v, **{**kwargs, 'parent': resource}), case_handler,
                                                   **kwargs) for k, v in
            resource.items() if
            ('shape_filter' in kwargs and k[0].upper() + k[1:] in kwargs[
                'shape_filter']) or 'shape_filter' not in kwargs}
    elif isinstance(resource, list):
        return [walk_dict_filter(item, case_handler, **{**kwargs, 'parent': item}) for item in resource]

    return resource


def assert_sitewise_response(response, method='sitewise'):
    """Checks IoT SiteWise's API response for any errors and raises Exception if any are found."""
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'{method} failed: {response}')

    if 'errorEntries' in response and response['errorEntries']:
        raise Exception(
            f'{method} API failed due to: '
            f'{json.dumps(response["errorEntries"], indent=4, sort_keys=True, default=str)}')
