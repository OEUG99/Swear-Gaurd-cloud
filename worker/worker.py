import re
from datetime import datetime

import boto3
import json
import time
from video_processing import *

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Configuration
bucket_name = 'applebananatest123'

# Initialize SQS client
sqs = boto3.client('sqs')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Configuration: Replace with your queue URL
queue_url = 'https://sqs.us-east-1.amazonaws.com/812477365003/FileStateQueue'  # Replace with your queue's URL

def poll_sqs():
    print("Polling for messages in the queue...")
    try:
        while True:
            # Receive messages from the SQS queue
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,  # Receive one message at a time
                WaitTimeSeconds=10,     # Long polling: waits for 10 seconds if no messages are available
                VisibilityTimeout=20    # Time for the consumer to process the message before it becomes visible again
            )

            # Check if any messages are received
            messages = response.get('Messages', [])
            if not messages:
                print("No new messages. Waiting...")
                continue

            for message in messages:
                # Print message body
                print("New message received:")
                body = json.loads(message['Body'])

                # Extract the message from the data sent.
                fileState = json.loads(body['Message'])

                # Print the parsed message
                print(json.dumps(fileState, indent=4))

                arn = fileState["arn"]
                file_id = fileState["file-id"]
                email = fileState["email"]
                download_file_from_arn(arn, file_id+"-raw"+".mp4")
                print("downloaded complete")


                process_video(file_id+"-raw"+".mp4", file_id)

                s3_key = "processed/" + file_id + "_" + file_id+"-censored.mp4"
                new_arn = upload_file_to_bucket(file_id+"-censored.mp4", bucket_name, s3_key)
                timestamp = datetime.utcnow().isoformat()
                table_name = 'API-DB'
                table = dynamodb.Table(table_name)

                try:
                    # Delete a file based on its ARN
                    delete_file_by_arn(arn)  # Assuming this is already defined

                    response = table.update_item(
                        Key={
                            'file-id': file_id, # Ensure 'file-id' matches exactly and value is a string
                            'email': email
                        },
                        UpdateExpression = "SET ARN = :new_arn, #st = :new_state",
                        ExpressionAttributeValues={
                            ':new_arn': new_arn,  # New value for 'Timestamp' attribute
                            ':new_state': "FINISHED"
                        },
                        ExpressionAttributeNames={
                            '#st': 'State'
                        },
                        ReturnValues="UPDATED_NEW"
                    )

                    print("UpdateItem succeeded:")
                    print(response['Attributes'])

                except (NoCredentialsError, PartialCredentialsError):
                    print("Error: AWS credentials not found.")
                except Exception as e:
                    print(f"Error occurred: {e}")

                # Delete the message from the queue after processing

                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
                print("Message processed and deleted from the queue.")





    except KeyboardInterrupt:
        print("\nStopping the message polling...")

def download_file_from_arn(arn, local_path):
    # Parse the ARN
    arn_parts = arn.split(":::")[1]
    bucket_name, object_key = arn_parts.split("/", 1)

    print(object_key)
    print(bucket_name)
    print(local_path)

    # Download file
    try:
        s3_client.download_file(bucket_name, object_key, local_path)
    except Exception as e:
        print(e)
        return
    print(f"File downloaded to {local_path}")



def upload_file_to_bucket(file_path, bucket_name, s3_key):
    """
    Upload a file to an S3 bucket and return its ARN if successful.

    Args:
        file_path (str): Path to the file to be uploaded.
        bucket_name (str): Name of the S3 bucket.
        s3_key (str): S3 key for the uploaded file.

    Returns:
        str: ARN of the uploaded file.

    Raises:
        Exception: If the upload fails.
    """
    # Initialize S3 client

    try:
        # Upload file
        s3_client.upload_file(file_path, bucket_name, s3_key)

        # Construct the ARN
        arn = f"arn:aws:s3:::{bucket_name}/{s3_key}"
        return arn
    except Exception as e:
        raise Exception(f"Failed to upload file to S3 bucket '{bucket_name}': {str(e)}")


def delete_file_by_arn(arn):
    """
    Delete a file in an S3 bucket using its ARN.

    Args:
        arn (str): The ARN of the file to delete.

    Raises:
        ValueError: If the ARN is invalid or does not match the expected format.
        Exception: If the deletion operation fails.
    """
    # Parse the ARN to extract bucket name and key
    arn_pattern = r"^arn:aws:s3:::(?P<bucket>[^/]+)/(?P<key>.+)$"
    match = re.match(arn_pattern, arn)

    if not match:
        raise ValueError(f"Invalid S3 ARN format: {arn}")

    bucket_name = match.group("bucket")
    s3_key = match.group("key")

    # Initialize S3 client
    s3_client = boto3.client('s3')

    try:
        # Delete the object
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Successfully deleted file: {arn}")
    except Exception as e:
        print(f"Failed to delete file at ARN '{arn}': {str(e)}")

if __name__ == "__main__":
    poll_sqs()
