import urllib.request
import json

req = urllib.request.Request(
    'https://wandbox.org/api/compile.json',
    data=json.dumps({
        'compiler': 'gcc-head',
        'code': '#include <iostream>\nint main(){int x; std::cin >> x; std::cout<<x*2;}',
        'stdin': '21'
    }).encode(),
    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
)

print(urllib.request.urlopen(req).read().decode())
