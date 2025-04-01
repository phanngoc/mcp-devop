import os
import json
import time
import subprocess
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import boto3
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")

# Initialize AWS clients
boto3_config = {}
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    boto3_config.update({
        'aws_access_key_id': AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
    })
    if AWS_SESSION_TOKEN:
        boto3_config.update({'aws_session_token': AWS_SESSION_TOKEN})

# Create boto3 clients with the configuration
s3_client = boto3.client('s3', region_name=AWS_REGION, **boto3_config)
dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION, **boto3_config)
cloudwatch_client = boto3.client('cloudwatch', region_name=AWS_REGION, **boto3_config)
cloudwatch_logs_client = boto3.client('logs', region_name=AWS_REGION, **boto3_config)
lambda_client = boto3.client('lambda', region_name=AWS_REGION, **boto3_config)
ec2_client = boto3.client('ec2', region_name=AWS_REGION, **boto3_config)
iam_client = boto3.client('iam', region_name=AWS_REGION, **boto3_config)

# Create MCP server
mcp = FastMCP("AWS Integration Server")

# ----- S3 Resources and Tools -----

@mcp.resource("s3://{bucket}/{key}")
def s3_resource(bucket: str, key: str) -> str:
    """Access S3 content as a resource"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        return f"Error accessing S3: {str(e)}"

@mcp.tool()
def list_s3_buckets() -> str:
    """List all S3 buckets"""
    try:
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return json.dumps(buckets, indent=2)
    except Exception as e:
        return f"Error listing S3 buckets: {str(e)}"

@mcp.tool()
def list_s3_objects(bucket: str, prefix: str = "") -> str:
    """List objects in an S3 bucket with optional prefix"""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = [obj['Key'] for obj in response.get('Contents', [])]
        return json.dumps(objects, indent=2)
    except Exception as e:
        return f"Error listing S3 objects: {str(e)}"

@mcp.tool()
def get_s3_object_info(bucket: str, key: str) -> str:
    """Get detailed information about an S3 object"""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        info = {
            "ContentLength": response.get('ContentLength'),
            "ContentType": response.get('ContentType'),
            "LastModified": response.get('LastModified').strftime('%Y-%m-%d %H:%M:%S'),
            "Metadata": response.get('Metadata', {}),
            "StorageClass": response.get('StorageClass'),
            "ETag": response.get('ETag')
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting S3 object info: {str(e)}"

# ----- DynamoDB Resources and Tools -----

@mcp.resource("dynamodb://{table}/{key_name}/{key_value}")
def dynamodb_resource(table: str, key_name: str, key_value: str) -> str:
    """Access DynamoDB item as a resource"""
    try:
        response = dynamodb_client.get_item(
            TableName=table,
            Key={key_name: {"S": key_value}}
        )
        item = response.get('Item', {})
        return json.dumps(item, indent=2)
    except Exception as e:
        return f"Error accessing DynamoDB: {str(e)}"

@mcp.tool()
def list_dynamodb_tables() -> str:
    """List all DynamoDB tables"""
    try:
        response = dynamodb_client.list_tables()
        tables = response.get('TableNames', [])
        return json.dumps(tables, indent=2)
    except Exception as e:
        return f"Error listing DynamoDB tables: {str(e)}"

@mcp.tool()
def query_dynamodb(table: str, key_name: str, key_value: str, limit: int = 10) -> str:
    """Query DynamoDB table"""
    try:
        response = dynamodb_client.query(
            TableName=table,
            KeyConditionExpression=f"{key_name} = :value",
            ExpressionAttributeValues={
                ":value": {"S": key_value}
            },
            Limit=limit
        )
        items = response.get('Items', [])
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error querying DynamoDB: {str(e)}"

@mcp.tool()
def describe_dynamodb_table(table: str) -> str:
    """Get detailed information about a DynamoDB table"""
    try:
        response = dynamodb_client.describe_table(TableName=table)
        table_info = response.get('Table', {})
        info = {
            "TableName": table_info.get('TableName'),
            "Status": table_info.get('TableStatus'),
            "ProvisionedThroughput": {
                "ReadCapacityUnits": table_info.get('ProvisionedThroughput', {}).get('ReadCapacityUnits'),
                "WriteCapacityUnits": table_info.get('ProvisionedThroughput', {}).get('WriteCapacityUnits')
            },
            "KeySchema": table_info.get('KeySchema', []),
            "ItemCount": table_info.get('ItemCount'),
            "CreationDateTime": table_info.get('CreationDateTime').strftime('%Y-%m-%d %H:%M:%S') if table_info.get('CreationDateTime') else None,
            "TableSizeBytes": table_info.get('TableSizeBytes')
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error describing DynamoDB table: {str(e)}"

# ----- CloudWatch Resources and Tools -----

@mcp.resource("cloudwatch://{namespace}/{metric_name}/{period}")
def cloudwatch_resource(namespace: str, metric_name: str, period: str) -> str:
    """Access CloudWatch metrics as a resource"""
    try:
        # Parse period in minutes and convert to seconds
        period_mins = int(period)
        period_seconds = period_mins * 60
        
        # Calculate time range (last period_mins minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=period_mins)
        
        response = cloudwatch_client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[],  # No dimensions for simplicity
            StartTime=start_time,
            EndTime=end_time,
            Period=period_seconds,
            Statistics=['Average', 'Maximum', 'Minimum']
        )
        
        datapoints = response.get('Datapoints', [])
        
        # Sort datapoints by timestamp
        sorted_datapoints = sorted(datapoints, key=lambda x: x['Timestamp'])
        
        # Format the response
        formatted_datapoints = []
        for point in sorted_datapoints:
            formatted_datapoints.append({
                "Timestamp": point['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "Average": point.get('Average'),
                "Maximum": point.get('Maximum'),
                "Minimum": point.get('Minimum'),
                "Unit": point.get('Unit')
            })
        
        return json.dumps(formatted_datapoints, indent=2)
    except Exception as e:
        return f"Error accessing CloudWatch metrics: {str(e)}"

@mcp.tool()
def list_cloudwatch_metrics(namespace: str) -> str:
    """List available CloudWatch metrics for a namespace"""
    try:
        response = cloudwatch_client.list_metrics(Namespace=namespace)
        metrics = response.get('Metrics', [])
        
        # Simplify the response
        formatted_metrics = []
        for metric in metrics:
            formatted_metrics.append({
                "MetricName": metric.get('MetricName'),
                "Namespace": metric.get('Namespace'),
                "Dimensions": metric.get('Dimensions', [])
            })
        
        return json.dumps(formatted_metrics, indent=2)
    except Exception as e:
        return f"Error listing CloudWatch metrics: {str(e)}"

@mcp.tool()
def get_cloudwatch_alarms() -> str:
    """List CloudWatch alarms and their status"""
    try:
        response = cloudwatch_client.describe_alarms()
        alarms = response.get('MetricAlarms', [])
        
        # Simplify the response
        formatted_alarms = []
        for alarm in alarms:
            formatted_alarms.append({
                "AlarmName": alarm.get('AlarmName'),
                "AlarmDescription": alarm.get('AlarmDescription'),
                "StateValue": alarm.get('StateValue'),
                "MetricName": alarm.get('MetricName'),
                "Namespace": alarm.get('Namespace'),
                "Threshold": alarm.get('Threshold'),
                "ComparisonOperator": alarm.get('ComparisonOperator')
            })
        
        return json.dumps(formatted_alarms, indent=2)
    except Exception as e:
        return f"Error getting CloudWatch alarms: {str(e)}"

# ----- Lambda Resources and Tools -----

@mcp.resource("lambda://{function_name}")
def lambda_resource(function_name: str) -> str:
    """Access Lambda function configuration as a resource"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        
        # Extract relevant information
        configuration = response.get('Configuration', {})
        
        # Format the response
        info = {
            "FunctionName": configuration.get('FunctionName'),
            "Runtime": configuration.get('Runtime'),
            "Handler": configuration.get('Handler'),
            "CodeSize": configuration.get('CodeSize'),
            "Description": configuration.get('Description'),
            "Timeout": configuration.get('Timeout'),
            "MemorySize": configuration.get('MemorySize'),
            "LastModified": configuration.get('LastModified'),
            "Role": configuration.get('Role'),
            "Environment": configuration.get('Environment', {}).get('Variables', {})
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error accessing Lambda function: {str(e)}"

@mcp.tool()
def list_lambda_functions() -> str:
    """List all Lambda functions"""
    try:
        response = lambda_client.list_functions()
        functions = response.get('Functions', [])
        
        # Simplify the response
        formatted_functions = []
        for function in functions:
            formatted_functions.append({
                "FunctionName": function.get('FunctionName'),
                "Runtime": function.get('Runtime'),
                "Handler": function.get('Handler'),
                "LastModified": function.get('LastModified'),
                "MemorySize": function.get('MemorySize'),
                "Timeout": function.get('Timeout')
            })
        
        return json.dumps(formatted_functions, indent=2)
    except Exception as e:
        return f"Error listing Lambda functions: {str(e)}"

@mcp.tool()
def get_lambda_invocations(function_name: str, days: int = 1) -> str:
    """Get Lambda function invocation metrics"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get invocation metrics
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': function_name
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Sum']
        )
        
        datapoints = response.get('Datapoints', [])
        
        # Sort datapoints by timestamp
        sorted_datapoints = sorted(datapoints, key=lambda x: x['Timestamp'])
        
        # Format the response
        formatted_datapoints = []
        for point in sorted_datapoints:
            formatted_datapoints.append({
                "Timestamp": point['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                "Invocations": point.get('Sum', 0),
            })
        
        return json.dumps(formatted_datapoints, indent=2)
    except Exception as e:
        return f"Error getting Lambda invocations: {str(e)}"

# ----- EC2 Resources and Tools -----

@mcp.resource("ec2://{instance_id}")
def ec2_resource(instance_id: str) -> str:
    """Access EC2 instance details as a resource"""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response.get('Reservations'):
            return f"No instance found with ID: {instance_id}"
        
        instance = response['Reservations'][0]['Instances'][0]
        
        # Format the response
        info = {
            "InstanceId": instance.get('InstanceId'),
            "InstanceType": instance.get('InstanceType'),
            "State": instance.get('State', {}).get('Name'),
            "LaunchTime": instance.get('LaunchTime').strftime('%Y-%m-%d %H:%M:%S') if instance.get('LaunchTime') else None,
            "PublicIpAddress": instance.get('PublicIpAddress'),
            "PrivateIpAddress": instance.get('PrivateIpAddress'),
            "SecurityGroups": [sg.get('GroupName') for sg in instance.get('SecurityGroups', [])],
            "Tags": {tag.get('Key'): tag.get('Value') for tag in instance.get('Tags', [])}
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error accessing EC2 instance: {str(e)}"

@mcp.tool()
def list_ec2_instances() -> str:
    """List all EC2 instances"""
    try:
        response = ec2_client.describe_instances()
        
        instances = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instances.append({
                    "InstanceId": instance.get('InstanceId'),
                    "InstanceType": instance.get('InstanceType'),
                    "State": instance.get('State', {}).get('Name'),
                    "PublicIpAddress": instance.get('PublicIpAddress'),
                    "PrivateIpAddress": instance.get('PrivateIpAddress'),
                    "Name": next((tag.get('Value') for tag in instance.get('Tags', []) if tag.get('Key') == 'Name'), "")
                })
        
        return json.dumps(instances, indent=2)
    except Exception as e:
        return f"Error listing EC2 instances: {str(e)}"

@mcp.tool()
def get_ec2_status(instance_id: str) -> str:
    """Get detailed status of an EC2 instance"""
    try:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        
        if not response.get('InstanceStatuses'):
            return f"No status information available for instance: {instance_id}"
        
        status = response['InstanceStatuses'][0]
        
        # Format the response
        info = {
            "InstanceId": status.get('InstanceId'),
            "InstanceState": status.get('InstanceState', {}).get('Name'),
            "InstanceStatus": status.get('InstanceStatus', {}).get('Status'),
            "SystemStatus": status.get('SystemStatus', {}).get('Status'),
            "Events": status.get('Events', [])
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting EC2 status: {str(e)}"

# ----- IAM Resources and Tools -----

@mcp.resource("iam://{role_name}")
def iam_role_resource(role_name: str) -> str:
    """Access IAM role details as a resource"""
    try:
        response = iam_client.get_role(RoleName=role_name)
        role = response.get('Role', {})
        
        # Format the response
        info = {
            "RoleName": role.get('RoleName'),
            "RoleId": role.get('RoleId'),
            "Arn": role.get('Arn'),
            "Path": role.get('Path'),
            "CreateDate": role.get('CreateDate').strftime('%Y-%m-%d %H:%M:%S') if role.get('CreateDate') else None,
            "AssumeRolePolicyDocument": role.get('AssumeRolePolicyDocument')
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error accessing IAM role: {str(e)}"

@mcp.tool()
def list_iam_roles() -> str:
    """List all IAM roles"""
    try:
        response = iam_client.list_roles()
        roles = response.get('Roles', [])
        
        # Simplify the response
        formatted_roles = []
        for role in roles:
            formatted_roles.append({
                "RoleName": role.get('RoleName'),
                "Path": role.get('Path'),
                "Created": role.get('CreateDate').strftime('%Y-%m-%d') if role.get('CreateDate') else None
            })
        
        return json.dumps(formatted_roles, indent=2)
    except Exception as e:
        return f"Error listing IAM roles: {str(e)}"

@mcp.tool()
def list_iam_policies(role_name: str) -> str:
    """List policies attached to an IAM role"""
    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        policies = response.get('AttachedPolicies', [])
        
        # Format the response
        formatted_policies = []
        for policy in policies:
            formatted_policies.append({
                "PolicyName": policy.get('PolicyName'),
                "PolicyArn": policy.get('PolicyArn')
            })
        
        return json.dumps(formatted_policies, indent=2)
    except Exception as e:
        return f"Error listing IAM policies: {str(e)}"

# ----- Prompts -----

@mcp.prompt()
def aws_status_prompt() -> str:
    """Generate a prompt to check AWS service status"""
    return "Please analyze the current status of our AWS resources and services. What issues or anomalies do you see?"

@mcp.prompt()
def s3_analysis_prompt(bucket: str) -> str:
    """Generate a prompt to analyze S3 bucket contents"""
    return f"Please analyze the contents of S3 bucket '{bucket}' and provide insights or recommendations."

@mcp.prompt()
def ec2_monitoring_prompt(instance_id: str) -> str:
    """Generate a prompt to monitor EC2 instance"""
    return f"Please monitor the status and performance of EC2 instance '{instance_id}'. Provide insights and recommendations."

@mcp.prompt()
def cost_analysis_prompt() -> str:
    """Generate a prompt for AWS cost analysis"""
    return "Please analyze our AWS costs and provide recommendations for optimization and cost-saving opportunities."

@mcp.tool()
def list_cloudwatch_log_groups() -> str:
    """List all CloudWatch log groups"""
    try:
        response = cloudwatch_logs_client.describe_log_groups()
        log_groups = response.get('logGroups', [])
        
        # Format the response
        formatted_groups = []
        for group in log_groups:
            formatted_groups.append({
                "logGroupName": group.get('logGroupName'),
                "storedBytes": group.get('storedBytes'),
                "creationTime": datetime.fromtimestamp(group.get('creationTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S'),
                "retentionInDays": group.get('retentionInDays', 'Never Expire')
            })
        
        return json.dumps(formatted_groups, indent=2)
    except Exception as e:
        return f"Error listing CloudWatch log groups: {str(e)}"

@mcp.tool()
def run_cloudwatch_logs_query(log_group_name: str, query: str, hours: int = 24) -> str:
    """Run a CloudWatch Logs Insights query
    
    Args:
        log_group_name: The name of the log group to query
        query: The query string in CloudWatch Logs Insights syntax
        hours: Number of hours to look back (default 24)
    """
    try:
        # Calculate time range
        end_time = int(time.time())
        start_time = end_time - (hours * 3600)  # Convert hours to seconds
        
        # Start the query
        start_query_response = cloudwatch_logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query,
            limit=1000  # Maximum number of results to return
        )
        
        query_id = start_query_response['queryId']
        
        # Wait for query to complete
        response = None
        while response is None or response['status'] == 'Running':
            time.sleep(1)
            response = cloudwatch_logs_client.get_query_results(
                queryId=query_id
            )
        
        # Format results
        if response['status'] == 'Complete':
            results = []
            for result in response.get('results', []):
                # Convert the list of field/value pairs into a dictionary
                result_dict = {}
                for field in result:
                    result_dict[field['field']] = field['value']
                results.append(result_dict)
            
            return json.dumps({
                'status': 'Complete',
                'statistics': {
                    'recordsMatched': response.get('statistics', {}).get('recordsMatched', 0),
                    'recordsScanned': response.get('statistics', {}).get('recordsScanned', 0),
                    'bytesScanned': response.get('statistics', {}).get('bytesScanned', 0)
                },
                'results': results
            }, indent=2)
        else:
            return json.dumps({
                'status': response['status'],
                'error': 'Query did not complete successfully'
            }, indent=2)
            
    except Exception as e:
        return f"Error running CloudWatch Logs query: {str(e)}"

if __name__ == "__main__":
    # Start the server
    mcp.run() 