import os, json
import requests


#API key for KeaPC is: 8yArxdsF.E4viD1uo4yLSibw0QqI5Vno4KPJ6b8hO
#API key for keaCom is: swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA
 
#dev
#url="http://localhost:8000/api/RFIDTags/"
#key = "vaGkQQur.OkotzgLTEDFuXwzZrUA1oMUH7iKWDugW"
#API key for keaCom is: swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA
#key = "swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA"
#API Key for PI3
#key = "TM4fc8ew.yIeDMRVam9qvQvyGr68n3EpXirAdwv5h"
#BeeComp
#key = "lR95LKJ5.bY6X3kf2sIgBIklwLnZ18l7RbwTNllBF"
#VegaCom
#key = "BJ52fz5N.4536zhdh3XhRKbM8QJ27G9qmO8dkjuhE"

#aws
#url="http://ec2-52-20-131-209.compute-1.amazonaws.com/api/basic/"
url="http://ec2-52-20-131-209.compute-1.amazonaws.com/api/RFIDTags/"
#key = "fS6yn9J2.V0nZcnDAG5Jf6uZHafXQa3R1a2aqSJbe"
key = "CFiTkTbk.JWUqGSLUUqrTbhOSOteivmEachoDGeMy"

cmd="curl -s -k -H Authorization: Api-Key " + key + " " + url
print (url)

headers = {'x-api-key':key}
print(headers)

resp = requests.get(url,headers=headers)
print(resp.status_code)
print(resp.text)