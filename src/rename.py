import re
import glob 
import sys
import os

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
		return number.replace("s","S").replace("e","E")

path = sys.argv[1]
os.chdir(path)

filename = path.split(os.sep)[-2]

filename = filename.replace(" ", "\ ")
filename = filename.replace("(", "\(")
filename = filename.replace(")", "\)")
filename = filename.replace("'", "\\'")
print filename
videos = glob.glob("*.avi")
videos.extend(glob.glob("*.mp4"))
videos.extend(glob.glob("*.mkv"))

subs = glob.glob("*.srt")
subs.extend(videos)
print len(subs)
count = 0
for e in subs:
	tmp = e.replace(" ", ".")
	tmp = tmp.replace("-.", "")
	m = re.search(r"([0-9\.]+|[aA-zZ\.]+|[aA-zZ]+)([0-9]+x[0-9]+|(S|s)[0-9]+(E|e)[0-9]+)",tmp)
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
		print "mv " + e + " " + newsubs
		os.system("mv " + e + " " + newsubs)
	else:
		print "******Rinomina il file:", e, "************"