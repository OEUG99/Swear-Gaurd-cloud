import boto3
from datetime import datetime
import uuid
import json

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Configuration
file_path = 'test-video.mp4'
file_id = str(uuid.uuid4())
bucket_name = 'applebananatest123'
s3_key = "raw/" + file_id + "_" +  file_path
table_name = 'API-DB'
topic_arn = 'arn:aws:sns:us-east-1:812477365003:FileStateChange'  # Replace with your topic ARN

try:
    # Upload to S3
    s3_client.upload_file(file_path, bucket_name, s3_key)
    print(f'File uploaded successfully to {bucket_name}/{s3_key}')

    # Store file metadata in DynamoDB
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat()
    arn = f"arn:aws:s3:::{bucket_name}/{s3_key}"

    table.put_item(
        Item={
            'file-id': file_id,
            'email': "oli@eugenio.software",
            'State': 'unedited',
            'ARN': arn,
            'Timestamp': timestamp
        }
    )
    print(f'Metadata stored successfully in DynamoDB table: {table_name}')

    # Publish an event to the SNS topic
    message_body = {
        'file-id': file_id,
        'email': "oli@eugenio.software",
        'state': 'unedited',
        'arn': arn,
        'timestamp': timestamp
    }

    response = sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message_body),  # Message body as JSON string
        Subject="FileUploaded",  # Optional, used for email subscribers
        MessageAttributes={
            'EventType': {
                'DataType': 'String',
                'StringValue': 'FileUploaded'
            }
        }
    )
    print(f'Event published to SNS Topic ({topic_arn}). Message ID: {response["MessageId"]}')

except Exception as e:
    print(f'Error occurred: {e}')
