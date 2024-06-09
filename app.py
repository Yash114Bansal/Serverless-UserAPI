import os
import re
import uuid
import boto3
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)


dynamodb_client = boto3.client("dynamodb")

if os.environ.get("IS_OFFLINE"):
    dynamodb_client = boto3.client(
        "dynamodb", region_name="localhost", endpoint_url="http://localhost:8000"
    )


USERS_TABLE = os.environ["USERS_TABLE"]
MANAGERS_TABLE = os.environ["MANAGERS_TABLE"]


def is_valid_mobile(mob_num):
    return bool(re.match(r"[789]\d{9}$", mob_num))


def is_valid_pan(pan_num):
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan_num))

def dynamodb_to_dict(item):
    if not item:
        return None
    return {k: list(v.values())[0] for k, v in item.items()}

@app.route("/create_user", methods=["POST"])
def create_user():
    data = request.get_json()

    full_name = data.get("full_name")
    mob_num = data.get("mob_num")
    pan_num = data.get("pan_num")
    manager_id = data.get("manager_id")

    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    
    if not mob_num:
        return jsonify({"error": "Mobile number is required"}), 400
    
    if not pan_num:
        return jsonify({"error": "Pan number is required"}), 400

    pan_num = pan_num.upper()
    
    mob_num = mob_num.removeprefix("0").removeprefix("+91").strip()

    if not is_valid_mobile(mob_num):
        return jsonify({"error": "Invalid mobile number"}), 400

    if not is_valid_pan(pan_num):
        return jsonify({"error": "Invalid PAN number"}), 400

    if manager_id:
        response = dynamodb_client.get_item(
            TableName=MANAGERS_TABLE, Key={"manager_id": {"S": manager_id}}
        )
        if "Item" not in response:
            return jsonify({"error": "Invalid manager_id"}), 400

    user_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    dynamodb_client.put_item(
        TableName=USERS_TABLE,
        Item={
            "user_id": {"S": user_id},
            "full_name": {"S": full_name},
            "mob_num": {"S": mob_num},
            "pan_num": {"S": pan_num},
            "manager_id": {"S": manager_id} if manager_id else {"NULL": True},
            "created_at": {"S": created_at},
            "updated_at": {"S": created_at},
            "is_active": {"BOOL": True},
        },
    )
    return jsonify({"message": "User created successfully"}), 201


@app.route("/get_users", methods=["POST"])
def get_users():
    data = request.get_json(silent=True)
    if data is None:
        data = {}

    user_id = data.get("user_id")
    mob_num = data.get("mob_num")
    manager_id = data.get("manager_id")

    if user_id:
        response = dynamodb_client.get_item(TableName=USERS_TABLE, Key={"user_id": {"S": user_id}})
        if "Item" in response:
            return jsonify({"users": [response["Item"]]}), 200
        else:
            return jsonify({"users": []}), 200

    if mob_num:
        response = dynamodb_client.scan(
            TableName=USERS_TABLE,
            FilterExpression="mob_num = :val",
            ExpressionAttributeValues={":val": {"S": mob_num}},
        )
        return jsonify({"users": response.get("Items", [])}), 200

    if manager_id:
        response = dynamodb_client.scan(
            TableName=USERS_TABLE,
            FilterExpression="manager_id = :val",
            ExpressionAttributeValues={":val": {"S": manager_id}},
        )
        return jsonify({"users": response.get("Items", [])}), 200

    response = dynamodb_client.scan(TableName=USERS_TABLE)
    dict_response =  [dynamodb_to_dict(item) for item in response.get("Items", [])]
    return jsonify(dict_response), 200
