import boto3
from boto3.session import Session
import botocore
import os
import sys


class Client():
    """A boto3 client"""
    def __init__(self,
                 aws_access_key,
                 aws_secret_key,
                 aws_region,
                 aws_role_arn=False,
                 client_type='ec2',
                 role_session_name='github-copy-ami'
                 ):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.aws_region = aws_region
        self.aws_role_arn = aws_role_arn
        self.client_type = client_type
        self.role_session_name = role_session_name

    def create(self):
        """Create a boto3 client"""

        # use a role to setup the client
        if self.aws_role_arn:
            try:
                target_client = boto3.client(
                    'sts',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region)

                response = target_client.assume_role(
                    RoleArn=self.aws_role_arn,
                    RoleSessionName=self.role_session_name
                )
            except botocore.exceptions.ClientError as e:
                sys.exit(e)

            session = Session(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken']
            )

            client = session.client(
                self.client_type,
                region_name=self.aws_region
            )

        else:
            client = boto3.client(
                self.client_type,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )

        return client


def main():

    source_ami_id = os.environ["INPUT_SOURCE_AMI_ID"]
    source_aws_access_key = os.environ["INPUT_SOURCE_AWS_ACCESS_KEY"]
    source_aws_secret_key = os.environ["INPUT_SOURCE_AWS_SECRET_KEY"]
    source_aws_region = os.environ["INPUT_SOURCE_AWS_REGION"]
    target_aws_access_key = os.environ["INPUT_TARGET_AWS_ACCESS_KEY"]
    target_aws_secret_key = os.environ["INPUT_TARGET_AWS_SECRET_KEY"]
    target_aws_region = os.environ["INPUT_TARGET_AWS_REGION"]
    target_kms_key = os.environ["INPUT_TARGET_KMS_KEY"]
    delete_on_copy = os.environ["INPUT_DELETE_ON_COPY"]

    if 'INPUT_TARGET_AMI_NAME' in os.environ:
        target_ami_name = os.environ["INPUT_TARGET_AMI_NAME"]
    else:
        target_ami_name = False

    if 'INPUT_TARGET_AMI_DESCRIPTION' in os.environ:
        target_ami_description = os.environ["INPUT_TARGET_AMI_DESCRIPTION"]
    else:
        target_ami_description = 'copy'

    if 'INPUT_SOURCE_AWS_ROLE_ARN' in os.environ:
        source_aws_role_arn = os.environ["INPUT_SOURCE_AWS_ROLE_ARN"]
    else:
        source_aws_role_arn = False

    if 'INPUT_TARGET_AWS_ROLE_ARN' in os.environ:
        target_aws_role_arn = os.environ["INPUT_TARGET_AWS_ROLE_ARN"]
    else:
        target_aws_role_arn = False

    # configure a target client
    target_client = Client(
        aws_access_key=target_aws_access_key,
        aws_secret_key=target_aws_secret_key,
        aws_region=target_aws_region,
        aws_role_arn=target_aws_role_arn,
        client_type='ec2',
        role_session_name='github-target-ami'
    ).create()

    # configure a source client
    source_client = Client(
        aws_access_key=source_aws_access_key,
        aws_secret_key=source_aws_secret_key,
        aws_region=source_aws_region,
        aws_role_arn=source_aws_role_arn,
        client_type='ec2',
        role_session_name='github-source-ami'
    ).create()

    # get info on source image
    try:
        response = source_client.describe_images(
            ImageIds=[source_ami_id]
        )
    except botocore.exceptions.ClientError as e:
        sys.exit(e)

    source_image_name = response['Images'][0]['Name']
    source_image_tags = response['Images'][0]['Tags']
    source_ebs_volumes = response['Images'][0]['BlockDeviceMappings']

    # Initiate a copy of the AMI using target account creds
    print('Initiating AMI copy')

    # use a new name if provided otherwise use the source ami name
    new_ami_name = target_ami_name if target_ami_name else source_image_name

    try:
        response = target_client.copy_image(
            Description=target_ami_description,
            Encrypted=True,
            KmsKeyId=target_kms_key,
            Name=new_ami_name,
            SourceImageId=source_ami_id,
            SourceRegion=source_aws_region
        )
    except botocore.exceptions.ClientError as e:
        sys.exit(e)

    ami_id = response['ImageId']

    # wait for the copy operation to complete
    print(f"Waiting for {ami_id} to become available.")
    waiter = target_client.get_waiter('image_available')
    waiter.wait(
        ImageIds=[ami_id],
    )

    # set the same tags on copied image
    # update the AMI tag to production
    try:
        response = target_client.create_tags(
            Resources=[
                ami_id
            ],
            Tags=source_image_tags
        )
    except botocore.exceptions.ClientError as e:
        sys.exit(e)

    # optionally delete source image
    if delete_on_copy == 'True':
        print('Deleting source AMI')
        try:
            response = source_client.deregister_image(
                ImageId=source_ami_id
            )
        except botocore.exceptions.ClientError as e:
            sys.exit(e)

        print('Deleting source AMI snapshots')
        for volume in source_ebs_volumes:
            if 'Ebs' in volume:
                try:
                    response = source_client.delete_snapshot(
                        SnapshotId=volume['Ebs']['SnapshotId']
                    )
                except botocore.exceptions.ClientError as e:
                    sys.exit(e)

    # set GitHub Action output variables
    print(f"::set-output name=ami_id::{ami_id}")
    print(f"::set-output name=ami_name::{target_ami_name}")


if __name__ == "__main__":
    main()
