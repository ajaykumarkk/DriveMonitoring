import string
from ctypes import windll
global drives_list
global process_dict
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Process,Manager
import sqlite3
from sqlite3 import Error
import win32api
import wmi
import math
c = wmi.WMI()

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   res=str(s)+size_name[i]
   return res

class MyHandler(FileSystemEventHandler):
	def on_any_event(self, event):
		text=event.src_path
		dbInsert(text[0],text,event.event_type)

def dbConnect():
	conn = sqlite3.connect('History_Data.db')
	return conn
	print("Connected Successfully")

def dbCreate():
	conn=dbConnect()
	conn.execute(''' CREATE TABLE if not exists Hist (id INTEGER PRIMARY KEY AUTOINCREMENT ,Drive STRING,Path STRING,Event STRING,Time INTEGER);''')
	conn.execute(''' CREATE TABLE if not exists sessions (id INTEGER PRIMARY KEY AUTOINCREMENT ,Drive STRING,DriveName STRING,Serial STRING,start INTEGER,end INTEGER);''')
	conn.execute(''' CREATE TABLE if not exists Drives (id INTEGER PRIMARY KEY AUTOINCREMENT ,DriveName STRING,FileSystem STRING,Serial STRING,Size STRING);''')

	#print("Table Created Successfully")
	
def newDrive(dn,fs,s,size):
	conn =dbConnect()
	c=conn.cursor()
	cout=c.execute('select id from Drives where Serial = "'+ s + '";')
	rows = cout.fetchall()
	try:
		if len(rows) == 0:
			c.execute('INSERT INTO Drives(id,DriveName,FileSystem,Serial,size) values(NULL,"'+dn+'","'+fs+'","'+str(s)+'","'+str(convert_size(int(size)))+'");')
			conn.commit()
			conn.close()
	except Error as e:
		print(e)
		
def dbInsert(d,p,e):
	conn=dbConnect()
	c=conn.cursor()
	c.execute('INSERT INTO Hist(id,Drive,Path,Event,Time) values(NULL,"'+d+'","'+p+'","'+e+'",strftime("%s","now"));')
	conn.commit()
	conn.close()
	print("Inserted TO DB : "+p)

def session_create(d,dn,serial):
	conn=dbConnect()
	c=conn.cursor()
	c.execute('INSERT INTO sessions(id,Drive,DriveName,Serial,start,end) values(NULL,"'+d+'","'+dn+'","'+str(serial)+'",strftime("%s","now"),NULL);')
	conn.commit()
	conn.close()
	
def session_end(d):
	conn =dbConnect()
	c=conn.cursor()
	cout=c.execute('select id from sessions where Drive = "'+ d + '" and end is NULL;')
	rows = cout.fetchall()
	try:
		for row in rows:
			cout=c.execute('update sessions set end = strftime("%s","now") where id ='+str(row[0]))
		conn.commit()
		conn.close()
	except Error as e:
		print(e)
	
def end_allsessions():
	conn =dbConnect()
	c=conn.cursor()
	cout=c.execute('select id from sessions where end is NULL;')
	rows = cout.fetchall()
	try:
		for row in rows:
			cout=c.execute('update sessions set end = strftime("%s","now") where id ='+str(row[0]))
		conn.commit()
		conn.close()
	except Error as e:
		print(e)


		
def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in map(chr, range(65, 91)):
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives

def scan_path(path):
	event_handler = MyHandler()
	observer = Observer()
	observer.schedule(event_handler, path, recursive=True)
	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	observer.join()
	
def Db_Dump():
	conn =dbConnect()
	cur=conn.execute('select * from Hist;')
	for i in cur:
		print(i)
	cur=conn.execute('select * from Sessions;')
	for i in cur:
		print(i)
	cur=conn.execute('select * from Drives;')
	for i in cur:
		print(i)

def get_Serial(d):
	for disk in c.Win32_LogicalDisk():
		if disk.Caption == d:
			return disk.VolumeSerialNumber
			
def get_dsize(d):
	for disk in c.Win32_LogicalDisk():
		if disk.Caption == d:
			return disk.Size

if __name__ == '__main__':
	drives_list=get_drives()
	drive_dic={}
	drives_list1=[]
	process=[]
	dbCreate()
	try:
		while True:
			drives_list1=get_drives()
			if len(list(set(drives_list1) - set(drives_list))) > 0:
				print("Drives Added"+str(set(drives_list1) - set(drives_list)))
				for i in (set(drives_list1) - set(drives_list)):
					p1=Process(target=scan_path, args=(str(i)+":\\",))
					volInf=win32api.GetVolumeInformation(str(i)+":\\")
					session_create(i,volInf[0],get_Serial(str(i)+":"))
					p1.start()
					newDrive(volInf[0],volInf[4],get_Serial(str(i)+":"),get_dsize(str(i)+":"))
					print("process Started for Drive : "+str(i))
					drive_dic[i]=p1 #new process
				print(drive_dic)
				#Db_Dump()
				drives_list=drives_list1
			elif len(list(set(drives_list) - set(drives_list1))) > 0:
				print("Drives Removed"+str(set(drives_list) - set(drives_list1)))
				for i in (set(drives_list) - set(drives_list1)):
					if i in drive_dic.keys():
						drive_dic[i].terminate()
						#volInf=win32api.GetVolumeInformation(str(i)+":\\")
						print("Kiling process")
						session_end(str(i))
						del drive_dic[i] #terminate proces
				print(drive_dic)
				drives_list=drives_list1
	except KeyboardInterrupt:
		for i in drive_dic.keys():
			drive_dic[i].terminate()
		end_allsessions()
		Db_Dump()
		print(" Ending All Sessions \n All watchers Terminated")
		exit(0)