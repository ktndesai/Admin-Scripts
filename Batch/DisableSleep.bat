@echo off
REM ===================================================================================
REM '
REM ' FILE: DisableSleep.bat
REM '
REM ' OPTIONS: No Options, used as a library 
REM ' REQUIREMENTS: N/A
REM ' BUGS: 
REM ' NOTES: 
REM ' AUTHOR: Ketan Desai ketandesai.co.uk
REM ' VERSION: 1.0
REM ' CREATED: 15.08.2013
REM '===================================================================================
echo disabling standby
powercfg.exe -change -standby-timeout-ac 0
powercfg.exe -change -standby-timeout-dc 0
powercfg.exe -change -hibernate-timeout-ac 0
powercfg.exe -change -hibernate-timeout-dc 0 
powercfg -h off

