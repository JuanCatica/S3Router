import boto3
import yaml
import json
import os

BUCKET = os.environ['BUCKET']
PREFIX = os.environ['PREFIX']
TABLE = os.environ['TABLE']

s3 = boto3.client('s3')
dynamo = boto3.client('dynamodb', region_name="us-east-1")

def lambda_handler(event, context):
    rules_created = 0
    rules_failed = 0
    errors = []

    response = s3.get_object(Bucket=BUCKET, Key=PREFIX)
    copy_rules = yaml.safe_load(response['Body'].read().decode('utf-8'))

    # TODO: Truncate table or delete old rules
    for cpr in copy_rules:
        try:
            bucket, prefix, *_ = cpr["path"].split("/")
            item = {
                'bucket':{
                    "S": bucket
                },
                'prefix':{
                    "S": prefix
                },
                'rule': {
                    "S": json.dumps(cpr)
                }
            }
            dynamo.put_item(
                TableName=TABLE,
                Item=item
            )
            rules_created += 1
        except Exception as e:
            errors.append(str(e))
            rules_failed += 1

    return {
        "rules_created": rules_created,
        "rules_failed": rules_failed,
        "errors": errors
    }