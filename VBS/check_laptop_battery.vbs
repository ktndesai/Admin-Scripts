' WMI script to return the charge remaining in a laptop battery, using the 
' EstimatedChargeRemaining property of the Win32_Battery class
'
' This is a NSClient++ script, to be called by Nagios using "check_nrpe"
'
' The base of this VBScript code was generated using the WMI Code Generator, Version 2.01
' http://www.robvanderwoude.com/wmigen.html
'
' Conditional logic and exit code by Cornell D. Green, Feb 2009
' http://www.communit.us
' http://www.degeekify.com

On Error Resume Next

Const wbemFlagReturnImmediately = &h10
Const wbemFlagForwardOnly       = &h20

If WScript.Arguments.UnNamed.Count = 1 Then
	strComputer = WScript.Arguments.UnNamed(1)
Else
	strComputer = "."
End If

Set objWMIService = GetObject( "winmgmts://" & strComputer & "/root/CIMV2" )
Set colInstances = objWMIService.ExecQuery( "SELECT * FROM Win32_Battery", "WQL", wbemFlagReturnImmediately + wbemFlagForwardOnly )

For Each objInstance In colInstances
	WScript.Echo "Battery " & objInstance.Status & " - Charge Remaining = " & objInstance.EstimatedChargeRemaining & "% | charge=" & objInstance.EstimatedChargeRemaining
If objInstance.EstimatedChargeRemaining = 100 Then  ' OK Status - life is good here...
	WScript.Quit(0)
ElseIf objInstance.EstimatedChargeRemaining < 80 Then  ' CRITICAL Status - DefCon 1; I hope you packed a lunch...
	WScript.Quit(2)
Else													' WARNING Status - not *yet* cause for alarm... but our eyes are upon ye...
	WScript.Quit(1)
End If
Next