# Copy AMI GitHub Action

The purpose of this action is to copy encrypted AMIs from one AWS account to another.

## Usage

This action is typically used in the deployment part of a workflow. It's important to note that this action uses
credentials from both a source and target AWS account.

### Example workflow

```yaml
name: My Workflow
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Copy AMI
      uses: exosite/ops-github-copy-ami@v1

      with:
        source_ami_id: 'ami-12873817823'
        source_aws_access_key: ${{ secret }}
        source_aws_secret_key: ${{ secret }}
        source_aws_region: 'us-west-2'
        target_ami_name: 'AMI-NAME'
        target_aws_region: 'us-west-1'
        target_aws_access_key: ${{ secret }}
        target_aws_secret_key: ${{ secret }}
        target_kms_key: 'arn:aws:kms:us-west-2:26376172632:key/278873123-2f55-2381-2991-41bb28ef5b36'


```

### Inputs

| Input                                             | Description                                        |
|------------------------------------------------------|-----------------------------------------------|
| `source_ami_id`                   | The AMI ID to copy                                      |
| `source_aws_access_key`      | An AWS access key credential for the source account       |
| `source_aws_secret_key`      | An AWS secret access key credential for the source account|
| `source_aws_region`          | The AWS region where the source AMI is located            |
| `source_aws_role_arn` _(optional)_  | An optional AWS role to assume for the source account     |
| `target_ami_name` _(optional)_   | Optional name to assign the new AMI                |
| `target_ami_description` _(optional)_  | The new AMI description                |
| `target_aws_access_key`      | An AWS access key credential for the target account       |
| `target_aws_secret_key`      | An AWS secret access key credential for the target account|
| `target_aws_region`          | The target AWS region to copy the AMI to                      |
| `target_aws_role_arn` _(optional)_  | An optional AWS role to assume for the target account     |
| `target_kms_key`             | A KMS Key ID for the target AWS account                   |
| `delete_on_copy`  _(optional)_  | Optionally delete source AMI after copying to new account (defaults to False|

### Outputs

| Output                                             | Description                                        |
|------------------------------------------------------|-----------------------------------------------|
| `ami_id`   | The ID of the new AMI which created from the copy    |
| `ami_name`   | The name of the new AMI copy    |

