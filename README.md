# DriveMonitoring
File Event Based Approach to create reports about Removable Drives History with file changes

Pre- Requisutes:
  1. watchdog 
  
    pip install watchdog
      
  2. win32api
      
    pip install pypiwin32
    
  3. wmi
  
    pip install WMI
 
 Config Required : Email server settings need to be updated to your smtp server
 
 Instructions:
  
    python Monitor.py 
    
   This runs the Agent and continously monitors the system no other config required
