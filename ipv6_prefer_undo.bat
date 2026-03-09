@echo off
echo Reverting to default IPv4/IPv6 priority...
netsh interface ipv6 set prefix ::ffff:0:0/96 55 0
echo Done! Back to default.
pause