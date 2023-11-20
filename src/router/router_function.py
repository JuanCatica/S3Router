import boto3
import json
import time
import re
import os

TABLE = os.environ['TABLE']
s3 = boto3.client('s3')
dynamo = boto3.client('dynamodb', region_name="us-east-1")

def lambda_handler(event, context):
    logs = []

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    prefix, *obj_name = key.split("/")
    obj_name = '/'.join(obj_name)
    extension = obj_name.split(".")[-1]

    # READ DYNAMO
    response = dynamo.get_item(
        TableName=TABLE,
        Key={
            "bucket": {'S': bucket} ,
            "prefix": {'S': prefix}
        }
    )

    if 'Item' in response:
        eval_file_type = False
        eval_schema = False
        output_destinations = []
        
        rule = json.loads(response['Item']["rule"]["S"])
        regex = rule["regex"]
        destinations = rule["destinations"]
        file_types = rule["eval"]["fileType"] 
        schema = None

        # VALIDATE: FILE TYPE
        if extension in file_types:
            eval_file_type = True

        # VALIDATE: SCHEMA
        # TODO
        eval_schema = True

        if eval_file_type and eval_schema:
            # REPLACEMENT
            real_destinations = _replace_destination(obj_name, destinations, regex, logs)

            # COPY
            for destination in destinations:
                des_bucket, *des_key = destination.split("/")
                des_key = '/'.join(des_key)
                _copy_object(bucket, key, des_bucket, des_key,logs)

        else:
            logs.append(f"EVAL-FAILED: EvalFileType:{eval_file_type}, extension:{extension}, EvalSchema:{eval_schema}")

    else:
        raise Exception(f"No Item Found for bucket:{bucket} and prefix:{prefix}")


def _replace_destination(obj_name, destinations, regex, logs):
    outputs = []
    caps = re.search(regex, obj_name).groupdict()
    for dst in destinations:
        out = dst
        found_error = False

        replacements = re.findall("<(\w+)>", dst).copy()
        for rep in replacements:
            if rep in caps.keys():
                out = out.replace("<"+rep+">", caps[rep])
            else:
                logs.append(f"ERROR: No '{rep}' to be replaced")
                found_error = True
        
        if not found_error:
            outputs.append(out)
    return outputs

def _copy_object(source_bucket, source_key, destination_bucket, destination_key, logs):
    # Copy the object
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    destination = {'Bucket': destination_bucket, 'Key': destination_key}
    
    s3.copy_object(CopySource=copy_source, Bucket=destination['Bucket'], Key=destination['Key'])
    logs.append(f"OK: src:{source_bucket}/{source_key}, dst:{destination_bucket}/{destination_key}")
