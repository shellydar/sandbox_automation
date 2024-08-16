import boto3
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig()

logger = logging.getLogger("lambda:retrieve_values")
logger.setLevel(os.getenv("LOGLEVEL", "INFO"))
org_client = boto3.client('organizations')

def get_tag_name():
    ssm_client = boto3.client('ssm')
    tag_name = ssm_client.get_parameter(Name="/Control_Tower/account_expiration")['Parameter']['Value']
    return tag_name

def get_expiration_period():
    ssm_client = boto3.client('ssm')
    period = ssm_client.get_parameter(Name="/Control_Tower/account_expiration_period")['Parameter']['Value']
    return period


#get OU ID for Sandbox OU
def get_ou_id(root_id, ou_name):
    logger.info(f"getOU ID for Root ID: {root_id} and ou_name {ou_name}")
    response = org_client.list_organizational_units_for_parent(ParentId=root_id)
    if "NextToken" in response:
        while "NextToken" in response:
            response = org_client.list_organizational_units_for_parent(ParentId=root_id, NextToken=response["NextToken"])
            for ou in response["OrganizationalUnits"]:
                logger.info(f"Response: {response}")
                if ou["Name"].lower() == ou_name.lower:
                    return ou["Id"]
    else:
        for ou in response["OrganizationalUnits"]:
            if ou["Name"].lower() == ou_name.lower():
                return ou["Id"]



def set_account_expiration_date(account_id, tag_name, months):
    response = org_client.list_tags_for_resource(ResourceId=account_id)
    expiration_date = (datetime.now() + timedelta(days=30*months)).strftime('%Y-%m-%d')
    logger.info(f"Account ID: {account_id}, Tag Name: {tag_name}, Expiration Date: {expiration_date}")
    for tag in response["Tags"]:
        if tag["Key"] == tag_name:
            logger.info(f"Tag {tag_name} already exists for account {account_id} with value {tag["Value"]} Updating value to {expiration_date}")
    org_client.tag_resource(ResourceId=account_id, Tags=[{'Key': tag_name, 'Value': expiration_date}])


def lambda_handler(event, context):
    root_id = org_client.list_roots()['Roots'][0]['Id']
    tag_name=get_tag_name()
    expiration_period=get_expiration_period()
    logger.info(f"Root ID: {root_id}")
    ou_id = get_ou_id(root_id=root_id, ou_name="Sandbox")
    logger.info(f"Sandbox OU ID: {ou_id}")
    if ou_id is None: 
        logger.error("Sandbox OU not found.")
        exit(1)
    if event["detail"]["eventName"] == "CreateManagedAccount" :
        if event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["organizationalUnit"]["organizationalUnitId"] == ou_id :
            account_id = event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
            set_account_expiration_date(account_id, tag_name, int(expiration_period))
            exit(0)
        else:
            logger.info("Event not related to Sandbox OU. Exiting.")
            exit(0)
    elif event["detail"]["eventName"] == "NewAccountCreated" :
        account_id = event["detail"]["accountId"]
        expiration_period = event["detail"]["expirationPeriod"]
        set_account_expiration_date(account_id, tag_name, int(expiration_period))
        exit(0)
