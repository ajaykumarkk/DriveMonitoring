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
	#print("Table Created Successfully")
	
	
def dbInsert(d,p,e):
	conn=dbConnect()
	c=conn.cursor()
	c.execute('INSERT INTO Hist(id,Drive,Path,Event,Time) values(NULL,"'+d+'","'+p+'","'+e+'",strftime("%s","now"));')
	conn.commit()
	conn.close()
	print("Inserted TO DB : "+p)

	
	
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
		observer.stop()
	observer.join()
	
def Db_Dump():
	conn =dbConnect()
	cur=conn.execute('select * from Hist;')
	for i in cur:
		print(i)
	
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
					p1.start()
					print("process Started for Drive : "+str(i))
					drive_dic[i]=p1 #new process
				print(drive_dic)
				Db_Dump()
				drives_list=drives_list1
			elif len(list(set(drives_list) - set(drives_list1))) > 0:
				print("Drives Removed"+str(set(drives_list) - set(drives_list1)))
				for i in (set(drives_list) - set(drives_list1)):
					if i in drive_dic.keys():
						drive_dic[i].terminate()
						del drive_dic[i] #terminate proces
				print(drive_dic)
				drives_list=drives_list1
	except:
		pass
		