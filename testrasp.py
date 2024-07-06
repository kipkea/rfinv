import os, json
import requests

#dev
url="http://localhost:8000/api/basic/"
key = "VfixmvGp.qqBqOzM6WKT0tFXYNF3RKMATK6WqeX8I"

#BeeComp
#key = "KvXlXwDg.YdXZI2D9YNomiTN84qqNQ3eEpVvrgmhg"

#aws
#url="http://ec2-52-20-131-209.compute-1.amazonaws.com/api/basic/"
#key = "fS6yn9J2.V0nZcnDAG5Jf6uZHafXQa3R1a2aqSJbe"

cmd="curl -s -k -H Authorization: Api-Key " + key + " " + url
print (url)

headers = {'x-api-key':key}
print(headers)

resp = requests.get(url,headers=headers)
print(resp.status_code)
print(resp.text)