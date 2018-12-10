@echo off
REM ===================================================================================
REM '
REM ' FILE: Get PcInfo.bat
REM '
REM ' OPTIONS: No Options, used as a library 
REM ' REQUIREMENTS: N/A
REM ' BUGS: 
REM ' NOTES: 
REM ' AUTHOR: Ketan Desai ketandesai.co.uk
REM ' VERSION: 1.0
REM ' CREATED: 15.08.2013
REM '===================================================================================
FOR /F "tokens=* USEBACKQ" %%F IN (`hostname`) DO (
SET computername=%%F
)
@echo:
echo    Your Computer Name is: %ComputerName%
ipconfig | findstr /i "ipv4"
ipconfig /all | findstr /i "Default Gateway"
ipconfig /all | findstr /i "Servers"
ipconfig /all | findstr /i "Physical"
echo    .
systeminfo|find /i "system boot time"
systeminfo|find /i "OS Name"
systeminfo|find /i "OS Version"
echo    .
WMIC BIOS GET SERIALNUMBER
@echo
pause