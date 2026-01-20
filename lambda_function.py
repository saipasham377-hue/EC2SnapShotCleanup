import boto3
import datetime
import os

# Initialize a session using Boto3
session = boto3.Session()

# Get the EC2 resource
ec2 = session.resource('ec2')

def lambda_handler(event, context):
    # Define the number of days before a snapshot should be deleted
    days_to_keep = int(os.environ['DAYS_TO_KEEP'])
    
    # Calculate the date threshold for the snapshots
    threshold_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_keep)
    
    # Retrieve all snapshots
    snapshots = ec2.snapshots.filter(OwnerIds=['self'])
    
    for snapshot in snapshots:
        # Delete snapshots older than the threshold date
        if snapshot.start_time < threshold_date:
            print(f'Deleting snapshot: {snapshot.id}')
            snapshot.delete()
        else:
            print(f'Snapshot {snapshot.id} is within retention period.')