# EC2 Snapshot Automated Cleanup Solution

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Solution Design](#solution-design)
4. [Prerequisites](#prerequisites)
5. [Project Structure](#project-structure)
6. [Infrastructure Setup](#infrastructure-setup)
7. [Lambda Function Deployment](#lambda-function-deployment)
8. [Configuration](#configuration)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Cost Optimization](#cost-optimization)
13. [Security Considerations](#security-considerations)
14. [Maintenance](#maintenance)

---

## Overview

This solution provides an **automated, serverless approach** to managing EC2 snapshots in AWS. It automatically identifies and deletes snapshots that are older than a specified threshold (default: 1 year), helping reduce storage costs and maintain a clean AWS environment.

### Key Features
- ✅ **Fully Automated**: Runs daily on a schedule via EventBridge
- ✅ **VPC-Isolated**: Lambda runs within a VPC for enhanced security
- ✅ **Comprehensive Logging**: Detailed CloudWatch logs of all actions
- ✅ **Error Handling**: Graceful error handling with detailed error messages
- ✅ **Infrastructure as Code**: Complete Terraform implementation
- ✅ **Configurable**:  Easily adjust age threshold, schedule, and other parameters
- ✅ **Cost-Effective**: Serverless architecture with minimal operational overhead
- ✅ **Account-Scoped**: Only deletes snapshots owned by your AWS account

### Cost Savings
- Each snapshot stored in AWS costs approximately $0.05 per GB per month
- For an account with 500 GB of old snapshots, this solution can save **$300/month**
- With the solution cost (Lambda executions) being negligible, the ROI is immediate

---

## Architecture

### System Design Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS Account                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        VPC (10.0.0.0/16)                         │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────────┐ │  │
│  │  │         Public Subnet (10.0.1.0/24)                        │ │  │
│  │  │                                                            │ │  │
│  │  │  ┌─────────────────────────────────────────────────────┐  │ │  │
│  │  │  │  NAT Gateway                                         │  │ │  │
│  │  │  │  (Allows outbound internet access for Lambda)       │  │ │  │
│  │  │  └─────────────────────────────────────────────────────┘  │ │  │
│  │  │                       ▲                                    │ │  │
│  │  │                       │ (Outbound Traffic)                 │ │  │
│  │  └───────────────────────┼────────────────────────────────────┘ │  │
│  │                          │                                       │  │
│  │  ┌───────────────────────┼────────────────────────────────────┐ │  │
│  │  │  Private Subnet (10.0.2.0/24)                             │ │  │
│  │  │                       │                                    │ │  │
│  │  │  ┌──────────────────▼──────────────────────────────────┐ │ │  │
│  │  │  │                                                      │ │ │  │
│  │  │  │  ┌──────────────────────────────────────────────┐   │ │ │  │
│  │  │  │  │  Lambda Function                             │   │ │ │  │
│  │  │  │  │  (snapshot-cleanup)                          │   │ │ │  │
│  │  │  │  │                                              │   │ │ │  │
│  │  │  │  │  • Python Runtime (3.11)                     │   │ │ │  │
│  │  │  │  │  • Memory:  256 MB                            │   │ │ │  │
│  │  │  │  │  • Timeout: 300 seconds                      │   │ │ │  │
│  │  │  │  │                                              │   │ │ │  │
│  │  │  │  │  Actions:                                     │   │ │ │  │
│  │  │  │  │  1.  Describe EC2 Snapshots                  │   │ │ │  │
│  │  │  │  │  2. Filter by Age (>365 days)              │   │ │ │  │
│  │  │  │  │  3. Delete Old Snapshots                    │   │ │ │  │
│  │  │  │  │  4. Log Results to CloudWatch               │   │ │ │  │
│  │  │  │  └──────────────────────────────────────────────┘   │ │ │  │
│  │  │  │                       │                             │ │ │  │
│  │  │  │  ┌────────────────────┴─────────────────────────┐   │ │ │  │
│  │  │  │  │  Security Group (Lambda)                     │   │ │ │  │
│  │  │  │  │  • Egress:  HTTPS (443)                       │   │ │ │  │
│  │  │  │  │  • Egress: DNS (53)                          │   │ │ │  │
│  │  │  │  └──────────────────────────────────────────────┘   │ │ │  │
│  │  │  └──────────────────────────────────────────────────────┘ │ │  │
│  │  │                                                            │ │  │
│  │  └────────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     Internet Gateway                             │  │
│  │                (Routes traffic to AWS APIs)                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      AWS Services (Regional)                            │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  EventBridge │  │  EC2 Service │  │  CloudWatch  │                  │
│  │   (Scheduler)│  │  (Snapshots) │  │    (Logs)    │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                          │
│         │ Triggers Daily  │ API Calls        │ Writes Logs              │
│         │                 │                  │                          │
│         └─────────────────┼──────────────────┘                          │
│                           │                                             │
│                      Lambda Function                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                    IAM Permissions                                       │
│                                                                          │
│  Lambda Role Policy:                                                    │
│  • ec2:DescribeSnapshots  - Read all snapshots                         │
│  • ec2:DeleteSnapshot     - Delete old snapshots                       │
│  • logs:*                 - Write to CloudWatch Logs                   │
│  • ec2:CreateNetworkInterface  - VPC execution permissions             │
│  • ec2:DescribeNetworkInterfaces                                       │
│  • ec2:DeleteNetworkInterface                                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Daily Schedule (EventBridge)
       │
       ▼
┌─────────────────────────────────┐
│ Lambda Function Invoked          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ VPC Network Interface Created    │
│ (via NAT Gateway)               │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Call EC2 API:                    │
│ DescribeSnapshots               │
│ (Filter:  OwnerIds=self)         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Calculate Snapshot Age:         │
│ Current Time - Start Time       │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Filter Snapshots:                │
│ Age > Threshold (365 days)      │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ For Each Old Snapshot:          │
│ Call EC2 API:  DeleteSnapshot    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Log Results to CloudWatch       │
│ • Success count                 │
│ • Failure count                 │
│ • Snapshot details              │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Return Response                 │
│ • Status Code: 200/500          │
│ • Summary Statistics            │
└─────────────────────────────────┘
```

---

## Solution Design

### Why Terraform?

We chose **Terraform** for this solution because:

1. **Multi-Cloud Capability**: Terraform is cloud-agnostic and can be extended to manage infrastructure across AWS, Azure, GCP, etc. 
2. **State Management**: Terraform maintains state files that track infrastructure, allowing safe updates and rollbacks
3. **Modularity**: Easy to create reusable modules for different environments
4. **Version Control**:  Infrastructure code can be stored in git and version controlled
5. **Dependency Management**: Terraform automatically handles resource dependencies
6. **Readability**: HCL (HashiCorp Configuration Language) is human-readable and easy to understand
7. **Active Community**: Large community with extensive modules and providers
8. **Cost**:  Free and open-source

### Alternative:  AWS CloudFormation

CloudFormation is AWS-native and offers:
- Native AWS service integration
- Drift detection
- Better AWS-specific features

However, Terraform is more flexible and easier to manage across multiple environments.

### Key Architecture Components

#### 1. **VPC (Virtual Private Cloud)**
- **CIDR Block**: 10.0.0.0/16
- **Purpose**: Provides network isolation for the Lambda function
- **Benefits**: 
  - Enhanced security
  - Fine-grained network control
  - Compliance with security policies

#### 2. **Public Subnet (10.0.1.0/24)**
- **Purpose**: Houses the NAT Gateway
- **Rationale**: 
  - NAT Gateway requires public subnet placement
  - Allows private resources to access the internet securely

#### 3. **Private Subnet (10.0.2.0/24)**
- **Purpose**: Hosts the Lambda function
- **Security Advantages**:
  - Lambda has no inbound internet access
  - Only outbound access through NAT Gateway
  - Enhanced security posture

#### 4. **NAT Gateway**
- **Purpose**: Enables Lambda to make outbound API calls while remaining private
- **Why Needed**: EC2 API calls are outbound; Lambda needs internet access through a controlled gateway
- **Cost**: ~$0.045/hour + data transfer

#### 5. **Security Group**
- **Egress Rules**:
  - HTTPS (443): For EC2 API calls
  - DNS (53): For DNS resolution
- **Ingress Rules**:  None (no inbound access needed)

#### 6. **IAM Role and Policies**
- **EC2 Snapshot Permissions**: DescribeSnapshots, DeleteSnapshot
- **CloudWatch Permissions**: Create logs, write logs
- **VPC Execution**:  Network interface management
- **Principle of Least Privilege**: Only permissions needed for the function

#### 7. **Lambda Function**
- **Runtime**: Python 3.11 (latest stable)
- **Memory**: 256 MB (sufficient for API calls)
- **Timeout**: 300 seconds (5 minutes for full scan)
- **VPC Configuration**: Private subnet + Security Group

#### 8. **EventBridge Schedule Rule**
- **Trigger**: Daily at 2 AM UTC
- **Cron Expression**: `cron(0 2 * * ? *)`
- **Advantages**:
  - More flexible than CloudWatch Events
  - Better integration with modern AWS services
  - Supports various schedule patterns

#### 9. **CloudWatch Logs**
- **Log Group**: `/aws/lambda/snapshot-cleanup-*`
- **Retention**: 30 days
- **Monitoring**: All function execution details

---

## Prerequisites

### Software Requirements
- **Terraform**: >= 1.0
  - Installation: https://www.terraform.io/downloads.html
- **AWS CLI**: >= 2.0
  - Installation: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- **Python**:  >= 3.9 (for local testing)
- **Git**: For version control

### AWS Account Requirements
- Active AWS account with billing enabled
- Permissions to create: 
  - VPC and subnets
  - NAT Gateway
  - Security Groups
  - IAM roles and policies
  - Lambda functions
  - CloudWatch resources
  - EventBridge rules

### AWS Credentials Configuration
```bash
# Option 1: Using AWS CLI
aws configure

# Option 2: Using environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option 3: Using AWS credentials file (~/.aws/credentials)
[default]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key
```

### IAM Permissions Required (Minimum)
```json
{
  "Version": "2012-10-17",
  "Statement":  [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "iam:*",
        "lambda:*",
        "logs: *",
        "events:*",
        "cloudwatch:*"
      ],
      "Resource":  "*"
    }
  ]
}
```

---

## Project Structure

```
snapshot-cleanup-project/
│
├── main.tf                 # Primary Terraform configuration
├── variables.tf            # Terraform variable definitions
├── outputs.tf              # Terraform outputs
├── terraform.tfvars        # Variable values (optional, for overrides)
├── lambda_function.py      # Python Lambda function code
├── . gitignore              # Git ignore file
├── README.md              # This file
├── DEPLOYMENT.md          # Detailed deployment guide
└── ARCHITECTURE.md        # Detailed architecture documentation
```

### File Descriptions

| File | Purpose |
|------|---------|
| `main.tf` | Contains VPC, subnet, security group, NAT, Lambda, IAM, and EventBridge configurations |
| `variables.tf` | Defines configurable parameters with defaults and descriptions |
| `outputs.tf` | Specifies outputs after Terraform apply |
| `lambda_function.py` | Python code executed by the Lambda function |
| `terraform.tfvars` | Optional file to override default variable values |

---

## Infrastructure Setup

### Step 1: Prepare Your Environment

```bash
# Clone or create your project directory
mkdir snapshot-cleanup-project
cd snapshot-cleanup-project

# Initialize Git (optional but recommended)
git init

# Copy all the provided files to this directory
# - main.tf
# - variables. tf
# - outputs.tf
# - lambda_function.py
# - README.md
```

### Step 2: Configure Terraform

#### Option A: Using Default Values

```bash
# Initialize Terraform
terraform init

# Review the plan (no changes made yet)
terraform plan

# This will show all resources that will be created
```

#### Option B: Using Custom Values

Create a `terraform.tfvars` file:

```hcl
aws_region           = "us-west-2"
project_name         = "my-snapshot-cleanup"
environment          = "production"
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidr   = "10.0.1.0/24"
private_subnet_cidr  = "10.0.2.0/24"
snapshot_age_days    = 365
log_retention_days   = 30
schedule_expression  = "cron(0 2 * * ? *)"
```

Then apply:
```bash
terraform plan -var-file="terraform.tfvars"
```

### Step 3: Review Infrastructure Plan

```bash
# Generate and review the plan
terraform plan -out=tfplan

# This will display: 
# - All resources to be created
# - Resource properties
# - Terraform will ask for confirmation to proceed
```

**Expected Resources (12 total)**:
1. VPC
2. Public Subnet
3. Private Subnet
4. Internet Gateway
5. NAT Gateway
6. NAT Gateway Elastic IP
7. Public Route Table
8. Private Route Table
9. Route Table Associations (2)
10. Security Group
11. IAM Role
12. IAM Policies (2)
13. Lambda Function
14. CloudWatch Log Group
15. EventBridge Rule
16. EventBridge Target
17. Lambda Permission

### Step 4: Deploy Infrastructure

```bash
# Apply the Terraform configuration
terraform apply tfplan

# Or directly (will prompt for confirmation)
terraform apply

# Type 'yes' when prompted

# Output example:
# Apply complete! Resources:  17 added, 0 changed, 0 destroyed. 
#
# Outputs:
# lambda_function_name = "snapshot-cleanup-snapshot-cleanup"
# vpc_id = "vpc-0a1b2c3d4e5f6g7h8"
# private_subnet_id = "subnet-0a1b2c3d4e5f6g7h8"
# ... 
```

### Step 5: Verify Deployment

```bash
# List created resources
terraform show

# Get specific output values
terraform output lambda_function_name
terraform output vpc_id
terraform output private_subnet_id
terraform output security_group_id

# Verify in AWS Console
# Navigate to: 
# - EC2 > VPCs (check VPC creation)
# - EC2 > Subnets (check subnet creation)
# - Lambda > Functions (check function creation)
# - CloudWatch > Rules (check EventBridge rule)
```

### Step 6: Verify Lambda Configuration

```bash
# Get Lambda function details
aws lambda get-function \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --region us-east-1

# Check Lambda VPC configuration
aws lambda get-function-configuration \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --region us-east-1 \
  --query 'VpcConfig'

# Expected output:
# {
#     "SubnetIds": ["subnet-xxxxx"],
#     "SecurityGroupIds":  ["sg-xxxxx"]
# }
```

---

## Lambda Function Deployment

### How Lambda Deployment Works

Terraform automatically: 
1. Archives the `lambda_function.py` file
2. Creates a ZIP file with the function code
3. Uploads it to AWS
4. Creates the Lambda function with specified configuration

### Manual Deployment (Alternative)

If you need to update only the Lambda function code:

```bash
# 1. Update lambda_function.py

# 2. Recreate the deployment package
zip lambda_function.zip lambda_function. py

# 3. Update the Lambda function
aws lambda update-function-code \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --zip-file fileb://lambda_function.zip \
  --region us-east-1

# 4. Verify the update
aws lambda get-function-configuration \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --region us-east-1
```

### Function Code Explanation

#### Main Handler:  `lambda_handler(event, context)`

```python
def lambda_handler(event, context):
    # Entry point for Lambda invocation
    # Called by EventBridge on schedule
```

**Parameters**:
- `event`: Contains data passed to Lambda (EventBridge passes schedule info)
- `context`: Runtime information (request ID, function name, remaining time)

**Return Value**:
```json
{
  "statusCode":  200,
  "body":  {
    "message": "Snapshot cleanup completed successfully",
    "region": "us-east-1",
    "summary": {
      "total_snapshots": 10,
      "successfully_deleted": 8,
      "failed_deletions": 2,
      "deleted_snapshots": [... ],
      "failed_snapshots": [...]
    },
    "timestamp": "2026-01-20T14:30:00+00:00"
  }
}
```

#### Key Functions:

1. **`get_snapshot_age_in_days(snapshot_start_time)`**
   - Calculates snapshot age
   - Handles timezone-aware datetime objects
   - Returns age in days

2. **`get_old_snapshots(age_threshold_days)`**
   - Retrieves all snapshots owned by the account
   - Uses pagination for accounts with many snapshots
   - Filters snapshots older than threshold
   - Returns list of old snapshot objects

3. **`delete_snapshot(snapshot_id)`**
   - Attempts to delete a single snapshot
   - Handles various exception types: 
     - `InvalidSnapshot.NotFound`: Snapshot already deleted
     - `InvalidSnapshotInUse`: Snapshot in use (cannot delete)
     - Generic exceptions:  Unknown errors
   - Returns tuple: (success:  bool, message: str)

4. **`delete_old_snapshots(snapshots)`**
   - Iterates through old snapshots
   - Attempts deletion of each
   - Tracks successes and failures
   - Returns summary dictionary

### Environment Variables

Configured in Terraform `aws_lambda_function` block:

| Variable | Value | Purpose |
|----------|-------|---------|
| `SNAPSHOT_AGE_DAYS` | 365 | Age threshold in days |
| `AWS_REGION` | us-east-1 | Target AWS region |
| `PROJECT_NAME` | snapshot-cleanup | Used in logging |

**Modify in Terraform**:
```hcl
environment {
  variables = {
    SNAPSHOT_AGE_DAYS = 180  # Change to 6 months
    AWS_REGION        = "us-west-2"
    PROJECT_NAME      = "my-cleanup"
  }
}
```

---

## Configuration

### Customizing the Solution

#### 1. Change Snapshot Age Threshold

**In Terraform** (`variables.tf` or `terraform.tfvars`):
```hcl
variable "snapshot_age_days" {
  default = 180  # 6 months instead of 1 year
}
```

**Re-apply**:
```bash
terraform apply
```

#### 2. Change Execution Schedule

**In Terraform** (`variables.tf`):
```hcl
variable "schedule_expression" {
  # Run every Sunday at 3 AM UTC
  default = "cron(0 3 ?  * SUN *)"
  
  # Other examples:
  # Every day at 2 AM UTC:  "cron(0 2 * * ? *)"
  # Every 6 hours: "rate(6 hours)"
  # Every Monday and Thursday at 1 AM: "cron(0 1 ?  * MON,THU *)"
}
```

**Cron Expression Format**:
```
cron(minutes hours day month ?  day-of-week year)
     0       2     *   *     ?      *            *

?  = any value (used for day and day-of-week to avoid conflict)
* = every value
```

#### 3. Change Lambda Memory and Timeout

**In Terraform** (`main.tf`):
```hcl
resource "aws_lambda_function" "snapshot_cleanup" {
  memory_size = 512    # Increase from 256
  timeout     = 600    # Increase from 300 seconds
}
```

#### 4. Change VPC CIDR Blocks

**In Terraform** (`terraform.tfvars`):
```hcl
vpc_cidr             = "10.1.0.0/16"
public_subnet_cidr   = "10.1.1.0/24"
private_subnet_cidr  = "10.1.2.0/24"
```

#### 5. Deploy in Different Region

**In Terraform**:
```bash
terraform apply -var="aws_region=eu-west-1"
```

Or in `terraform.tfvars`:
```hcl
aws_region = "eu-west-1"
```

### Lambda Permissions

The Lambda role has the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2SnapshotPermissions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSnapshots",
        "ec2:DeleteSnapshot"
      ],
      "Resource":  "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn: aws:logs:region:account:log-group:/aws/lambda/snapshot-cleanup-*"
    },
    {
      "Sid": "VPCExecutionPolicy",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource":  "*"
    }
  ]
}
```

**Explanation**:
- `ec2:DescribeSnapshots`: Read-only permission to list snapshots
- `ec2:DeleteSnapshot`: Permission to delete snapshots
- CloudWatch Logs permissions: Write execution logs
- VPC permissions: Create/manage ENIs (Elastic Network Interfaces) for Lambda

### Sensitive Information Management

**Best Practices**: 

1. **Never commit AWS credentials**: 
```bash
# Add to .gitignore
echo ". aws/" >> .gitignore
echo "*. tfvars" >> .gitignore
echo "*.key" >> .gitignore
```

2. **Use AWS Secrets Manager** (Advanced):
```hcl
# Retrieve secrets in Lambda code
import json
import boto3

secrets_client = boto3.client('secretsmanager')

def get_secret(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

3. **Use IAM Roles** (Recommended):
```hcl
# Lambda automatically assumes the IAM role
# No need to hardcode credentials
```

---

## Monitoring and Logging

### CloudWatch Logs

#### Accessing Logs

```bash
# Method 1: AWS CLI
aws logs tail /aws/lambda/snapshot-cleanup-snapshot-cleanup --follow

# Method 2: AWS Console
# Navigate to CloudWatch > Logs > Log groups > /aws/lambda/snapshot-cleanup-*

# Method 3: Filter logs for specific date
aws logs filter-log-events \
  --log-group-name /aws/lambda/snapshot-cleanup-snapshot-cleanup \
  --start-time $(date -d '1 day ago' +%s)000 \
  --end-time $(date +%s)000
```

#### Log Examples

**Successful Execution**:
```
[INFO] Starting snapshot cleanup for region us-east-1
[INFO] Snapshot age threshold: 365 days
[INFO] Event received:  {}
[INFO] Fetching snapshots older than 365 days from region us-east-1
[INFO] Found old snapshot: snap-0123456789abcdef0 - Age: 400 days, Size: 100 GB, Created: 2024-12-15T10:30:00+00:00
[INFO] Total old snapshots found: 3
[INFO] Attempting to delete snapshot:  snap-0123456789abcdef0
[INFO] Successfully deleted snapshot: snap-0123456789abcdef0
[INFO] Snapshot cleanup summary:  {... }
```

**Error Handling**:
```
[ERROR] Error deleting snapshot snap-0123456789abcdef1: 
InvalidSnapshotInUse: The Snapshot 'snap-0123456789abcdef1' is currently in use by an AMI
```

### CloudWatch Metrics

#### Default Metrics

EventBridge automatically creates:
- `Rules` invocations
- `FailedInvocations`
- `Invocations`

Lambda automatically creates:
- `Invocations`: Total function invocations
- `Errors`: Function errors
- `Duration`: Execution time (ms)
- `Throttles`: Function throttles

#### Custom Metrics (Optional Enhancement)

Add to Lambda code:
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_metric(metric_name, value):
    cloudwatch.put_metric_data(
        Namespace='SnapshotCleanup',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value':  value,
                'Unit': 'Count'
            }
        ]
    )

# Usage in lambda_handler
put_metric('SnapshotsDeleted', summary['successfully_deleted'])
put_metric('SnapshotsDeletionFailed', summary['failed_deletions'])
```

#### Viewing Metrics

```bash
# CLI
aws cloudwatch list-metrics \
  --namespace AWS/Lambda \
  --metric-name Invocations

# Console
# CloudWatch > Metrics > AWS/Lambda
```

### CloudWatch Alarms (Optional)

Create an alarm for Lambda failures:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name snapshot-cleanup-failures \
  --alarm-description "Alert when snapshot cleanup fails" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1
```

Or in Terraform:
```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "snapshot-cleanup-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.alerts. arn]
}
```

### Logging Best Practices

1. **Use structured logging**:
```python
import logging
import json

logger = logging. getLogger()
logger.setLevel(logging.INFO)

# Structured log format
logger.info(json.dumps({
    'action': 'delete_snapshot',
    'snapshot_id': 'snap-xxx',
    'status': 'success',
    'age_days': 400
}))
```

2. **Include context**:
```python
logger.info(f"Processing snapshot {snapshot_id} (Age: {age} days, Size: {size} GB)")
```

3. **Handle errors properly**:
```python
try:
    # Do something
except Exception as e:
    logger. error(f"Operation failed: {str(e)}", exc_info=True)
```

### Monitoring Dashboard (Optional)

Create a CloudWatch Dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name SnapshotCleanup \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
            [".", "Errors", {"stat": "Sum"}],
            [".", "Duration", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Lambda Metrics"
        }
      }
    ]
  }'
```

---

## Testing

### Manual Testing

#### Test 1: Manual Lambda Invocation

```bash
# Invoke Lambda directly
aws lambda invoke \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --region us-east-1 \
  --log-type Tail \
  response.json

# View response
cat response.json | jq . 

# View logs from invocation
aws lambda invoke \
  --function-name snapshot-cleanup-snapshot-cleanup \
  --region us-east-1 \
  --log-type Tail \
  response.json \
  --query 'LogResult' \
  --output text | base64 -d
```

#### Test 2: Check EventBridge Rule

```bash
# Verify rule is enabled
aws events describe-rule \
  --name snapshot-cleanup-snapshot-cleanup-schedule \
  --region us-east-1

# List targets
aws events list-targets-by-rule \
  --rule snapshot-cleanup-snapshot-cleanup-schedule \
  --region us-east-1
```

#### Test 3: Test with Dry Run

Modify Lambda code to not delete (for testing):

```python
# In lambda_function.py, modify delete_snapshot function: 

def delete_snapshot(snapshot_id:  str) -> Tuple[bool, str]:
    try:
        logger.info(f"[DRY RUN] Would delete snapshot: {snapshot_id}")
        # Comment out actual deletion for testing
        # ec2_client.delete_snapshot(SnapshotId=snapshot_id)
        return True, f"[DRY RUN] Would delete:  {snapshot_id}"
    except Exception as e:
        ... 
```

#### Test 4: Verify VPC Configuration

```bash
# Check Lambda VPC configuration
aws ec2 describe-network-interfaces \
  --filters "Name=description,Values=AWS Lambda VPC ENI*" \
  --region us-east-1

# Verify subnet
aws ec2 describe-subnets \
  --subnet-ids subnet-xxxxx \
  --region us-east-1
```

### Testing Checklist

- [ ] Terraform plan shows all expected resources
- [ ] Terraform apply completes successfully
- [ ] Lambda function is created with correct VPC configuration
- [ ] EventBridge rule is created and enabled
- [ ] IAM role has correct permissions
- [ ] Manual Lambda invocation succeeds
- [ ] CloudWatch logs appear after invocation
- [ ] EventBridge triggers Lambda on schedule
- [ ] Lambda successfully deletes old snapshots
- [ ] Error handling works for edge cases

### Load Testing (Advanced)

For accounts with many snapshots:

```python
# Test pagination
# Lambda includes pagination to handle large numbers of snapshots
# Verify with: 

aws ec2 describe-snapshots \
  --owner-ids self \
  --max-results 100 \
  --region us-east-1

# Check total count
aws ec2 describe-snapshots \
  --owner-ids self \
  --region us-east-1 \
  --query 'length(Snapshots)'
```

---

## Troubleshooting

### Issue 1: Lambda Cannot Access EC2 API

**Symptoms**:
- "Unable to locate credentials"
- "An error occurred (UnauthorizedOperation)"

**Solutions**: 

```bash
# Check IAM role
aws iam get-role --role-name snapshot-cleanup-lambda-role

# Check IAM role policies
aws iam list-role-policies --role-name snapshot-cleanup-lambda-role

# Check Lambda execution role configuration
aws lambda get-function-configuration \
  --function-name snapshot-cleanup-snapshot-cleanup | grep Role
```

**Fix**:
```bash
# Re-apply Terraform to fix policies
terraform apply -auto-approve
```

### Issue 2: Lambda Cannot Access Network

**Symptoms**:
- "Task timed out after 300 seconds"
- "Unable to connect to endpoint"

**Causes & Solutions**:

```bash
# 1. Check NAT Gateway status
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=vpc-xxxxx \
  --region us-east-1

# 2. Verify security group egress rules
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --region us-east-1 \
  --query 'SecurityGroups[0].IpPermissionsEgress'

# 3. Check route table
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-xxxxx \
  --region us-east-1
```

**Fix**:
```bash
# Ensure NAT Gateway has Elastic IP
aws ec2 describe-nat-gateways --region us-east-1

# Ensure route table has route to NAT
aws ec2 describe-route-tables --region us-east-1
