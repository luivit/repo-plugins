#!/usr/bin/python
#
#
#
# Auth: Jarkko Vesiluoma
#       jvesiluoma@gmail.com
#
# Version history:
#  [B]1.1.0[/B] - Beta, programs can now be removed from recordings / favourites.
#  [B]1.0.9[/B] - Beta, Context menu to save program to recordings / favourites added, tmp dirs now selectable from settings
#  [B]1.0.8[/B] - Beta, Search for recordings added
#  [B]1.0.7[/B] - Beta, Download and Plot context menus added
#  [B]1.0.6[/B] - Beta, Minor fixes
#  [B]1.0.5[/B] - Beta, LiveTV added
#  [B]1.0.4[/B] - Pre-Alpha2, Video stop now fixed, started to code "LiveTV" option 
#  [B]1.0.3[/B] - Pre-Alpha2, tmpfile location check (os-check)
#  [B]1.0.2[/B] - Pre-Alpha2, minor modifications
#  [B]1.0.1[/B] - Pre-Alpha2, modified menu structure
#  [B]1.0.0[/B] - Initial version for XBMC 
#
#
#
# Watson 1 API description:
#
# User recordings (user archive):
#   http://www.watson.fi/pctv/RSS?action=getfavoriterecordings
# 
#   XML format:
#     TITLE		= Program title
#     DESC		= Program description
#     AIRDATE	= Program airdate
#     LINK		= Program link to RSS, e.g: http://www.watson.fi/pctv/rss/recordings/1382979
#     PLINK		= Program permanent link, e.g: 1382979
#     SOURCEURL = Program source url, e.g: http://www.watson.fi/pctv/rss/channels/317994
#     SRCURLINF = Program source url info, e.g: 317994 - HLS/Unknown
#     DURL      = Program download url, if bitrate is '-1', then program is scheduled for recording, but not yet in archive e.g: http://www.watson.fi/pctv/Download?id=1382979&amp;format=HLS&amp;bitrate=-1
#                 If bitrate is for example 1974558, program is recorded and of course, state is 'active and reason is 'Completed' instead of 'blocked' and 'Queued'.
#     THUMBNAIL = Program thumbnail url, e.g: http://www.watson.fi/pctv/resources/recordings/screengrabs/1375085.jpg
#
#         <item>
#            <title>TITLE</title>
#            <description>DESC</description>
#            <dc:date>AIRDATE</dc:date>
#            <link>LINK</link>
#            <guid isPermaLink="false">PLINK</guid>
#            <source url="SOURCEURL">SRCURLINF</source>
#                        <media:content url="DURL" medium="video" type="video/mp4"  expression="full" duration="1980"/>
#            <media:status  state="blocked"  reason="Queued" />
#            <media:community><media:starRating average="0"  min="0" max="5"/></media:community>
#         </item>
#
#     This is how few last line looks, when program is already recorded, notice that 'content url' - line has video type, medium, filesize etc. and state is now 'active' and reason is changed to 'Complete'
#
#                        <media:content url="http://www.watson.fi/pctv/Download?id=1375085&amp;format=HLS&amp;bitrate=1974558" medium="video" type="video/mp4" fileSize="1091264424" expression="full" duration="3180"/>
#            <media:status  state="active"  reason="Completed" />
#            <media:community><media:starRating average="0"  min="0" max="5"/></media:community>
#            <media:thumbnail url="THUMBNAIL" height="72" width="96"/>
#
#
# EPG from last 120 hours:
#   http://www.watson.fi/pctv/RSS?action=getprograms&hours=120
#
#
# Users scheduled recordings: 
#   http://www.watson.fi/pctv/RSS?action=getscheduledrecordings
#   
#   XML format:
#     NAME		= Program name, e.g: Paljastavat valheet
#     CHANID	= Channel Id, e.g: 1011
#     LINK		= Program link, e.g: http://www.watson.fi/pctv/rss/scheduledrecordings/756093
#     PLINK		= Program permanent link, e.g: 756093
#     SURL		= Source URL: http://www.watson.fi/pctv/rss/channels/1011
#
#         <item>
#            <title>NAME</title>
#            <description>Scheduled Recording for Program Title NAME, Every Day from Channel ID CHANID</description>
#            <link>LINK</link>
#            <guid isPermaLink="false">PLINK</guid>
#            <source url="SURL">CHANID</source>
#         </item>
#
# Add recording to favorites:
#   RECORDINGID = 7 digit recodring id (permlink), e.g: 1264516
#   http://www.watson.fi/pctv/RSS?action=addfavorite&amp;id=RECORDINGID
#
#
# Remove program from recordings / favorites:
#    RECORDINGID = 7 digit recodring id (permlink), e.g: 1264516
#    http://www.watson.fi/pctv/RSS?action=removerecording&id=RECORDINGID
#
#
# Search recordings and programs:
#   SEARCHSTRING	= Search string to find recordings and programs
#   http://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term=SEARCHSTRING
#
# 
# 
#
# TV channel Id list: 
#   1006	= Jim
#   1007	= Yle something???
#   1008	= Nelonen
#   1010	= TV1
#   1011	= MTV3
#   1012	= TV2
#   1013	= SVT1
#   1014	= TV5
#   1015	= Sub
#   161260	= ???
#   629149	= AVA
#   642360	= MTV?
#   317994	= FOX



# Global variables
VERSION = "1.1.0"
MYHEADERS = { 'User-Agent': "Watson-XBMC version "+VERSION+";" }
DEBUG=1
# 1=low, 2=high, any other ==> low
QUALITY=2

# Imports
import locale
locale.setlocale(locale.LC_ALL, 'C')
import urllib, urllib2, cookielib , re, os, sys, time, linecache, StringIO, time, xbmcplugin, xbmcaddon, xbmcgui, socket, operator
#import CommonFunctions as common
from xml.dom import minidom
from urlparse import urlparse
watson_addon = xbmcaddon.Addon("plugin.video.watson");

url_archive='http://www.watson.fi/pctv/RSS?action=getfavoriterecordings'

tmpfile=watson_addon.getSetting("tempdir")+"tmp_m3u8a"
tmpfile2=watson_addon.getSetting("tempdir")+"tmp_m3u8b"


# Check settings
def settings():
  # Is account setup properly? Well...at least something given?
  print "checking 05"
  if watson_addon.getSetting("username") != '' and watson_addon.getSetting("password") != '' and tmpfile != ""  and tmpfile2 != "":
    INDEX()
  else:
    u=sys.argv[0]+"?url=Settings&mode=5"
    listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(32005))
    listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(32006)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    
    u=sys.argv[0]+"?url=Settings&mode=5"
    listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(32007))
    listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(32007)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

    
# Get first selection list and display items from tuples
def INDEX():
  
  # Live TV
  u=sys.argv[0]+"?url=LiveTV&mode=1"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(32001))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(32001)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  
  # Archive
  u=sys.argv[0]+"?url=Archive&mode=2"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(32002))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(32002)})    
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  
  # Search recordings
  u=sys.argv[0]+"?url=SearchRec&mode=7"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(32003))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(32003)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)    
   
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
     
# Ask search string from user
def search(url):
  keyboard = xbmc.Keyboard('', watson_addon.getLocalizedString(32004))
  keyboard.doModal()
  if keyboard.isConfirmed() and keyboard.getText():
    search_string = keyboard.getText().replace(" ","+")
    searchrec("http://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term="+search_string)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
# Search from programs *** Not in use ***        
def searchproc(url):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  #dom = minidom.parseString(content)
  #items = dom.getElementsByTagName('item')

  # Save everyhing we need to tuples...
  procsearchmatch=re.compile('<title>(.+?)</title>\n            <description>(.+?)</description>\n            <dc:date>(.+?)</dc:date>\n            <guid isPermaLink="false">(.+?)</guid>\n            <link>(.+?)</link>\n            <source url="(.+?)">(.+?)</source>\n            <media:content duration="(.+?)"/>\n').findall(searchcontent)

  
  procsearchmatch.sort(key=operator.itemgetter(0), reverse=True)
  
  # Add search results
  for matchitem in procsearchmatch:    
    sendurl=matchitem[4]
    sendday=matchitem[2].split("T")[0]
    sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
    sendname=matchitem[0]+" - "+sendday+" "+sendtime

    senddesc=matchitem[1].replace("&#228;","a")
    senddesc=senddesc.replace("&#246;","o")
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    addDir(sendname.replace("&#228;","a"),sendurl.replace("&amp;","&"),4,"",senddesc, "")    
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
    
# Add recording to 'favourites' by plink (seven digit recording id)
def addrecording(name, plink):

  # Compile url
  url="http://www.watson.fi/pctv/RSS?action=addfavorite&id="+plink
         
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  
  xbmcgui.Dialog().ok("Info","Recording %s \n added to recordings."%(name))
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
def removerecording(url,name):
    
  # Compile url
  url="http://www.watson.fi/pctv/RSS?action=removerecording&id="+plink
   
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  
  xbmcgui.Dialog().ok("Info","Recording %s \n removed from recordings."%(name))  
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def searchrec(url):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  #dom = minidom.parseString(content)
  #items = dom.getElementsByTagName('item')

  # Save everyhing we need to tuples...
  recsearchmatch=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n            <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n            <media:status  state="(.+?)"  reason="(.+?)" \/\>\n            <media:community\><media:starRating average="(.+?)"  min=".+?" max=".+?"\/\><\/media:community\>\n            <media:thumbnail url="(.+?)" height="(.+?)" width="(.+?)"\/\>').findall(searchcontent)  
 
  
  recsearchmatch.sort(key=operator.itemgetter(2), reverse=True)
  
  # Add search results
  for matchitem in recsearchmatch:    
    sendurl=matchitem[8]
    sendday=matchitem[2].split("T")[0]
    sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
    sendname=matchitem[0]+" - "+sendday+" "+sendtime

    senddesc=matchitem[1].replace("&#228;","a")
    senddesc=senddesc.replace("&#246;","o")
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    addDir(sendname.replace("&#228;","a"),sendurl.replace("&amp;","&"),4,matchitem[17],senddesc, matchitem[5])    

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

  
# Fetch XML and parse channel list from there and make list of channels
def livetv(url):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  content = opener.open(request).read()
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
  
  #Save everyhing we need to tuples...
  livematch=re.compile('<title>(.+?)<\/title>\n        <description\>(.+?)<\/description\>\n        <link\>(.+?)<\/link>').findall(content)
    
  
  for i in items:
    programtitle=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
    programdesc=i.getElementsByTagName('description')[0].childNodes[0].nodeValue

    programurl=i.getElementsByTagName('media:content')
    programstream1=programurl[0].getAttribute("url")

    parseurl=urlparse(str(programstream1))

    # Read playlist
    response = urllib2.urlopen(programstream1)
    try:
      stringresponse=response.read()
    except urllib2.HTTPError as e:
      print e.code
      print e.read()

    # Get correct urls for streams..playlist contains current program files???.
    playurl={}
    i=0
    for line in stringresponse.split("\n"):
      if "m3u8" in line:
        if i==0:
          playurl["720p"]=line
        else:
          playurl["640p"]=line
        i+=1
    
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    addDir(programtitle,programstream1.replace("playlist.m3u8",playurl["720p"]),6,"",programdesc,"NoContext")

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
      
          
# Get first selection list and display items from tuples
def programs(url):

  checked = []
  ie=0
  if LoginError==False:
    for e in match:
      if e[0] not in checked:
        checked.append(e[0])
  
  checked.sort()
  i=0
  for item in checked:
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    addDir(item.replace("&#228;","a"),"episodelisturl",3,"","","NoContext")
    i+=1
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
      
# Get first selection list and display items from tuples
def episodelist	(url,name):
  i=0
    
  # Sort results by time 
  match.sort(key=operator.itemgetter(2), reverse=True)
  
  for matchitem in match:
    
    if matchitem[0]==name:
      #adddir uniques
      sendurl=matchitem[8]
      sendday=matchitem[2].split("T")[0]
      sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
      sendname=matchitem[0]+" - "+sendday+" "+sendtime

      senddesc=matchitem[1].replace("&#228;","a")
      senddesc=senddesc.replace("&#246;","o")
      #Format: addDir(name,url,mode,thumbnail, description, permlink)    
      addDir(sendname.replace("&#228;","a"),sendurl.replace("&amp;","&"),4,matchitem[17],senddesc, matchitem[5])    
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  
# Add item to XBMC display list
def addDir(name,url,mode,iconimage,pdesc,plink):
  u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
  ok=True
  liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
  contextMenuItems = []
  
  if url.startswith("http"):
    # Create context menu if needed
    if plink != "NoContext":
      contextMenuItems.append(('Download Video', 'XBMC.RunPlugin(%s?url=%s&name=%s&mode=9)'%(sys.argv[0],url, name)))
      contextMenuItems.append(( "Plot", "XBMC.Action(Info)", ))
      contextMenuItems.append(('Remove from recordings', 'XBMC.RunPlugin(%s?url=%s&name=%s&plink=%s&mode=10)'%(sys.argv[0],"removerecording",name,plink)))
      if plink != "":
        contextMenuItems.append(('Add to recordings', 'XBMC.RunPlugin(%s?url=%s&name=%s&plink=%s&mode=8)'%(sys.argv[0],"addrecording",name,plink)))
        
    liz.addContextMenuItems( contextMenuItems )
    liz.setInfo( type="Video", infoLabels={ "Title": name, 'Plot': pdesc } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)                    
  else:
    liz.setInfo( type="Video", infoLabels={ "Title": name, 'Plot': pdesc } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)          

  return ok

# Play LiveTV, url can be played directly
def playlive(url):
  
  # Play selected video
  playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
  
  # Clear playlist before adding new stuff...
  playlist.clear()
  playlist.add(url)
  xbmc.Player().play( playlist)
  while xbmc.Player().isPlaying():
    xbmc.sleep(250)
  xbmc.Player().stop()
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

        
# Retrieve m3u8 file, the dirty, dirty, dirty way, parse it and get and create real playlist
def playurl(url):

  playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )

  # Clear playlist before adding new stuff...
  playlist.clear()
  playlist.add(getplaylisturl(url))

  # Play from playlist
  xbmc.Player().play( playlist)
  while xbmc.Player().isPlaying():
    xbmc.sleep(250)
  xbmc.Player().stop()
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getplaylisturl(urlin):
  playurllow=""
  playurlhigh=""
  
    
  # Compile and retrieve redirection and right npvr server
  try:
    compiledurl='http://'+watson_addon.getSetting("username")+':'+watson_addon.getSetting("password")+'@'+url.split("//")[1]
    urllib.urlretrieve(compiledurl, tmpfile)
  except:
    print "Error creating playlist download URL."

  try:
    fdbc=urllib.urlopen(compiledurl)
    redirection=urlparse(fdbc.url)
  except:
    redirection=""
  
  linestring=open(tmpfile, 'r').read()
  for line in linestring.split("\n"):   
    if "01.m3u8?session" in line:
      playurllow=line
    elif "02.m3u8?session" in line:
      playurlhigh=line
   

  if watson_addon.getSetting("bitrate") == 1:
    finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurllow
  elif watson_addon.getSetting("bitrate") == 0:
    finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurlhigh
  else:
    finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurlhigh

  return finalplaylist  
  
# Download selected video
def downloadvideo(durl,dname):
  
  downloadurl=getplaylisturl(durl)
  ddir=watson_addon.getSetting("savedir")+dname.replace(':','-')
  ddir=ddir.replace(' ','_')
  
  
  # Try to make download dir..
  try:
    os.makedirs(ddir)
  except:
    print "downloadvideo: download dir already exists or permission denied..."
    
  # Get download url (playlist)
  try:
    urllib.urlretrieve(downloadurl, tmpfile2)
    linestring=open(tmpfile2, 'r').read()
    
    xbmcgui.Dialog().ok("Status","Downloading %s in background, \n file is saved to %s."%(dname.replace(':','-'), ddir))    
  except:
    xbmcgui.Dialog().ok("Status","Error getting download url!")    
  
  # Fetch video files
  try:  
    for line in linestring.split("\n"):
      if "session=" in line:      
        if (os.name == "nt"):
          urllib.urlretrieve("http://"+downloadurl.split("/")[2]+"/recorder/resources/"+line, ddir+"\\"+line.split("?")[0])
        elif (os.name == "posix"):
          urllib.urlretrieve("http://"+downloadurl.split("/")[2]+"/recorder/resources/"+line, ddir+"/"+line.split("?")[0])
          
  except:
    xbmcgui.Dialog().ok("Status","Error fetching video files!")
    
  # Combine videofiles!
  try:    
    if (os.name == "nt"):
      cmd='copy /b '+ddir+'\\*.ts '+watson_addon.getSetting("savedir")+dname.replace(':','-').replace(' ','_')+".ts"
      os.system(cmd)      
      cmd_del='rmdir /S /Q '+ddir
      os.system(cmd_del)
      
    if (os.name == "posix"):
      cmd='cat '+ddir+'/*.ts > '+watson_addon.getSetting("savedir")+dname.replace(':','-').replace(' ','_')+".ts"
      print "downloadvideo: cmd = "+cmd
      os.system(cmd)
      cmd_del='rm -rf '+ddir
      print "downloadvideo: cmd_del = "+cmd_del      
      os.system(cmd_del)      
    print "Program: "+line.split("-")[0]+" downloaded, title: "+dname.replace(':','-').replace(' ','_')
  except:
    xbmcgui.Dialog().ok("Status","Error downloading file!")    
  
  # added 9.2
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
          
def get_params():
  param=[]
  paramstring=sys.argv[2]
    
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
      
    pairsofparams=cleanedparams.split('&')
    
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
        
    if paramstring.endswith("mode=9"):
      downloadurl=paramstring.split('=')[1]+"="+paramstring.split('=')[2]+"="+paramstring.split('=')[3]+"="+paramstring.split('=')[4].split('&')[0]
      param.update({'url' : downloadurl })
      
  return param

  
# Main program
params=get_params()
url=None
name=None
mode=None
plink=None
LoginError=True
# Try to get XML list
try:
  cookiejar=cookielib.CookieJar()
  auth_handlerb = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handlerb.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handlerb),urllib2.HTTPCookieProcessor(cookiejar))
  request = urllib2.Request(url_archive, headers=MYHEADERS)
  urllib2.install_opener(opener)
  content = opener.open(request).read()
  
  # Save everyhing we need to tuples...
  match=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n            <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n            <media:status  state="(.+?)"  reason="(.+?)" \/\>\n            <media:community\><media:starRating average="(.+?)"  min=".+?" max=".+?"\/\><\/media:community\>\n            <media:thumbnail url="(.+?)" height="(.+?)" width="(.+?)"\/\>').findall(content)
  LoginError=False
except:
  print "Error opening XML"
  LoginError=True
  

# Get 'url'
try:
  url=urllib.unquote_plus(params["url"])
except:
  pass
  
# Get 'name'
try:
  name=urllib.unquote_plus(params["name"])
except:
  pass
try:
  plink=urllib.unquote_plus(params["plink"])
except:
  pass        
try:
  mode=int(params["mode"])
except:
  pass

if mode==None or url==None or len(url)<1:
  settings()

# Show main menu, livetv / archive / search programs / search recordings
elif mode==0:
  INDEX()

# LiveTV
elif mode==1:
  livetv('http://www.watson.fi/pctv/RSS?action=getavailableretvchannels')

# Archive
elif mode==2:
  programs('http://www.watson.fi/pctv/RSS?action=getfavoriterecordings')
  
# Archive episodelist
elif mode==3:
  episodelist(url,name)
  
# Play from download url...
elif mode==4:
  playurl(url)

# Show settings if not defined or something wrong...
elif mode==5:
  watson_addon.openSettings(url=sys.argv[0])  

# Play live feed
elif mode==6:
  playlive(url)

# Search records
elif mode==7:
  search(url)  
  
# Add recording to favorites / recordings
elif mode==8:  
  addrecording(name,plink)
  
# Download video
elif mode==9:
  downloadvideo(url,name)
  
# Download video
elif mode==10:
  removerecording(name,plink)  
  
xbmcplugin.endOfDirectory(int(sys.argv[1]))