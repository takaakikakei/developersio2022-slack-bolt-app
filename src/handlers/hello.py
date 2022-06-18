import json


def handler(event, context):
    body = {
        "message": "Your function executed successfully!",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
