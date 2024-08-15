import boto3
import os
import logging
from datetime import datetime, timedelta


logging.basicConfig()

logger = logging.getLogger("lambda:retrieve_values")
logger.setLevel(os.getenv("LOGLEVEL", "INFO"))
org_client = boto3.client('organizations')

def get_tag_name():
    ssm_client = boto3.client('ssm')
    tag_name = ssm_client.get_parameter(Name="/Control_Tower/account_expiration")['Parameter']['Value']
    return tag_name

def get_accounts(ou_id):
    response = org_client.list_accounts_for_parent(ParentId=ou_id)
    results = response['Accounts']
    while "NextToken" in response:
        response = org_client.list_accounts_for_parent(ParentId=ou_id,NextToken=response["NextToken"])
        results.extend(response['Accounts'])
    return results

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

#get account expiration date from tag
def get_account_expiration_date(account_id, tag_name):
    response = org_client.list_tags_for_resource(ResourceId=account_id)
    for tag in response["Tags"]:
        if tag["Key"] == tag_name:
            try:
                datetime.date.fromisoformat(tag["Value"])
                return tag["Value"]
            except ValueError:
                raise ValueError("Incorrect data format, should be YYYY-MM-DD")
    return None


root_id = org_client.list_roots()['Roots'][0]['Id']
logger.info(f"Root ID: {root_id}")
ou_id = get_ou_id(root_id=root_id, ou_name="Sandbox")
logger.info(f"Sandbox OU ID: {ou_id}")
if ou_id is None: 
    logger.error("Sandbox OU not found.")
    exit(1)
accounts = get_accounts(ou_id)
if len(accounts) == 0:
    logger.info("No accounts found in Sandbox OU.")
    exit(0)
logger.info(f"Number of accounts in Sandbox OU: {len(accounts)}")
tag_name=get_tag_name()
accounts_to_expire = [] #list to store accounts to expire = []
accounts_with_no_tag = []
accounts_to_keep = []
for Id in accounts:
    expiration_date=get_account_expiration_date(Id=Id, tah_name=tag_name)
    if expiration_date is None:
        accounts_with_no_tag.append(Id)
        logger.info(f"Account {Id} does not have the {tag_name} tag.")
        continue
    elif datetime.strptime(expiration_date, '%Y-%m-%d').date() < datetime.now().date():
        accounts_to_expire.append(Id)
        logger.info(f"Account {Id} has expiration date set to {expiration_date}. It needs to be expired.")
    else:
        accounts_to_keep.append(Id)
        prlogger.infoint(f"Account {Id} does not need to be expired. It's expiration date is:{expiration_date} ")

logger.info(f"Accounts in Sandbox OU: {accounts}")
logger.info(f"Accounts to expire: {accounts_to_expire}")
logger.info(f"Number of accounts to expire: {len(accounts_to_expire)}")
logger.info(f"Accounts with no {tag_name} tag: {accounts_with_no_tag}")
logger.info(f"Number of accounts with no {tag_name} tag: {len(accounts_with_no_tag)}")
logger.info(f"Accounts to keep: {accounts_to_keep}")
logger.info(f"Number of accounts to keep: {len(accounts_to_keep)}")



