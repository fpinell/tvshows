import httplib
conn = httplib.HTTPSConnection("eztv.ag")
import json
import unidecode
headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}

req = conn.request("GET", "/js/search_shows1.js")
res = conn.getresponse()
data = res.read()


j = json.loads(data.strip().split("=")[-1].replace(";$(document).ready(function(){$(\".tv-show-search-select\").select2({data:data});});",""))

with open("../support/new_db.txt","w") as fout:
    for s in j:
        fout.write(s["id"]+","+unidecode.unidecode(s["text"])+"\n")
