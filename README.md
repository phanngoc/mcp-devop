# Advanced AWS Integration MCP Server

This project provides a powerful AWS integration server using Claude MCP (Model Control Protocol) capabilities. It allows you to interact with AWS services directly through Claude, accessing AWS resources and tools.

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the root directory with your AWS credentials and configuration:

```
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
# AWS_SESSION_TOKEN=your_session_token_here

# AWS Advanced Configuration (Uncomment as needed)
# AWS_PROFILE=default
# AWS_CONFIG_FILE=~/.aws/config
# AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials
# AWS_STS_REGIONAL_ENDPOINTS=regional
# AWS_RETRY_MODE=standard
# AWS_MAX_ATTEMPTS=5

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Running the Server

#### Option 1: Run Directly

```bash
python advanced_server.py
```

#### Option 2: Use the Streamlit Interface

```bash
streamlit run advanced_app.py
```

## Available AWS Services

The MCP server integrates with the following AWS services:

- **S3**: List buckets, objects, and access S3 content
- **DynamoDB**: Query tables and access items
- **CloudWatch**: View metrics and alarms
- **Lambda**: List functions and view configurations
- **EC2**: List instances and check status
- **IAM**: List roles and policies

## MCP Resource URLs

Access AWS resources using MCP resource URLs:

- S3: `s3://{bucket}/{key}`
- DynamoDB: `dynamodb://{table}/{key_name}/{key_value}`
- CloudWatch: `cloudwatch://{namespace}/{metric_name}/{period}`
- Lambda: `lambda://{function_name}`
- EC2: `ec2://{instance_id}`
- IAM: `iam://{role_name}`

## Environment Variables

The application uses the following environment variables, loaded via python-dotenv:

| Variable | Description | Default |
|----------|-------------|---------|
| AWS_DEFAULT_REGION | AWS region to use | us-east-1 |
| AWS_ACCESS_KEY_ID | AWS access key ID | - |
| AWS_SECRET_ACCESS_KEY | AWS secret access key | - |
| AWS_SESSION_TOKEN | AWS session token for temporary credentials | - |
| AWS_PROFILE | AWS profile name to use | default |
| AWS_CONFIG_FILE | Path to AWS config file | ~/.aws/config |
| AWS_SHARED_CREDENTIALS_FILE | Path to AWS credentials file | ~/.aws/credentials |
| AWS_STS_REGIONAL_ENDPOINTS | STS endpoint resolution logic | legacy |
| AWS_RETRY_MODE | Type of retries | legacy |
| AWS_MAX_ATTEMPTS | Maximum number of attempts for requests | - |
| DEBUG | Enable debug mode | True |
| LOG_LEVEL | Logging level | INFO |