from bs4 import BeautifulSoup
import httplib
import sys

# path = sys.argv[1]

conn = httplib.HTTPSConnection("eztv.ch")
	
headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}

req = conn.request("GET", "/")
res = conn.getresponse()
data = res.read()
# print data
soup = BeautifulSoup(data,"html5lib")	

# soup = BeautifulSoup(open("untitled.html"))
l = soup.find('select')
out = open ("db.txt", mode="w")
for serie in l.findAll("option")[1:]:
	out.write(serie["value"] + "," + serie.contents[0] + "\n")

