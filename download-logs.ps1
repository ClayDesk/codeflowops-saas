# Download production logs
$latestUrl = "https://elasticbeanstalk-us-east-1-586794474096.s3.amazonaws.com/resources/environments/logs/tail/e-5k3ytruqcr/i-0f067cae642c4fd43/TailLogs-1756046939329.txt?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEO%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIFPJXL%2Frxt%2FKxL7L0gtnBHE1fDktb%2Be3icQa3h2xhI24AiEA3CbmQ3w11mWk1Oa%2Fl%2BUdciepjIyj8JeWax%2BpPTqSxFwq6wIIRxAAGgwxMTU0MTQyMTkwOTQiDL4OXyGDjvhKpU3F0irIAkYFoqEE3jmoJDn1lXP39X1aGDIRXkpZa2ap4lPAwIty9ljXorc20X1gVYcBctrw3%2BBTgwNAgW17S6YTCAZJu%2Fwjk0z7zx%2BqNogqGXQ8W7t9soOcAF52R2HLEftlZXiS2ojU9IkVxkgtNwFCq%2BYGHai5jaDbmK%2FJooeLjTPJ8vEgkLOVfYADCCrMT07ISvj2QLjqZSlX31ktDbYHTnEHm%2Byfv8wBBrmC3Q4HPMJHFGTW5979mjl2XSJoAe0LXFgUZf%2FH8K5Fnbx5FOvkzF2S7EVOgHeKvozgdB8QvIRZKxdKr7iL%2FiKHt%2BLsRH7l32kC98BW7l2Zc9LoBIiK5HXFCE7shwahpWBnCwisWXcV2jl1wqFvpVinYWgVVs%2FAEZfv8v5OCXQY%2BJgRQSi95p2Kvdfxl0ErI39nxbHe5nlW%2B2VKKZxH6O6oaPEwvbmsxQY6vwH4n4StuOw8%2Bnqp%2B55vxPXC0LHMqqsmf3SIxqTqC5aZuCrcc1F446vN3%2B0z4rh52%2BoD3hCm%2BHYY1U1eRnSxOOYkB9Zo38cfNluuRc2bT%2BrY3sEd7PzU5RxMlxEUdLIxPGNTyc9ibX3nf9vh2hv8a%2BB35SJXs3m2RXFQe9W2BnoPRxJ%2B5RIH28OK58TFSheR%2Fi%2FOmDBo8MLniwz9aTHl6iZuVP3WupdPygA29zXgWtXlFbK0TU5gYg%2BcVQv6doZRiw%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20250824T144912Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=ASIARVXZZHFLOGHJ54ZK%2F20250824%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=40a430af337d9c70df8e7794de643c807533dfc02f07e9a270028cd4a1aa40e9"

$earlierUrl = "https://elasticbeanstalk-us-east-1-586794474096.s3.amazonaws.com/resources/environments/logs/tail/e-5k3ytruqcr/i-0f067cae642c4fd43/TailLogs-1756046611467.txt?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEO7%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCLCMq4RhyfT0jNvIu9GpuWGgFidDxcKmIkYRIKpwTqjAIgPNWgdyPsHb4MiQ0vicOxQqv9GWRvPKxjbyfUMlJaGFAq6wIIRxAAGgwxMTU0MTQyMTkwOTQiDJgKRXlda6oC3dcrwyrIAsVSpkY8Wly40IAvAZRB5i8QAv0CX041TajBModleuEVnUus3yOZ28urej1bVyqt54RsjicnuSCrsvKdDwPaOHbSmU3akNKjobUPR0sh1jMriW7jQoXarHd81jIpAn9%2Fq9rHtsE4ODgkP4yoZgsev5MPdIBMPYPEiFKqfCoRtSPj8DzL259irnpw%2BDTof4wuFXiXPRPUoCIReENIJ09EwxAtgTUoeyb6VeP6DoFHoBQwHYOFTZozDUJRR734WFR5jtvCZvYfnAU7VP1wPsQXReRqSGa%2Fv7iQg3yTah%2FTzDYH4arHDeRQzRBtY3CfXufD5jsCv1Kw%2FFz%2B4%2FzaqVuMZyq02iHsbdcLZcc1Bh%2B48aVu2fYwhtVKarherCz6RZq6GRa2zkF6r6g3IopgLou85CXobF9rIdhpBW6dny2pEjOFo6QGnjSafWMw%2BrOsxQY6vwFo8tfSrb7hzU30OQlTNnaapIL3xqqoiARQ3RXYtXHiSMt6den3tHkdZO1IWaVszxtIgrGGL7Ex%2FQlNOg6AvqTr%2BDVGbYmd0jQImCGjxTARF3ipBknDoUl9YYD1nDpIEH8D68xlBQY4mAHMEiM%2Fhtk0tjtcMmiMLnl5WTLN4aLfkoZiZW7JpQb22JG7QIUW4Ccs1I3y0xkF6GfSuRwThC8Y8mbHx3yhC9TEaULsOwsRLV3lU%2FQF3LLD9RoluXv1Dg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20250824T144339Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=ASIARVXZZHFLAJXDMG4X%2F20250824%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=3fe21061bcd6c5d6a9b7d823a704c41e681cde9ec53f5684812a8f25ad554260"

Write-Host "Downloading latest logs..."
try {
    Invoke-WebRequest -Uri $latestUrl -OutFile "latest-logs.txt"
    Write-Host "Latest logs downloaded successfully"
} catch {
    Write-Host "Error downloading latest logs: $($_.Exception.Message)"
}

Write-Host "Downloading earlier logs..."
try {
    Invoke-WebRequest -Uri $earlierUrl -OutFile "earlier-logs.txt"
    Write-Host "Earlier logs downloaded successfully"
} catch {
    Write-Host "Error downloading earlier logs: $($_.Exception.Message)"
}
