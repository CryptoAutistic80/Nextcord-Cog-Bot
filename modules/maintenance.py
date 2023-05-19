import os  # Importing the os library for interacting with the operating system
import time  # Importing the time module for working with time-related operations
from nextcord.ext import tasks  # Importing the tasks module from nextcord.ext

# Defining a class named Maintenance
class Maintenance:
    def __init__(self, delete_after=3600, check_interval=3600):
        self.folder_path = './new_images/'
        self.delete_after = delete_after  # Time in seconds after which files should be deleted
        self.check_interval = check_interval  # Time in seconds indicating how often to check for old files
        self.cleaner.start()  # Start the cleaner task

    @tasks.loop(seconds=3600)  # Decorator to make the cleaner function a looping task that runs every 3600 seconds (1 hour)
    async def cleaner(self):
        # Walk through all files in the directory
        for foldername, subfolders, filenames in os.walk(self.folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                # If the file is older than the specified time, delete it
                if os.path.getmtime(file_path) < time.time() - self.delete_after:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")

    @cleaner.before_loop
    async def before_cleaner(self):
        print("File cleaner started...")

