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
    print(f"Account ID: {account_id}, Tag Name: {tag_name}, Expiration Date: {expiration_date}")
    for tag in response["Tags"]:
        if tag["Key"] == tag_name:
            print(f"Tag {tag_name} already exists for account {account_id} with value {tag["Value"]} Updating value to {expiration_date}")
    org_client.tag_resource(ResourceId=account_id, Tags=[{'Key': tag_name, 'Value': expiration_date}])

def suspendAccount(account_id):
    
    org_client.close_account(AccountId=account_id)
    print(f"Account {account_id} not found in Sandbox OU. Exiting.")

def lambda_handler(event, context):
    if event["Source"]== "account_expiration":
        print(f"Account {event["Detail"]["accountId"]} marked based on expiration date {event["Detail"]["expirationDate"]}. Processing...")
        account_id = event["Detail"]["accountId"]
        suspendAccount(account_id)
    else:
        print("Event not related to Sandbox OU. Exiting.")
        exit(0)
