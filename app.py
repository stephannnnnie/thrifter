from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import os
import uuid
import json
from datetime import datetime
import ast
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

items = []
uri = "yourapi"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['secondhand_clothes']
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#get all clothes
@app.route('/api/clothes', methods=['GET'])
def get_clothes():
    clothes = list(db.clothes.find({})
                   .sort([("days_since_posted", 1), ("sold", 1)])
                   .limit(20))
    processed_clothes = []
    for item in clothes:
        processed_item = {
                'id': str(item['_id']),
                'name': item.get('name', 'Unknown'),
                'retailPrice': item.get('retailPrice', '0'),
                'file_name': item.get('file_name', ''),
                'Category': item.get('Category', ''),
                'sold': item.get('sold', False),
                'owner': item.get('owner', '')
            }
        processed_clothes.append(processed_item)
    return jsonify(processed_clothes)


list_fields = ["name", "description", "owner", "days_since_posted", "retailPrice", "file_name",
               'Color', 'Size', 'Material', 'Occasion', 'Category',
               'Details', 'Length', 'Seasons', 'Fit', 'Brand', 'sold'
       ]
@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
#    user_prefs = request.json.preferences
   request_data = request.get_json()
        
    # Extract user preferences and other data
   user_prefs = request_data.get('preferences', {})
   query = {}

   or_conditions = []


   # 遍历用户偏好，生成每个字段的查询条件（$in）
   for field in ["details", "color", "size", "seasons", "material",
               "length", "occasion", "fit", "brand", "category"]:
       if field in user_prefs and user_prefs[field]:
           # 将当前字段添加到 $or 查询条件中
           preferences_list = user_prefs[field]
        
        # 为每个偏好项生成正则表达式条件，并使用 $or 组合它们
           for pref in preferences_list:
                or_conditions.append({
                    field.capitalize(): {"$regex": pref, "$options": "i"}  # 对每个偏好项使用正则表达式匹配
                })

   # 如果有价格区间，添加价格区间查询条件
   if "price" in user_prefs and len(user_prefs["price"]) == 2:
       min_price, max_price = user_prefs["price"]
       or_conditions.append({
           "retailPrice": {"$gte": [{"$toDouble": "$retailPrice"}, min_price], "$lte": [{"$toDouble": "$retailPrice"}, max_price]}
       })


   # 如果有 or_conditions，添加到查询条件中
   if or_conditions:
       query["$or"] = or_conditions
   print(or_conditions)


   # 查询 MongoDB
   items = list(db.clothes.find(query))


   # 数据清洗和格式化
   cleaned_items = []
   for item in items:
       cleaned_item = {}
       for key, value in item.items():
           if key == "_id":
               continue  # 去掉 MongoDB 自带的 _id
           elif key in list_fields:
               try:
                   parsed_list = ast.literal_eval(value)
                   if isinstance(parsed_list, list):
                       cleaned_item[key] = ', '.join(parsed_list)
                   else:
                       cleaned_item[key] = value
               except:
                   cleaned_item[key] = value
           else:
               cleaned_item[key] = value
       cleaned_items.append(cleaned_item)


   # 排序 sold=False 在前，days_since_posted 从小到大
   cleaned_items.sort(key=lambda x: (x.get('sold', True), int(x.get('days_since_posted', 9999))))
#    print(cleaned_items)
   return jsonify(cleaned_items)

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.json
    
    # Generate a unique ID for the item
    item_id = str(uuid.uuid4())
    
    # Add the ID and timestamp
    data['id'] = item_id
    if 'createdAt' not in data:
        data['createdAt'] = datetime.now().isoformat()
    
    # Store the item
    items.append(data)
    
    # In a real app, you would save to a database
    with open('items.json', 'w') as f:
        json.dump(items, f)
    
    return jsonify({"id": item_id, "message": "Item created successfully"})

@app.route('/api/uploads', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    # Generate a unique filename
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Save the file
    file.save(file_path)
    
    # In a real app, you might upload to cloud storage like AWS S3
    # Return the URL where the image can be accessed
    image_url = f"/uploads/{filename}"  # Relative URL to the saved image
    
    return jsonify({"imageUrl": image_url})

@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify(items)


@app.route('/clothes/<clothes_id>', methods=['GET'])
def get_clothes_detail(clothes_id):
    try:
        clothes = db.clothes.find_one({"_id": ObjectId(clothes_id)})
        if clothes:
            clothes['_id'] = str(clothes['_id'])
            return jsonify(clothes)
        else:
            return jsonify({"error": "Clothes not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/clothes', methods=['POST'])
def add_clothes():
    data = request.json
    result = db.clothes.insert_one(data)
    return jsonify({"status": "success", "id": str(result.inserted_id)})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
