import os, json
import requests

#dev
url="http://localhost:8000/api/basic/"
key = "vaGkQQur.OkotzgLTEDFuXwzZrUA1oMUH7iKWDugW"

#BeeComp
#key = "lR95LKJ5.bY6X3kf2sIgBIklwLnZ18l7RbwTNllBF"

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