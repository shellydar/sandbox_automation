import boto3
import os
from datetime import datetime, timedelta

org_client = boto3.client('organizations')

def get_tag_name():
    ssm_client = boto3.client('ssm')
    tag_name = ssm_client.get_parameter(Name="Control_Tower/account_expiration")['Parameter']['Value']
    return tag_name

def get_accounts(ou_id):
    response = org_client.list_tags_for_resource(arentId=ou_id)
    results = response['Accounts']
    while "NextToken" in response:
        response = org_client.list_accounts(NextToken=response["NextToken"])
        results.extend(response['Accounts'])
    return results

def get_account_tags(account_id):
    response = org_client.list_tags_for_resource(ResourceId=account_id)
    results = response["Tags"]
    while "NextToken" in response:
        response = org_client.list_tags_for_resource(NextToken=response["NextToken"])
        results.extend(response["Tags"])
    return results

def check_expiration(tag_value):
    expiration_date = datetime.strptime(tag_value, "%Y-%m-%d")
    today = datetime.now()
    if today > expiration_date:
        return True
    else:
        return False

# list accounts in AWS OU called "Sandbox"

root_id = org_client.list_roots()['Roots'][0]['Id']
ou_id = [ou['Id'] for ou in org_client.list_organizational_units_for_parent(ParentId=root_id)['OrganizationalUnits'] if ou['Name'] == 'Sandbox'][0]
accounts = get_accounts(ou_id)
tag_name=get_tag_name()
accounts_to_expire = [] #list to store accounts to expire = []

for Id in accounts:
    account_tags = get_account_tags(Id)
    for tag in account_tags:
        if tag['Key'] == tag_name:
            if check_expiration(tag['Value']):
                accounts_to_expire.append(Id)
                print(f"Account {Id} needs to be expired.")
                break
            
            else:
                print(f"Account {Id} does not need to be expired.")
                break
            break
        else:
            print(f"Account {Id} does not have the {tag_name} tag.")
            break
        break
    break
print(f"Accounts to expire: {accounts_to_expire}")
print(f"Number of accounts to expire: {len(accounts_to_expire)}")


print(f"Accounts in Sandbox OU: {accounts}")
print(f"Number of accounts in Sandbox OU: {len(accounts)}")
print(f"Account ID: {account_id}")
print(f"Account Tags: {account_tags}")
print(f"Root ID: {root_id}")
print(f"OU ID: {ou_id}")
print(f"Account ID: {account_id}")
print(f"Account Tags: {account_tags}")

#function to get tag name from systems manager parameter store


