@echo off
echo Setting IPv6 priority over IPv4 (temporary)
netsh interface ipv6 set prefix ::ffff:0:0/96 50 0
echo Done! IPv6 is now preferred.
echo.
echo To revert back to normal, run: ipv6_prefer_undo.bat
pause