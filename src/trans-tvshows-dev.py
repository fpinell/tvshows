import httplib
import urllib
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
import datetime
import smtplib
import urllib2
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import traceback

def sender(username, password, toaddress, email_text):
	fromaddr = username
	toaddrs = toaddress
	now = datetime.datetime.now()
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddrs
	msg['Subject'] = "Tv shows [ " + now.strftime('%Y/%m/%d') + " ]"
	msg.attach(MIMEText(email_text, 'plain'))

	text = msg.as_string()
	# Credentials (if needed)
	username = username
	password = password

	# The actual mail send
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username, password)
	server.sendmail(fromaddr, toaddrs, text)
	server.quit()


def new_subs(show, season, episode, language, destdir):
	count = 0
	data = {}
	data["keywords"] = show
	data["seasons"] = season
	data["episodes"] = episode
	data["output_format"] = "json"
	try: 
		url = "https://www.podnapisi.net/subtitles/search/?" + urllib.urlencode(data)
		#print url
		headers_connection = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-GB,en;q=0.8,en-US;q=0.6,es;q=0.4,it;q=0.2,ru;q=0.2,de;q=0.2',
		'Cache-Control': 'no-cache',
		'Connection': 'keep-alive',
		'Pragma': 'no-cache',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.231' }
		req = urllib2.Request(url,headers=headers_connection)
		res = urllib2.urlopen(req)
		page_content = res.read()
		soup = BeautifulSoup(page_content, "html5lib")
		links = soup.findAll('tr', {'class': 'subtitle-entry'})
		if len(links) > 0:
			table = soup.find(
				'table', {'class': 'table table-striped table-hover'})
			languages = table.find_all('abbr', {'class': True})
			url = "https://www.podnapisi.net" + \
				links[0]['data-href'] + '/download'
			req = urllib2.Request(url)
			res = urllib2.urlopen(req)
			file_page = res.read()
			with open("temp.zip", "w") as code:
				code.write(file_page)
			fh = open('temp.zip', 'rb')
			if zipfile.is_zipfile(fh):
				zf = zipfile.ZipFile(fh, "r")
				logging.info(str(zf.namelist()))
				#print str(zf.namelist())
				retval = os.getcwd()
				os.chdir(destdir)
				logging.info(str(zf.namelist()) + ' ' + destdir)
				#print str(zf.namelist()) + ' ' + destdir
				count += 1
				zf.extractall(path=".", members=None, pwd=None)
				os.chdir(retval)
		logging.info('Subs found ' + str(count))
		return count
	except Exception,e:
		logging.error("Error downloding the subs " + str(traceback.print_exc()))
		pass

def consinstency(number):
	if "x" in number:
		season, episode = number.split("x")
		if int(season[0]) != 0 and len(season) < 2:
			season = "0" + season
		if int(episode[0]) != 0 and len(episode) < 2:
			episode = "0" + episode
		number = "S" + season + "E" + episode
		return number
	else:
		return number


def rename(path):
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
		m = re.search(
			r"([0-9\.]+|[aA-zZ\.]+|[aA-zZ]+)([0-9]+x[0-9]+|S[0-9]+E[0-9]+)", tmp)
		if m is not None:
			n = consinstency(m.group(2))
			if "srt" in tmp:
				newsubs = filename + "." + n + ".srt"
			elif "avi" in tmp:
				newsubs = filename + "." + n + ".avi"
			elif "mp4" in tmp:
				newsubs = filename + "." + n + ".mp4"
			elif "mkv" in tmp:
				newsubs = filename + "." + n + ".mkv"
			e = e.replace(" ", "\ ")
			e = e.replace("(", "\(")
			e = e.replace(")", "\)")
			e = e.replace("'", "\\'")
			e = e.replace(",", "\,")
			# print "mv " + e + " " + newsubs
			os.system("mv " + e + " " + newsubs)
		else:
			logging.info("******Rinomina il file:" + e + " ************")
		os.chdir(".")


def comparison(lastepisode, lastseason, currentepisode, currentseason):

	if lastseason < currentseason:
		return 1
	if lastseason == currentseason:
		if lastepisode < currentepisode:
			return 1
		else:
			return 0
	if lastseason > currentseason:
		return 0


def updatelast(lastseason, lastepisode, currentseason, currentepisode):
	if lastseason < currentseason:
		return 1
	if lastseason == currentseason:
		if lastepisode < currentepisode:
			return 1
		else:
			return 0
	if lastseason > currentseason:
		return 0


def episodeseason(str1, str2):
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
	return episode, season


def getlistofepisodes(listoftorrent):
	listofepisodes = []
	for t in listoftorrent:
		listofepisodes.append(t.season + "," + t.episode)

	return listofepisodes


class torrent:

	def __init__(self, sname, season, episode, mlink, server, dirsname, client='aria'):
		self.sname = sname
		self.season = season
		self.episode = episode
		self.mlink = mlink
		self.server = server
		self.dirsname = dirsname
		self.client = client
		self.gid = -1
		self.status = ""
		self.type = 1

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
			self.status = r['status']
		elif self.client == 'trans':
			# sys.stdout.write('Get status of torrent '+ str(self.gid)+"\n")
			trans_torrent = self.server.get_torrent(self.gid)
			progress = trans_torrent.progress
			if progress == 100.0:
				self.status = 'complete'
				self.server.remove_torrent(self.gid)

	def start(self):
		if self.client == 'aria':
			self.gid = self.server.aria2.addUri(
				[self.mlink], {"dir": self.dirsname, "bt-metadata-only": "false"})
		elif self.client == 'trans' and 'magnet' in self.mlink:

			logging.info("add_torrent(" + self.mlink +
						 ",download_dir=" + self.dirsname + ")")
			trans_torrent = self.server.add_torrent(
				self.mlink, download_dir=self.dirsname)
			self.gid = trans_torrent.id
			# sys.stdout.write('Started the torrent with gid = ' + str(trans_torrent.id))


def stopplex():
	ps = subprocess.Popen("ps aux | grep 'Plex'",
						  shell=True, stdout=subprocess.PIPE)
	out, err = ps.communicate()
	lines = out.split('\n')
	for line in lines[:-1]:
		m = re.search('grep', line)
		sep = re.compile('[\s]+')
		if m == None:
			info = sep.split(line)
			os.kill(int(info[1]), 9)
	return 0


def eztvquery(conn, headers, sname, lastseason, lastepisode):
	SearchString = database[sname]
	# logging.info('searchstring '+ SearchString)
	url = "/search/?q1=&q2="+SearchString+"&search=Search"

	try: 

		req = conn.request("GET", url, headers=headers)
		res = conn.getresponse()
		data = res.read()
		soup = BeautifulSoup(data, "html5lib")

		magnets = soup.find_all("a", {"class": "magnet"})
		toDownloadlow = {}
		toDownloadhigh = {}

		listofepisodes = []
		listofepisodes.append((lastseason, lastepisode))

		# logging.info(str(len(magnets)))
		for m in magnets:
			reg = re.search(
				r"(?P<season>S[0-9]+|[0-9]+x)(?P<episode>E[0-9]+|[0-9]+)", m['title'])
			check = 0
			if reg != None:
				currEpisode, currSeason = episodeseason(
					reg.group('episode'), reg.group('season'))
				# logging.info(str(currEpisode)+ ' ' + str(currSeason))
				listofepisodes.append((currSeason, currEpisode))
				check = comparison(lastepisode, lastseason,
								   currEpisode, currSeason)
				if check:
					magnet = m['href']
					downkey = str(currSeason) + "," + str(currEpisode)
					# print magnet
					if magnet != "":
						if "720p" in m:
							toDownloadhigh[downkey] = magnet
						else:
							toDownloadlow[downkey] = magnet
					else:
						logging.info("magnet not found " +
									 currEpisode + ' ' + currSeason + ' ' + sname)
				else:
					continue
		listofepisodes = sorted(
			listofepisodes, key=operator.itemgetter(0, 1), reverse=True)
		forupdateseason = listofepisodes[0][0]
		forupdateepisode = listofepisodes[0][1]

		return toDownloadlow, toDownloadhigh, forupdateseason, forupdateepisode
	except Exception,e:
		logging.error("INTO eztvquery " + traceback.print_exc())
		pass

def launch_transmission():
	ps = subprocess.Popen(
		"ps aux | grep 'transmission-daemon' | grep -v 'grep'", shell=True, stdout=subprocess.PIPE)
	out, err = ps.communicate()
	lines = out.split('\n')
	if len(lines) == 1:
		#--enable-dht --dht-entry-point=dht.transmissionbt.com:6881 --dht-listen-port=6881 --max-overall-download-limit=2M --max-concurrent-downloads=5
		# command = "aria2c --conf-path=/home/fabiopinelli/Documents/tvshows/src/aria2.conf  --disable-ipv6 --enable-rpc --seed-time=0  --bt-max-peers=200 --allow-overwrite=true --max-overall-upload-limit=20K --daemon"
		command = 'transmission-daemon'
		ps = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		out, err = ps.communicate()
		logging.info("NEW Transmission daemon NOW running.")
	else:
		logging.info("Transmission daemon already running")


def launcharia():
	ps = subprocess.Popen(
		"ps aux | grep 'aria2c' | grep -v 'grep'", shell=True, stdout=subprocess.PIPE)
	out, err = ps.communicate()
	lines = out.split('\n')
	if len(lines) == 1:
		#--enable-dht --dht-entry-point=dht.transmissionbt.com:6881 --dht-listen-port=6881 --max-overall-download-limit=2M --max-concurrent-downloads=5
		command = "aria2c --conf-path=/home/fabiopinelli/Documents/tvshows/src/aria2.conf  --disable-ipv6 --enable-rpc --seed-time=0  --bt-max-peers=200 --allow-overwrite=true --max-overall-upload-limit=20K --daemon"
		ps = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
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

logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',
					filename="tvshows.log", level=logging.INFO)

transmission_client = ""  # transmissionrpc.Client()

if client != "" and client == "aria":
	launcharia()
elif client == "trans":
	launch_transmission()
	time.sleep(5)
	try:
		transmission_client = transmissionrpc.Client(
			address='localhost', port=9091, http_handler=None, timeout=None, user='transmission', password='transmission')
		if len(transmission_client.list().keys()) > 0:
			transmission_client.remove_torrent(
				transmission_client.list().keys())
	except Exception, e:
		logging.error('Client transmission error')
		os.system("sudo service transmission-daemon restart")
logging.info("Begin " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
email_text = "Begin " + \
	time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"

os.chdir(workdir)
db = open(dbfile, mode="r")
database = {}
for l in db:
	l = l.strip()
	value, key = l.split(',')[:2]
	database[key] = value
db.close()
conn = httplib.HTTPSConnection("eztv.ag")

headers = {'X-Requested-With': 'XMLHttpRequest',
		   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
toupdate = {}
destdir = ""
numberofseries = 0
numberofdownloads = 0
numberofsubs = 0

with open(configfile, "r") as f:
	for l in f:
		l = l.strip()
		if destdir == "":
			destdir = l.strip()
		else:
			if len(l.split(',')) == 2:
				username, password = l.split(',')
			else:
				numberofseries += 1
				logging.info("reading line: " + l)
				tmpsubs = 0
				tmplastseason = 0 
				tmplastepisode = 0
				try:
					sname, tmplastseason, tmplastepisode, tmpsubs = l.strip().split(',')
				except Exception:
					logging.error("SOME PROBLEM READING THE CONFIG FILE " + l)
					pass
				lastseason = int(tmplastseason)
				lastepisode = int(tmplastepisode)
				# print sname,lastseason,lastepisode
				subs = 0 
				if tmpsubs != 'None':
					logging.info("Value for tmpsubs " + tmpsubs)
					subs = int(tmpsubs)
				if subs == 0:
					# dirsname = sname.replace("(","\(")
					# dirsname = dirsname.replace(")","\)")
					# print sname,lastseason,lastepisode
					where = destdir + "/" + sname
					##################### comment to be removed ###############
					try:
						subs = new_subs(sname, str(lastseason), str(
							lastepisode), language, where)
						##################### comment to be removed ###########
						numberofsubs = 0
						if subs is not None:
							numberofsubs += subs
						if subs != 0:
							rename(where)
						os.chdir(workdir)
					except Exception, e:
						logging.error(
							"PROBLEM DOWNLOADING SUBS " + str(traceback.print_exc()))
						email_text += "PROBLEM DOWNLOADING SUBS " + \
							str(traceback.print_exc()) + "\n"
						pass
				toupdate[sname] = [lastseason, lastepisode, str(0)]
				try:
					toDownloadlow, toDownloadhigh, forupdateseason, forupdateepisode = eztvquery(
						conn, headers, sname, lastseason, lastepisode)
					where = destdir + "/" + sname
					dirsname = sname
					numberofdownloads += len(toDownloadlow.keys())
					# logging.info("LEN LOW " + str(toDownloadlow.keys()))
					# logging.info("LEN HIGH" + str(toDownloadhigh.keys()))
					if len(toDownloadlow.keys()) > 0:
						# print "low quality dowloading", "client: ", client
						for e in sorted(toDownloadlow.keys()):
							# ariainput += "\'" + toDownloadlow[e] + "\' "
							s, ep = e.split(",")

							if client == "":
								print destdir + "/" + dirsname + "/"
								os.system("transmission -w " + destdir + "/" +
										  dirsname + "/ \"" + toDownloadlow[e] + "\"")
								print "Start dowloading ", sname, " Season", s, "Episode", ep
							elif client == "aria":
								t = torrent(sname, s, ep, toDownloadlow[
											e], server, destdir + "/" + dirsname)
								t.start()
								seriesindown[sname].append(t)
								logging.info("Adding: " + sname +
											 " S" + s + " E" + ep)
								email_text += "Adding: " + sname + " S" + s + " E" + ep + "\n"
								# aria = server.aria2.addUri([toDownloadlow[e]], {"dir":dirsname,"bt-metadata-only":"false"})
							elif client == "trans":
								t = torrent(sname, s, ep, toDownloadlow[
											e], transmission_client, destdir + "/" + dirsname, client='trans')
								torrents.append(t)
								# t.start()
								# seriesindown[sname].append(t)
								logging.info("Adding: " + sname +
											 " S" + s + " E" + ep)
								email_text += "Adding: " + sname + " S" + s + " E" + ep + "\n"
							##################### comment to be removed #######
							subs = new_subs(sname, s, e, language, where)
							numberofsubs = 0 
							if subs is not None:
								numberofsubs += subs

					elif len(toDownloadhigh.keys()) > 0 and client != "":
						for e in sorted(toDownloadhigh.keys()):
							# ariainput += "\'" + toDownloadlow[e] + "\' "
							s, ep = e.split(",")
							if client == "":
								os.system("ktorrent " + "\"" +
										  toDownloadhigh[e] + "\"")
								logging.info(
									"Start dowloading " + sname + " Season" + str(s) + " Episode " + str(e))
							else:
								t = torrent(sname, s, ep, toDownloadhigh[
											e], transmission_client, destdir + "/" + dirsname, client='trans')
								torrents.append(t)
								# t.start()
								# seriesindown[sname].append(t)
								logging.info(
									"Adding HIGH: " + sname + " S" + s + " E" + ep + " 720p")

								# aria = server.aria2.addUri([toDownloadlow[e]], {"dir":dirsname,"bt-metadata-only":"false"})
							# if sname == "Newsroom (2012)":
							# 	tmpsname = "Newsroom"
							#	subs = new_subs(tmpsname, s, ep,language,where)
							# 	subs = subtitles(tmpsname, s, ep,where,language)
							# else:
							##################### comment to be removed #######
							subs = 0
							try:
								subs = new_subs(sname, s, ep, language, where)
							except Exception,e:
								logging.error("Downloading subs " + str(traceback.print_exc()))
								pass

							numberofsubs += subs
					toupdate[sname] = [forupdateseason,
									   forupdateepisode, str(subs)]
				except Exception, e:
					logging.error("EZTV QUERY FAILED " + str(traceback.print_exc()))
					email_text += "EZTV QUERY FAILED " + str(traceback.print_exc())+ "\n"
					pass

# logging.info(str(len(torrents)) + ' ' + str(torrents))

for t in torrents:
	t.start()
	seriesindown[t.sname].append(t)
torrents = []
out = open(configfile, mode="w")
out.write(destdir + "\n")
for serie in sorted(toupdate.keys()):
	out.write(serie + "," + str(toupdate[serie][0]) + "," +
			  str(toupdate[serie][1]) + "," + toupdate[serie][2] + "\n")
out.write(username + "," + password)
out.close()
conn.close()
logging.info("Report:")
logging.info("- Serie controllate: " + str(numberofseries))
logging.info("- Episodi scaricati: " + str(numberofdownloads))
logging.info("- Sottotitoli scaricati: " + str(numberofsubs))
logging.info("End " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

email_text += "Report:\n"
email_text += "- Serie controllate: " + str(numberofseries) + "\n"
email_text += "- Episodi scaricati: " + str(numberofdownloads) + "\n"
email_text += "- Sottotitoli scaricati: " + str(numberofsubs) + "\n"
email_text += "End " + \
	time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n"

os.chdir(workdir)
completed = defaultdict(list)
if client != "":
	logging.info(str(len(seriesindown.keys())) + " TORRENTS IN DOWNLOAD")
	while len(seriesindown.keys()) > 0:
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
							rename(completed[s][0].dirsname)
							completed.pop(s)
							seriesindown.pop(s)
		logging.info(str(len(seriesindown.keys())) + " TORRENTS IN DOWNLOAD")
		time.sleep(60)
logging.info("NO MORE TORRENTS IN DOWNLOAD")
# print username, password, username, email_text
sender(username, password, username, email_text)
