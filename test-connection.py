import os
import boto3
import openai
from dotenv import load_dotenv

def test_aws_connection():
    print("Testing AWS Connection...")
    try:
        # Create an S3 client
        s3 = boto3.client('s3')
        
        # List S3 buckets to test connection
        response = s3.list_buckets()
        
        # Print the bucket names
        print("Connection successful! Available S3 buckets:")
        for bucket in response['Buckets']:
            print(f"- {bucket['Name']}")
        
        return True
    except Exception as e:
        print(f"AWS Connection failed: {e}")
        return False

def test_openai_connection():
    print("\nTesting OpenAI Connection...")
    try:
        # Set up the OpenAI client
        client = openai.OpenAI()
        
        # Make a simple API call to test the connection
        models = client.models.list()
        
        # Print available models
        print("Connection successful! Available models:")
        model_count = 0
        for model in models.data:
            print(f"- {model.id}")
            model_count += 1
            if model_count >= 5:  # Limit to 5 models to avoid clutter
                print("- ...")
                break
        
        return True
    except Exception as e:
        print(f"OpenAI Connection failed: {e}")
        return False

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    print("Environment Variables Test")
    print("--------------------------")
    
    # Check if required environment variables are set
    aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_DEFAULT_REGION')
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    print(f"AWS_ACCESS_KEY_ID: {'✓ Set' if aws_key else '✗ Not set'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✓ Set' if aws_secret else '✗ Not set'}")
    print(f"AWS_DEFAULT_REGION: {'✓ Set' if aws_region else '✗ Not set'}")
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set'}")
    
    print("\nConnection Tests")
    print("----------------")
    
    # Test connections
    aws_success = test_aws_connection()
    openai_success = test_openai_connection()
    
    # Summary
    print("\nConnection Test Summary")
    print("----------------------")
    print(f"AWS Connection: {'✓ Success' if aws_success else '✗ Failed'}")
    print(f"OpenAI Connection: {'✓ Success' if openai_success else '✗ Failed'}")

if __name__ == "__main__":
    main()
