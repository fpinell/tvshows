import httplib,urllib
import json 
import xmlrpclib
# import socket
import os
# import os.system
import subprocess
import sys
import re
import zipfile
import glob
from bs4 import BeautifulSoup
from collections import defaultdict
import time 
import operator
import logging 
import transmissionrpc 

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def sender(username,password,toaddress,email_text):
        fromaddr = username
        toaddrs  = toaddress

        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddrs
        msg['Subject'] = "Tv shows["+sname+"]"
        msg.attach(MIMEText(email_text, 'plain'))

        text = msg.as_string()
        # Credentials (if needed)  
        username = username
        password = password

        # The actual mail send  
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, text)
        server.quit()
        
def new_subs (name_serie,season,episode,language,destdir):
  
  name_serie = name_serie.replace(' ','+')
  
  params = {'keywords': name_serie, 'movie_type': 'tv-series', 'language':language,'year':'', 'seasons':season, 'episodes':episode}

  urllib.urlencode(params)

  conn = httplib.HTTPConnection("www.podnapisi.net")

  headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'text/html; charset=utf-8'}

  url = "/subtitles/search/advanced?" 
  for k in params:
    url += k+"="+params[k] + "&"
  #print url

  req = conn.request("GET", url, headers=headers)

  res = conn.getresponse()
  # print res.status, res.msg
  try:
    data = res.read()
    
  except httplib.IncompleteRead, e :
    print e.partial

  soup = BeautifulSoup(data.decode('utf-8'),"html5lib") 
  soup.decode(pretty_print=False, eventual_encoding="UTF-8", formatter='minimal')
  entries = soup.find_all('tr',{'class':'subtitle-entry'})
  check_file = 0
  i_link = 0
  count = 0
  if len(entries) > 0:
    while check_file != 1:
      url_link = entries[i_link].get('data-href')+'/download'
      req = conn.request('GET', url_link,headers=headers)
      res = conn.getresponse()
      data = res.read()
    
      with open("temp.zip", "wb") as code:
		code.write(data)
      fh = open('temp.zip', 'rb')
      if zipfile.is_zipfile(fh):
		zf = zipfile.ZipFile(fh,"r")
		check_file = 1
		retval = os.getcwd()
		os.chdir(destdir)
		count += 1
		zf.extractall(path=".", members=None, pwd=None)
		os.chdir(retval)
		i_link += 1
  logging.info( 'Subs found ' + str( count ) )
  return count


def consinstency(number):
	if "x" in number:
		season,episode = number.split("x")
		if int(season[0]) != 0 and len(season) < 2:
			season = "0"+season
		if int(episode[0]) !=0 and len(episode) < 2:
			episode = "0"+episode
		number = "S"+season+"E"+episode
		return number
	else:
		return number

def rename (path):
	os.chdir(path)

	videos = glob.glob("*.avi")
	videos.extend(glob.glob("*.mp4"))
	videos.extend(glob.glob("*.mkv"))

	subs = glob.glob("*.srt")
	subs.extend(videos)
	filename = path.split(os.sep)[-1]

	filename = filename.replace(" ", "\ ")
	filename = filename.replace("(", "\(")
	filename = filename.replace(")", "\)")
	filename = filename.replace("'", "\\'")

	for e in subs:
		tmp = e.replace(" ", ".")
		tmp = tmp.replace("-.", "")
		m = re.search(r"([0-9\.]+|[aA-zZ\.]+|[aA-zZ]+)([0-9]+x[0-9]+|S[0-9]+E[0-9]+)",tmp)
		if m is not None: 
			n = consinstency(m.group(2))
			if "srt" in tmp:
				newsubs = filename +"."+ n + ".srt"
			elif "avi" in tmp:
				newsubs = filename +"."+ n + ".avi"
			elif "mp4" in tmp:
				newsubs = filename +"."+ n + ".mp4"
			elif "mkv" in tmp:
				newsubs = filename +"."+ n + ".mkv"
			e = e.replace(" ", "\ ")
			e = e.replace("(", "\(")
			e = e.replace(")", "\)")
			e = e.replace("'", "\\'")
			e = e.replace(",", "\,")
			# print "mv " + e + " " + newsubs
			os.system("mv " + e + " " + newsubs)
		else:
			logging.info( "******Rinomina il file:" + e +" ************")
		os.chdir(".")

def subtitles (sname,season,episode,destdir,language):
	languages = {"en":"subtitles","it":"sottotitoli"}
	conn = httplib.HTTPConnection("www.podnapisi.net")

	headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}

	decode = {}
	decode['output'] = []
	temptatives = 0
	tmpsname = sname
	while len(decode['output']) == 0 and temptatives < 10: 
	    if sname == 'Americans (2013)':
	   		tmpsname = 'The Americans'

	    seasonname = "[\""+ tmpsname +"\",-1]"
	    params = urllib.urlencode({'rpcParams': seasonname, 'notificationTimestamp': 1385427964})
	    req = conn.request("POST", "/ppodnapisi/suggestions/",params, headers=headers)

	    res = conn.getresponse()
	    print res.status, res.msg

	    data = res.read()
	    decode = json.loads(data)
	    tmpsname = str(tmpsname.split(' ')[:-1])
	    temptatives += 1 

	if temptatives < 10: 
		if sname != 'Vikings (US)' and sname != 'Americans (2013)':
			sM = decode['output'][0]['omdb_id']
			title = decode['output'][0]['title'].replace(' ','+')
		else:
			print sname,len(decode['output'])
			sM = decode['output'][1]['omdb_id']
			title = decode['output'][1]['title'].replace(' ','+')
	#search?sT=1&sM=442223&sK=Homeland&sTS=3&sTE=9

		search = "/en/ppodnapisi/search?sT=1&sM=" + str(sM)+ "&sK="+title+"&sTS="+season+"&sTE="+episode
		req = conn.request("GET", search)

		res = conn.getresponse()

		
		data = res.read()
	# print data

		soup = BeautifulSoup(data.decode('utf-8'),"html5lib") 
		soup.decode(pretty_print=False, eventual_encoding="UTF-8", formatter='minimal')
	
		pages = soup.findAll('span',{'class':"pages"})

		linklastpage = pages[-1].findAll('a', href=True)
		if len(linklastpage) > 1: 
			if linklastpage[-1] != None:
			
				req = conn.request("GET", linklastpage[-1]['href'].encode('utf-8'))
				res = conn.getresponse()
				data = res.read()
				soup = BeautifulSoup(data.decode('utf-8'),"html5lib") 
				soup.decode(pretty_print=False, eventual_encoding="UTF-8", formatter='minimal')

		tabula = soup.find("table", {"class" : "list first_column_title"})
		count = 0
		subslist = []
		for row in tabula.findAll('tr'):
		    for divs in row.findAll('td'):
		        
		        for l in divs.findAll('div', {"class": "list_div2"}):
		            
		            for ls in l.findAll('a', href=True):
		            	
		                if languages[language] in ls['href'].encode('utf-8'):
		                    req = conn.request("GET", ls['href'].encode('utf-8'))
		                    res = conn.getresponse()
		                    soup2 = BeautifulSoup(res.read().decode('utf-8'),"html5lib" ) 
		                    # print soup2
		                    down = soup2.find_all('a', {"class":"button big download"})[0]
		                    
		                    # print 'ref', down['href']
		                    test = down['href'].split('/')
		                    test[3] = 'download'
		                    link = ""
		                    for t in test[1:]:
		                    	link += "/"+t
		                    headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept-Encoding':'gzip'}
		                    req = conn.request("GET", link)
		                    # req = conn.request("GET", down['href'])
		                    res = conn.getresponse()
		                    data = res.read()
		                    # print "data",data
		                    req = conn.request("GET", data)
		                    # req = conn.request("GET", down['href'])
		                    res = conn.getresponse()
		                    data = res.read()
		                    subslist.append(data)
		                    
		 
		if len(subslist) > 0:
			with open("temp.zip", "wb") as code:
				code.write(subslist[-1])
			code.close()
			fh = open('temp.zip', 'rb')
			zf = zipfile.ZipFile(fh,"r")
			retval = os.getcwd()
			os.chdir(destdir)

			zf.extractall(path=".", members=None, pwd=None)
			os.chdir(retval)
			count +=1
		    # print "Download subtitles for " + sname + " S" + season + " E" + episode 
	else:
		logging.info("Name not available in podnapisi")
		count = 0
	conn.close()
	print 'Subs found ',count
	return count

def comparison (lastepisode,lastseason,currentepisode,currentseason):
	
	if lastseason<currentseason:
		return 1
	if lastseason == currentseason:
		if lastepisode < currentepisode:
			return 1
		else:
			return 0
	if lastseason > currentseason:
		return 0
def updatelast (lastseason,lastepisode,currentseason,currentepisode):
	if lastseason<currentseason:
		return 1
	if lastseason == currentseason:
		if lastepisode < currentepisode:
			return 1
		else:
			return 0
	if lastseason > currentseason:
		return 0
def episodeseason(str1,str2):
	episode = 0 
	season = 0
	if "E" in str1:
		episode = int(str1.replace("E", ""))
	else:
		episode = int(str1)
	if "S" in str2:	
		season = int(str2.replace("S", ""))
	elif "x" in str2:
		season = int(str2.replace("x", ""))
	return episode,season

def getlistofepisodes (listoftorrent):
	listofepisodes = []
	for t in listoftorrent:
		listofepisodes.append(t.season + "," + t.episode)

	return listofepisodes

class torrent:
	def __init__(self,sname,season,episode,mlink,server,dirsname,client='aria'):
		self.sname = sname
		self.season = season
		self.episode = episode
		self.mlink = mlink
		self.server = server
		self.dirsname = dirsname
		self.client = client
		self.gid = -1
		self.status = ""
		self.type= 1 

	def getstatus(self):
		if self.client == 'aria':
			r = self.server.aria2.tellStatus(self.gid, ['status'])
			# sys.stdout.write("checking the status " + r['status'] + "\n")
			# sys.stdout.flush()
			if self.type == 1 and r['status'] != 'waiting':
				r = self.server.aria2.tellStatus(self.gid, ['followedBy'])
				while r.get('followedBy') == None:
					r = self.server.aria2.tellStatus(self.gid, ['followedBy'])
				# sys.stdout.write("Update the GID: " + self.gid + " --> " )
				self.gid = r['followedBy'][0]
				# sys.stdout.write( self.gid + "\n")
				# sys.stdout.flush()
				self.type = 2
			
			r = self.server.aria2.tellStatus(self.gid, ['status'])
			self.status=r['status']
		elif self.client == 'trans':
			# sys.stdout.write('Get status of torrent '+ str(self.gid)+"\n")
			trans_torrent = self.server.get_torrent(self.gid)
			progress = trans_torrent.progress
			if progress == 100.0:
				self.status = 'complete'
				self.server.remove_torrent(self.gid)


	def start(self):
		if self.client == 'aria':
			self.gid = self.server.aria2.addUri([self.mlink], {"dir":self.dirsname,"bt-metadata-only":"false"})	
		elif self.client == 'trans' and 'magnet' in self.mlink:

			logging.info("add_torrent("+self.mlink+",download_dir="+self.dirsname+")")
			trans_torrent = self.server.add_torrent(self.mlink,download_dir=self.dirsname)
			self.gid = trans_torrent.id
			# sys.stdout.write('Started the torrent with gid = ' + str(trans_torrent.id))


def stopplex():
	ps= subprocess.Popen("ps aux | grep 'Plex'", shell=True, stdout=subprocess.PIPE)
	out,err = ps.communicate()
	lines = out.split('\n')
	for line in lines[:-1]:
		m = re.search('grep', line)
		sep = re.compile('[\s]+')
		if m == None:
			info =sep.split(line) 	
			os.kill(int(info[1]), 9)
	return 0

def eztvquery(conn,headers,sname,lastseason,lastepisode):
	SearchString = database[sname]
	params = urllib.urlencode({'SearchString1': '', 'SearchString': SearchString, 'search':'Search'})
	length = 3
	while length != 5:
		req = conn.request("POST", "/search/",params, headers=headers)
		logging.info(sname)
		res = conn.getresponse()
		data = res.read()
		soup = BeautifulSoup(data,"html5lib")	
		length = len(soup.find_all("table", {"class" : "forum_header_border"}))
		#print length
	tab = soup.find_all("table", {"class" : "forum_header_border"})[4]
	toDownloadlow = {}
	toDownloadhigh = {}
	
	listofepisodes = []
	listofepisodes.append((lastseason,lastepisode))

	for row in tab.find_all('tr')[2:]:
		cells = row.find_all('td')
		
		if len(cells) == 6:
			name = cells[1].findAll('a')[0].contents[0]
			m = re.search(r"(?P<season>S[0-9]+|[0-9]+x)(?P<episode>E[0-9]+|[0-9]+)",name)
			check = 0 
			if m != None:
				currEpisode, currSeason = episodeseason(m.group('episode'),m.group('season'))
				# print currEpisode, currSeason
				listofepisodes.append((currSeason,currEpisode))
				check = comparison(lastepisode, lastseason, currEpisode, currSeason)
			if check:
				links = cells[2]
				magnet = ""
				if len(links.findAll('a',{'class':'magnet'}, href=True)) > 0:
				  magnet = links.findAll('a',{'class':'magnet'}, href=True)[0]['href']
				  downkey = str(currSeason)+","+str(currEpisode)
				  #print magnet
				if magnet != "":
				  if "720p" in name:
				    toDownloadhigh[downkey] = magnet
				  else:
				    toDownloadlow[downkey] = magnet
				else: 
				  print "magnet not found", currEpisode,currSeason,sname
			else:
				continue
	listofepisodes = sorted(listofepisodes, key=operator.itemgetter(0, 1), reverse = True)
	forupdateseason = listofepisodes[0][0]
	forupdateepisode = listofepisodes[0][1]
	
	return toDownloadlow,toDownloadhigh,forupdateseason,forupdateepisode

def launch_transmission():
	ps= subprocess.Popen("ps aux | grep 'transmission-daemon' | grep -v 'grep'", shell=True, stdout=subprocess.PIPE)
	out,err = ps.communicate()
	lines = out.split('\n')
	if len(lines) == 1:
		#--enable-dht --dht-entry-point=dht.transmissionbt.com:6881 --dht-listen-port=6881 --max-overall-download-limit=2M --max-concurrent-downloads=5
		# command = "aria2c --conf-path=/home/fabiopinelli/Documents/tvshows/src/aria2.conf  --disable-ipv6 --enable-rpc --seed-time=0  --bt-max-peers=200 --allow-overwrite=true --max-overall-upload-limit=20K --daemon"
		command = 'transmission-daemon'
		ps= subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		out,err = ps.communicate()
		logging.info("NEW Transmission daemon NOW running.")
	else:
		logging.info("Transmission daemon already running")

def launcharia():
	ps= subprocess.Popen("ps aux | grep 'aria2c' | grep -v 'grep'", shell=True, stdout=subprocess.PIPE)
	out,err = ps.communicate()
	lines = out.split('\n')
	if len(lines) == 1:
		#--enable-dht --dht-entry-point=dht.transmissionbt.com:6881 --dht-listen-port=6881 --max-overall-download-limit=2M --max-concurrent-downloads=5
		command = "aria2c --conf-path=/home/fabiopinelli/Documents/tvshows/src/aria2.conf  --disable-ipv6 --enable-rpc --seed-time=0  --bt-max-peers=200 --allow-overwrite=true --max-overall-upload-limit=20K --daemon"
		ps= subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		sys.stdout.write("server aria2c running.\n")

dbfile = sys.argv[1]
configfile = sys.argv[2]
language = sys.argv[3]
client = ""
if len(sys.argv) > 4:
	client = sys.argv[4]
username = ""
password = ""
# print dbfile, configfile
workdir = os.getcwd()
seriesindown = defaultdict(list)
torrents = []
server = xmlrpclib.ServerProxy('http://localhost:6800/rpc')

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s', filename="tvshows.log", level=logging.INFO)

transmission_client = ""#transmissionrpc.Client()

if client != "" and client == "aria":
	launcharia()
elif client == "trans": 
	launch_transmission()
	time.sleep(5)
	transmission_client = transmissionrpc.Client(address='localhost', port=9091, http_handler=None, timeout=None, user='transmission', password='transmission')
	if len(transmission_client.list().keys()) > 0:
		transmission_client.remove_torrent(transmission_client.list().keys())

logging.info("Begin " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
email_text = "Begin " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"

os.chdir(workdir)
db = open (dbfile, mode="r")
database = {}
for l in db:
	l = l.strip()
	value, key = l.split(',')[:2]
	database[key] = value
db.close()
conn = httplib.HTTPSConnection("eztv.ag")

headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}
toupdate = {}
destdir = ""
numberofseries = 0
numberofdownloads = 0
numberofsubs = 0

with open(configfile,"r") as f:
	for l in f:
		l=l.strip()
		if destdir == "":
			destdir=l.strip()
		else:
			if len(l.split(',')) == 2:
				username,password = l.split(',')
			else:
				numberofseries += 1
				sname,tmplastseason,tmplastepisode,tmpsubs = l.split(',')
				lastseason = int(tmplastseason)
				lastepisode = int(tmplastepisode)
				# print sname,lastseason,lastepisode 
				subs = int(tmpsubs)
				if subs == 0:
					# dirsname = sname.replace("(","\(")
					# dirsname = dirsname.replace(")","\)")	
					# print sname,lastseason,lastepisode
					where = destdir +"/"+sname
					##################### comment to be removed ##################
					try:
						subs = new_subs(sname, str(lastseason), str(lastepisode), language,where)
						##################### comment to be removed ##################
						numberofsubs += subs
						if subs !=0:
							rename(where)
						os.chdir(workdir)
					except Exception,e:
						logging.error("PROBLEM DOWNLOADING SUBS " + str(e.message) )
						email_text += "PROBLEM DOWNLOADING SUBS " + str(e.message) + "\n"
						pass					
				try:			
					toDownloadlow,toDownloadhigh,forupdateseason,forupdateepisode = eztvquery(conn, headers, sname, lastseason, lastepisode)
					where = destdir +"/"+sname
					dirsname = sname
					numberofdownloads += len(toDownloadlow.keys())
					
					if len(toDownloadlow.keys()) > 0: 
						# print "low quality dowloading", "client: ", client
						for e in sorted(toDownloadlow.keys()):
							# ariainput += "\'" + toDownloadlow[e] + "\' "
							s,ep = e.split(",")
							
							if client == "":
								print destdir +"/"+dirsname + "/"
								os.system("transmission -w " + destdir +"/"+dirsname + "/ \"" + toDownloadlow[e] + "\"")
								print "Start dowloading ",sname, " Season" ,s ,"Episode", ep	
							elif client == "aria":
								t = torrent(sname, s, ep, toDownloadlow[e],server, destdir +"/"+dirsname)
								t.start()
								seriesindown[sname].append(t)
								logging.info("Adding: " + sname + " S" + s + " E" + ep)
								email_text += "Adding: " + sname + " S" + s + " E" + ep + "\n"
								# aria = server.aria2.addUri([toDownloadlow[e]], {"dir":dirsname,"bt-metadata-only":"false"})
							elif client == "trans":
								t = torrent(sname, s, ep, toDownloadlow[e], transmission_client, destdir +"/"+dirsname,client='trans')
								torrents.append(t)
								#t.start()
								#seriesindown[sname].append(t)
								logging.info("Adding: " + sname + " S" + s + " E" + ep )
								email_text += "Adding: " + sname + " S" + s + " E" + ep + "\n"
							##################### comment to be removed ##################
							subs = new_subs(sname, s, e, language,where)
							numberofsubs += subs

					elif len(toDownloadhigh.keys()) > 0 and client != "": 
						for e in sorted(toDownloadhigh.keys()):
							# ariainput += "\'" + toDownloadlow[e] + "\' "
							s,ep = e.split(",")
							if client == "":
								os.system("ktorrent " + "\"" + toDownloadhigh[e] + "\"")
								logging.info("Start dowloading " + sname + " Season"  + str(s) + " Episode " + str(e))
							else:
								t = torrent(sname, s, ep, toDownloadhigh[e], transmission_client, destdir +"/"+dirsname,client='trans')
								torrents.append(t)
								#t.start()
								#seriesindown[sname].append(t)
								logging.info("Adding: " + sname + " S" + s + " E" + ep + " 720p")
								
								# aria = server.aria2.addUri([toDownloadlow[e]], {"dir":dirsname,"bt-metadata-only":"false"})
							# if sname == "Newsroom (2012)":
							# 	tmpsname = "Newsroom"
							#	subs = new_subs(tmpsname, s, ep,language,where)
							# 	subs = subtitles(tmpsname, s, ep,where,language)	
							# else:
							##################### comment to be removed ##################
							subs = new_subs(sname, s, ep,language,where)
							numberofsubs += subs
					toupdate[sname] = [forupdateseason,forupdateepisode,str(subs)]
				except Exception,e:
					logging.error("EZTV QUERY FAILED " + str(e.message))
					email_text += "EZTV QUERY FAILED " + str(e.message) + "\n"
					pass
for t in torrents:
  t.start()
  seriesindown[t.sname].append(t)
torrents = []
out = open(configfile, mode="w")
out.write(destdir+"\n")
for serie in sorted(toupdate.keys()):
	out.write (serie+"," + str(toupdate[serie][0]) + ","+str(toupdate[serie][1])+ ","+toupdate[serie][2]+"\n")
out.write(username + "," + password)
out.close()
conn.close()
logging.info("Report:")
logging.info("- Serie controllate: " + str(numberofseries) )
logging.info("- Episodi scaricati: " + str(numberofdownloads))
logging.info("- Sottotitoli scaricati: " + str(numberofsubs))
logging.info( "End " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

email_text += "Report:\n"
email_text += "- Serie controllate: " + str(numberofseries) + "\n" 
email_text += "- Episodi scaricati: " + str(numberofdownloads) + "\n"
email_text += "- Sottotitoli scaricati: " + str(numberofsubs) + "\n"
email_text += "End " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"

os.chdir(workdir)
completed = defaultdict(list)
if client != "":
	logging.info(str(len(seriesindown.keys())) + " TORRENTS IN DOWNLOAD" )
	while len(seriesindown.keys()) > 0 :
		for s in seriesindown.keys()[:]:
			for t in seriesindown[s][:]:
				t.getstatus()
				if t.status != 'waiting':
					if t.status == 'error':
						logging.info(t.season + " " + t.episode + " Restart")
						t.start()
					elif t.status == 'complete':
						seriesindown[s].remove(t)
						completed[s].append(t)
						if len(seriesindown[s]) == 0:
							listofepisodes = getlistofepisodes(completed[s])
							sender(username, password, username, email_text)
							rename(completed[s][0].dirsname)
							completed.pop(s)
							seriesindown.pop(s)
		logging.info(str(len(seriesindown.keys())) + " TORRENTS IN DOWNLOAD" )
		time.sleep(600)
logging.info("NO MORE TORRENTS IN DOWNLOAD") 
