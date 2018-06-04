import time

logFTPfail="10.0.1.35 ftp: action=Logon srcip=6.6.6.6 resultaction=fail user=pepe"
logFTPok="10.0.1.35 ftp: action=Logon srcip=6.6.6.6 resultaction=ok user=pepe"
logFTPupload="10.0.1.35 ftp: action=Upload srcip=8.8.8.8 resultaction=ok user=pepe"

for i in range(9):
    print time.strftime("%b %d %H:%M:%S") + " " + logFTPfail
    time.sleep(1)

print time.strftime("%b %d %H:%M:%S") + " " + logFTPok

time.sleep(5)
print time.strftime("%b %d %H:%M:%S") + " " + logFTPupload

