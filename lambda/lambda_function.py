import base64
from app import app


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")

    headers = event.get("headers") or {}

    body = event.get("body", "")

    if event.get("isBase64Encoded", False) and body:
        body = base64.b64decode(body)
    elif isinstance(body, str):
        body = body.encode("utf-8")

    query_string = event.get("rawQueryString", "")

    url = path
    if query_string:
        url += "?" + query_string

    with app.test_client() as client:
        response = client.open(
            path=url,
            method=method,
            headers=headers,
            data=body
        )

    content_type = response.headers.get("Content-Type", "")

    # HTML/JSON/texto se devuelve normalmente
    response_body = response.get_data(as_text=True)

    return {
        "statusCode": response.status_code,
        "headers": {
            "Content-Type": content_type
        },
        "body": response_body,
        "isBase64Encoded": False
    }
