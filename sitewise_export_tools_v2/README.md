# SiteWise Export Tools V2

## Asset Model Export Tool
Generates a CloudFormation template of all the SiteWise _models_ (including the hierarchy information) and _assets_ for a given region in an AWS account. 
The CloudFormation template can then be used to create the same SiteWise models and assets in a different region and/or AWS account.

Note: The tool does not support exporting of alarms.

### Usage

Call `./main.py` to export SIteWise models and/or assets into the `./cfnexport` destination folder.

```shell
$ python3 main.py --help
usage: main.py [-h] [--profile PROFILE] [--region REGION] [-a [ASSET_ID [ASSET_ID ...]]] [-v]

Asset & Model Export Tool For SiteWise

optional arguments:
  -h, --help            show this help message and exit
  --profile PROFILE     Credentials profile for the AWS account
  --region REGION       Specify the AWS region you would like to target
  -a [ASSET_ID [ASSET_ID ...]], --assets [ASSET_ID [ASSET_ID ...]]
                        List of SiteWise Asset id's to be included and recursively exported
  -v, --verbose         Enable verbose logging
```
**Exporting only SiteWise asset models:**
```shell
$ python3 -v main.py
05/10/2022 03:24:50 PM main DEBUG: ./main.py called with arguments: Namespace(assets=None, profile=None, region=None, verbose=True)
05/10/2022 03:24:50 PM models DEBUG: Scanning SiteWise models ...
05/10/2022 03:24:50 PM models INFO: Discovered model "TestModel"
05/10/2022 03:24:51 PM models INFO: Discovered model "TestSubModel"
05/10/2022 03:24:51 PM utils INFO: CloudFormation template of 2 resources successfully saved at "cfnexport/sitewise-models.json"
```

**Exporting SiteWise assets and models:**

There are three ways to command to export the assets using the command-line the argument `-a | --assets`.
In each case, all child assets of these assets are automatically included as well.

1. Export a single asset and it's children:
```shell
$ python3 ./main.py -v -a c595dea7-f616-4233-984c-0a6367738e4a
05/10/2022 03:25:47 PM main DEBUG: ./main.py called with arguments: Namespace(assets=['c595dea7-f616-4233-984c-0a6367738e4a'], profile=None, region=None, verbose=True)
05/10/2022 03:25:47 PM models DEBUG: Scanning SiteWise models ...
05/10/2022 03:25:47 PM models INFO: Discovered model "TestModel"
05/10/2022 03:25:47 PM models INFO: Discovered model "TestSubModel"
05/10/2022 03:25:47 PM assets DEBUG: Scanning SiteWise Assets ...
05/10/2022 03:25:47 PM assets INFO: Discovered asset "TestAsset"
05/10/2022 03:25:48 PM assets INFO: Discovered asset "TestSubAsset"
05/10/2022 03:25:48 PM utils INFO: CloudFormation template of 4 resources successfully saved at "cfnexport/sitewise-assets-and-models.json"
```

2. Export multiple assets (pass a list of asset-id's separated by space):
```shell
$ python3 ./main.py -v -a c595dea7-f616-4233-984c-0a6367738e4a abcf1b29-8ae5-4b22-b7c6-62de7b75bbe6
05/10/2022 03:27:01 PM main DEBUG: ./main.py called with arguments: Namespace(assets=['c595dea7-f616-4233-984c-0a6367738e4a', 'abcf1b29-8ae5-4b22-b7c6-62de7b75bbe6'], profile=None, region=None, verbose=True)
05/10/2022 03:27:01 PM models DEBUG: Scanning SiteWise models ...
05/10/2022 03:27:02 PM models INFO: Discovered model "TestModel"
05/10/2022 03:27:02 PM models INFO: Discovered model "TestSubModel"
05/10/2022 03:27:02 PM assets DEBUG: Scanning SiteWise Assets ...
05/10/2022 03:27:02 PM assets INFO: Discovered asset "TestAsset1"
05/10/2022 03:27:02 PM assets INFO: Discovered asset "TestSubAsset"
05/10/2022 03:27:03 PM assets INFO: Discovered asset "TestAsset2"
05/10/2022 03:27:03 PM utils INFO: CloudFormation template of 5 resources successfully saved at "cfnexport/sitewise-assets-and-models.json"
```

3. Export all assets

In this scenario, the list of assets gets populated at runtime with the top-level list of Sitewise assets. 
```shell
$ python3 ./main.py -v -a
05/10/2022 03:25:11 PM main DEBUG: ./main.py called with arguments: Namespace(assets=[], profile=None, region=None, verbose=True)
05/10/2022 03:25:11 PM models DEBUG: Scanning SiteWise models ...
05/10/2022 03:25:12 PM models INFO: Discovered model "TestModel"
05/10/2022 03:25:12 PM models INFO: Discovered model "TestSubModel"
05/10/2022 03:25:12 PM main DEBUG: Automatically including all top-level assets ...
05/10/2022 03:25:12 PM assets DEBUG: Scanning SiteWise Assets ...
05/10/2022 03:25:12 PM assets INFO: Discovered asset "TestAsset"
05/10/2022 03:25:12 PM assets INFO: Discovered asset "TestSubAsset"
05/10/2022 03:25:12 PM utils INFO: CloudFormation template of 4 resources successfully saved at "cfnexport/sitewise-assets-and-models.json"
```

