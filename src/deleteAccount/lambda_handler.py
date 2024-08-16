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


def suspendAccount(account_id):
    response = org_client.close_account(AccountId=account_id)
    logger.info(f"Account {account_id} is closed")
    return response

def lambda_handler(event, context):
    if event["Source"]== "account_expiration":
        logger.info(f"Account {event["Detail"]["accountId"]} marked based on expiration date {event["Detail"]["expirationDate"]}. Processing...")
        account_id = event["Detail"]["accountId"]
        suspendAccount(account_id)
    elif event["Source"]== "account_budget":
        logger.info(f"Account {event["Detail"]["accountId"]} marked based on budget exeeded. Processing...")
        account_id = event["Detail"]["accountId"]
        suspendAccount(account_id)
        exit(0)
    else:
        logger.error("Invalid event source. Exiting...")
        exit(1)
