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
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Following fields are required in the request body: full_name, mob_num, pan_num",}), 400

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
            "manager_id": {"S": manager_id} if manager_id else {"S": ''},
            "created_at": {"S": created_at},
            "updated_at": {"S": ''},
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
            return jsonify(dynamodb_to_dict(response["Item"])), 200
        else:
            return jsonify({"users": []}), 200

    if mob_num:
        response = dynamodb_client.scan(
            TableName=USERS_TABLE,
            FilterExpression="mob_num = :val",
            ExpressionAttributeValues={":val": {"S": mob_num}},
        )
    
        if "Items" in response:
            users = response["Items"]
            if users:
                users = dynamodb_to_dict(users[0])
            return jsonify(users), 200
        else:
            return jsonify({[]}), 200

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

@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json(silent=True)
    if data is None:
        data = {}

    user_id = data.get('user_id')
    mob_num = data.get('mob_num')

    if user_id:
        response = dynamodb_client.get_item(TableName=USERS_TABLE, Key={'user_id': {'S': user_id}})
        if 'Item' in response:
            delete_response = dynamodb_client.delete_item(TableName=USERS_TABLE, Key={'user_id': {'S': user_id}})
            return jsonify({"message": "User Deleted Successfully"}), 200
        
        return jsonify({"error": "No User Exist With Given user_id"}), 404
    
    if mob_num:
        mob_num = mob_num.removeprefix("0").removeprefix("+91").strip()

        response = dynamodb_client.scan(
            TableName=USERS_TABLE,
            FilterExpression='mob_num = :val',
            ExpressionAttributeValues={':val': {'S': mob_num}}
        )
        
        items = response.get('Items', [])
        if items:
            user_id = items[0]['user_id']['S']
            dynamodb_client.delete_item(TableName=USERS_TABLE, Key={'user_id': {'S': user_id}})
            return jsonify({"message": "User Deleted Successfully"}), 200
        
        return jsonify({"error": "No User Exist With Given phone"}), 404

    return jsonify({"error": "One of following fields are required user_id/mob_num"}), 400

@app.route('/update_user', methods=['POST'])
def update_user():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Following fields are required user_ids, update_data"}), 400
    
    user_ids = data.get('user_ids')
    update_data = data.get('update_data')

    if not user_ids or not update_data:
        return jsonify({"error": "Following fields are required user_ids, update_data"}), 400
    
    if 'manager_id' in update_data and len(update_data) > 1 or 'manager_id' not in update_data and len(user_ids)>1:
        return jsonify({"error": "Only manager_id can be updated in bulk"}), 400
    

    # Checked before loop so that db query do not call again and again for each user
    if 'manager_id' in update_data:
        manager_id = update_data['manager_id']
        if manager_id:
            response = dynamodb_client.get_item(
                TableName=MANAGERS_TABLE,
                Key={'manager_id': {'S': manager_id}}
            )
        if 'Item' not in response:
            return jsonify({"error": "Invalid manager_id"}), 400

    error_list = []

    for user_id in user_ids:
        
        response = dynamodb_client.get_item(
                TableName=USERS_TABLE,
                Key={'user_id': {'S': user_id}}
            )
        
        user = response.get('Item', [])
        if not user:
            error_list.append(f"User with user_id '{user_id}' was not found")
            continue

        if 'full_name' in update_data:
            full_name = update_data['full_name']
            if not full_name:
                error_list.append(f"Invalid full_name for user_id {user_id}")
                continue
            user['full_name'] = {'S': full_name}

        if 'mob_num' in update_data:
            mob_num = update_data['mob_num']
            if not is_valid_mobile(mob_num):
                error_list.append(f"Invalid mob_num for user_id {user_id}")
                continue
            user['mob_num'] = {'S': mob_num}

        if 'pan_num' in update_data:
            pan_num = update_data['pan_num'].upper()
            if not is_valid_pan(pan_num):
                error_list.append(f"Invalid pan_num for user_id {user_id}")
                continue
            user['pan_num'] = {'S': pan_num}
        if 'manager_id' in update_data:

                if not user['manager_id']['S']:
                    user['manager_id'] = {'S': update_data['manager_id']}
                else:
                    user["is_active"] = {"BOOL": False}
                    
                    dynamodb_client.put_item(
                        TableName=USERS_TABLE,
                        Item={
                            "user_id": {"S": str(uuid.uuid4())},
                            "full_name": user["full_name"],
                            "mob_num": user["mob_num"],
                            "pan_num": user["pan_num"],
                            "created_at": {"S": datetime.now().isoformat()},
                            "updated_at": {"S": datetime.now().isoformat()},
                            "is_active": {"BOOL": True},
                            "manager_id": {'S': update_data['manager_id']}
                        },
                    )

        user['updated_at'] = {'S': datetime.now().isoformat()}

    
        dynamodb_client.put_item(TableName=USERS_TABLE, Item=user)

    if error_list:
        return jsonify({"errors": error_list}), 400

    return jsonify({"message": "Users updated successfully"}), 200