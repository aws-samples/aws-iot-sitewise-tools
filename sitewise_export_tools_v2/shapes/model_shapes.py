# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json

# until we support alarms we need to remove "AssetModelCompositeModels" from the shape.
AssetModel = json.loads('''
{
  "Type" : "AWS::IoTSiteWise::AssetModel",
  "Properties" : {
      "AssetModelDescription" : "",
      "AssetModelHierarchies" : [],
      "AssetModelName" : "",
      "AssetModelProperties" : [],
      "AssetModelCompositeModels": [],
      "Tags" : []
    }
}
''')

AssetModelProperty = json.loads('''
{
  "DataType" : "",
  "DataTypeSpec" : "",
  "LogicalId" : "",
  "Name" : "",
  "Type" : [],
  "Unit" : ""
}
''')

AssetModelCompositeModel = json.loads('''
{
  "CompositeModelProperties" : "",
  "Description" : "",
  "Name" : "",
  "Type" : ""
}
''')

PropertyType = json.loads('''
{
  "Attribute" : [],
  "Metric" : [],
  "Transform" : [],
  "TypeName" : ""
}
''')

Attribute = json.loads('''
{
  "DefaultValue" : ""
}
''')

Metric = json.loads('''
{
  "Expression" : "",
  "Variables" : [],
  "Window" : ""
}
''')

MetricWindow = json.loads('''
{
  "Tumbling" : ""
}
''')

TumblingWindow = json.loads('''
{
  "Interval" : ""
}
''')

Transform = json.loads('''
{
  "Expression" : "",
  "Variables" : []
}
''')

ExpressionVariable = json.loads('''
{
  "Name" : "",
  "Value" : []
}
''')

VariableValue = json.loads('''
{
  "HierarchyLogicalId" : "",
  "PropertyLogicalId" : ""
}
''')

AssetModelHierarchy = json.loads('''
{
  "ChildAssetModelId" : "",
  "LogicalId" : "",
  "Name" : ""
}
''')
