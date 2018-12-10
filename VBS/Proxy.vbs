Option Explicit
Dim WSHShell, strSetting, Gateway1, Gateway2, strQuery, objWMIService, colItems, objItem, strGW, strIP
Set WSHShell = WScript.CreateObject("WScript.Shell")

'Define Gateway Addresses
Gateway1 = "172.27.40.1"
Gateway2 = "192.168.102.6"

'Query the Network Adapter Configuration Class and filter by Network Adapters using DHCP
strQuery = "SELECT * FROM Win32_NetworkAdapterConfiguration WHERE DHCPEnabled=1"


Set objWMIService = GetObject( "winmgmts://./root/CIMV2" )
Set colItems      = objWMIService.ExecQuery( strQuery, "WQL", 48 )

For Each objItem In colItems
    If IsArray( objItem.DefaultIPGateway ) Then
        If UBound( objItem.DefaultIPGateway ) = 0 Then
            strGW = objItem.DefaultIPGateway(0)
			strIP = objItem.IPAddress(0)
			'MsgBox strIP & chr(13) & strGW
        Else
        End If
    End If
Next
If strGW = Gateway1 then
'WSHShell.regwrite "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable", 1, "REG_DWORD"
MsgBox "Your are in TMA - Kingston " & chr(13) & "Gateway: " & strGW
	else
		If strGW = Gateway2 then
		'WSHShell.regwrite "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable", 1, "REG_DWORD"
		MsgBox "Your are in TMA - Polmont" & chr(13) & "Gateway: " & strGW
	else
'WSHShell.regwrite "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable", 0, "REG_DWORD"
MsgBox "Your are not in TMA " & chr(13) & "Gateway: " & strGW
End IF
End IF