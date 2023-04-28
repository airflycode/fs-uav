# import sys
# import time
# import logging

# from watchdog.observers import Observer
# from watchdog.events import LoggingEventHandler,FileSystemEventHandler


import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler,FileSystemEventHandler


# class processor(LoggingEventHandler):
#     def on_created(self, event):
#         super(LoggingEventHandler,self).on_created(event)
#         logging.info("created")
#         return super().on_created(event)

from watchdog.observers import Observer
from watchdog.events import *
import time

class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)
        self.last_filename = ""
        
    def on_moved(self, event):
        if event.is_directory:
            print("directory moved from {0} to {1}".format(event.src_path,event.dest_path))
        else:
            print("file moved from {0} to {1}".format(event.src_path,event.dest_path))

    def on_created(self, event):
        if event.is_directory:
            print("directory created:{0}".format(event.src_path))
        else:
            print("file created:{0}".format(event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            print("directory deleted:{0}".format(event.src_path))
        else:
            print("file deleted:{0}".format(event.src_path))

    # def on_modified(self, event):
    #     if event.is_directory:
    #         print("directory modified:{0}".format(event.src_path))
    #     else:
    #         print("file modified:{0}".format(event.src_path))
            
    def on_closed(self, event): 
        eventpath = event.src_path.split("/")
        eventpath_pf = eventpath[5:]
        print("/".join(eventpath_pf))
        if event.is_directory:
            print("directory closed:{0}".format(event.src_path))
        else:
            print("file closed:{0}".format(event.src_path))
            
if __name__ == "__main__":
    observer = Observer()
    event_handler = FileEventHandler()
    # path = sys.argv[1] if len(sys.argv) > 1 else '.'

    path = "/data/minio/cloud-bucket/wayline/"
    observer.schedule(event_handler,path,True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # path = sys.argv[1] if len(sys.argv) > 1 else '.'
    # event_handler = LoggingEventHandler()
    # observer = Observer()
    # observer.schedule(event_handler, path, recursive=True)
    # observer.start()
    # try:
    #     while True:
    #         time.sleep(1)
    # finally:
    #     observer.stop()
        # observer.join()
