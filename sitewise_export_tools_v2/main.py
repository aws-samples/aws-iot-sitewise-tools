# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import argparse
import logging
import sys

import boto3
from botocore.config import Config

from assets import extract_assets, get_top_level_assets
from models import extract_models
from utils import create_json_template, assert_sitewise_response

client = None

cfn_base = {
    'AWSTemplateFormatVersion': '2010-09-09',
    'Description': 'SiteWise Export',
    'Resources': {}
}

logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    stream=sys.stdout)

logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

logger = logging.getLogger()


def extract(client, assets: list = None) -> dict:
    cfn = cfn_base.copy()

    # get all models
    model_resources, lookup_model_id, lookup_model_property = extract_models(client)
    cfn['Resources'].update(model_resources)

    # when '-a' switch was included on the command line but no assets we're specified, retrieve all top-level assets
    if assets is not None and len(assets) == 0:
        logger.debug('Automatically including all top-level assets ...')
        assets = [asset['id'] for asset in get_top_level_assets(client)]

    if assets:
        cfn_assets = extract_assets(assets, lookup_model_id, lookup_model_property, client)
        cfn['Resources'].update(cfn_assets)

    return cfn


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Asset & Model Export Tool For SiteWise')
    parser.add_argument('--profile', help='Credentials profile for the AWS account')
    parser.add_argument('--region', help='Specify the AWS region you would like to target')
    parser.add_argument('-a', '--assets', required=False, metavar='ASSET_ID', nargs='*',
                        help='List of SiteWise Asset id\'s to be included and recursively exported')
    parser.add_argument('-v', '--verbose', help='Enable verbose logging', action='store_true', default=False)
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.debug(f'{__file__} called with arguments: {args}')

    # Setup the AWS SiteWise boto3 client
    if args.profile:
        boto3.setup_default_session(profile_name=args.profile)
    if args.region:
        my_config = Config(region_name=args.region)
    else:
        my_config = Config()
    client = boto3.client('iotsitewise', config=my_config)

    # Execute extraction:
    cfn = extract(client, assets=args.assets)

    # Dump CloudFormation into a json file
    create_json_template(cfn, name='sitewise-assets-and-models' if args.assets == [] else 'sitewise-models')
