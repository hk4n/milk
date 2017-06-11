import os

mode = oct(os.stat("from.txt").st_mode & 0777)

print(mode)
