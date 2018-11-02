import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Process,Manager


class MyHandler(FileSystemEventHandler):
	def on_any_event(self, event):
		text=event.src_path+"  "+event.event_type
		print(text)
		f = open("E:/file.txt", "a+")
		f.write(text + "\n")
		f.close()

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

if __name__ == '__main__':
	process=[]
	try:
		paths=['D:\IIDT\Finathon','D:\IIDT\cisco class']
		obs=[]
		for i in paths:
			p1=Process(target=scan_path, args=(i,))
			process.append(p1)
			p1.start()
			print("P started")
			
		print(process)
		time.sleep(5)
		print("Woke up shutting down one process")
		process[0].terminate()
	except:
		for i in process:
			i.terminate()

