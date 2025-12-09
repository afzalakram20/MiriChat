try:
    import boto3
    print("boto3 is available")
except ImportError:
    print("boto3 is NOT available")
