from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import csv
import gridfs
import os

uri = "mongodb+srv://dengheng:LRy3rgaPUDtVd3bN@cluster1.gp2ik.mongodb.net/?retryWrites=true&w=majority&appName=cluster1"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['secondhand_clothes']
collection = db['clothes']
# with open('outfits_cleaned.csv', 'r', encoding='utf-8') as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         collection.insert_one(row)
    

fs = gridfs.GridFS(db)

image_folder = './filtered_images'

for filename in os.listdir(image_folder):
    with open(os.path.join(image_folder, filename), 'rb') as f:
        # 如果数据库里已经有这个图片，可以选择跳过或替换
        if fs.find_one({'filename': filename}):
            print(f"{filename} already exists.")
            continue
        fs.put(f, filename=filename)
        print(f"{filename} uploaded.")



