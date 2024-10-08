import json

def create_response(message):
    """Helper function to create a standardized HTTP response."""
    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
    }

def health(event, context):
    """Health check endpoint."""
    return create_response("Go Serverless v3.0! Your function executed successfully!")

def v1_description(event, context):
    """API version 1 description."""
    return create_response("VISION API version 1.")

def v2_description(event, context):
    """API version 2 description."""
    return create_response("VISION API version 2.")
