# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

# until we support alarms we need to remove "AssetModelCompositeModels" from the shape.

Asset = json.loads('''
{
  "Type" : "AWS::IoTSiteWise::Asset",
  "Properties" : {
      "AssetHierarchies" : "",
      "AssetModelId" : "",
      "AssetName" : "",
      "AssetProperties" : [],
      "Tags" : []
    }
}
''')

AssetProperty = json.loads('''
 {
      "Alias" : "",
      "LogicalId" : "",
      "NotificationState" :""
}
''')

AssetHierarchy = json.loads('''
 {
      "ChildAssetId" : "",
      "LogicalId" : ""
}
''')
