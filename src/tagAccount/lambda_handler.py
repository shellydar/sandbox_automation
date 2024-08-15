import boto3
import os
from datetime import datetime, timedelta

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
    print(f"getOU ID for Root ID: {root_id} and ou_name {ou_name}")
    response = org_client.list_organizational_units_for_parent(ParentId=root_id)
    if "NextToken" in response:
        while "NextToken" in response:
            response = org_client.list_organizational_units_for_parent(ParentId=root_id, NextToken=response["NextToken"])
            for ou in response["OrganizationalUnits"]:
                print(f"Response: {response}")
                if ou["Name"].lower() == ou_name.lower:
                    return ou["Id"]
    else:
        for ou in response["OrganizationalUnits"]:
            if ou["Name"].lower() == ou_name.lower():
                return ou["Id"]



def set_account_expiration_date(account_id, tag_name, months):
    response = org_client.list_tags_for_resource(ResourceId=account_id)
    expiration_date = (datetime.now() + timedelta(days=30*months)).strftime('%Y-%m-%d')
    for tag in response["Tags"]:
        if tag["Key"] == tag_name:
            print(f"Tag {tag_name} already exists for account {account_id} with value {tag["Value"]} Updating value to {expiration_date}")
    org_client.tag_resource(ResourceId=account_id, Tags=[{'Key': tag_name, 'Value': expiration_date}])


def lambda_handler(event, context):
    root_id = org_client.list_roots()['Roots'][0]['Id']
    print(f"Root ID: {root_id}")
    ou_id = get_ou_id(root_id=root_id, ou_name="Sandbox")
    print(f"Sandbox OU ID: {ou_id}")
    if ou_id is None: 
        print("Sandbox OU not found.")
        exit(1)
    if event["detail"]["eventName"] == "CreateManagedAccount" and event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["organizationalUnit"]["organizationalUnitId"] == ou_id :
        account_id = event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
        tag_name=get_tag_name()
        expiration_period=get_expiration_period()
        set_account_expiration_date(ou_id, tag_name, int(expiration_period))
    else:
        print("Event not related to Sandbox OU. Exiting.")
        exit(0)
