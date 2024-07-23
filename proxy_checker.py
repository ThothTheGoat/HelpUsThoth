import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_proxy_type(proxy):
    """Determine the type of proxy based on the port number."""
    try:
        _, port = proxy.split(':')
        port = int(port)
        if port in [80, 8080]:
            return 'HTTP'
        elif port == 443:
            return 'HTTPS'
        elif port == 1080:
            return 'SOCKS'
        return 'Unknown'
    except ValueError:
        return 'Unknown'

def is_transparent_or_anonymous(proxy):
    """Determine if the proxy is Transparent, Anonymous, or Elite."""
    try:
        # Check the response headers from httpbin.org to categorize the proxy
        response = requests.get('http://httpbin.org/ip', proxies={'http': proxy, 'https': proxy}, timeout=5)
        headers = response.headers
        if 'X-Forwarded-For' in headers or 'Via' in headers:
            return 'Transparent Proxy'
        elif response.json().get('origin'):
            return 'Anonymous Proxy'
        return 'Elite Proxy'
    except requests.RequestException:
        return 'Unknown'

def check_proxy(proxy):
    """Check if the proxy is working and categorize it."""
    try:
        response = requests.get('http://httpbin.org/ip', proxies={'http': proxy, 'https': proxy}, timeout=5)
        if response.status_code == 200:
            proxy_type = get_proxy_type(proxy)
            proxy_category = is_transparent_or_anonymous(proxy)
            return proxy, True, proxy_type, proxy_category
    except requests.RequestException:
        pass
    return proxy, False, 'Unknown', 'Unknown'

def check_proxies(input_file, output_file):
    """Check proxies from the input file and write working proxies with type and category to the output file."""
    with open(input_file, 'r') as file:
        proxies = [line.strip() for line in file]

    working_proxies = []
    with ThreadPoolExecutor(max_workers=400) as executor:
        futures = {executor.submit(check_proxy, f"http://{proxy}"): proxy for proxy in proxies}
        for future in as_completed(futures):
            proxy, is_working, proxy_type, proxy_category = future.result()
            if is_working:
                working_proxies.append((proxy, proxy_type, proxy_category))
                print(f"Working proxy: {proxy}")
                print(f"  Type: {proxy_type}")
                print(f"  Category: {proxy_category}")
            else:
                print(f"Not working: {proxy}")

    with open(output_file, 'w') as file:
        for proxy, proxy_type, proxy_category in working_proxies:
            file.write(f"{proxy} | Type: {proxy_type} | Category: {proxy_category}\n")

    print(f"Working proxies have been saved to {output_file}")

# Specify the input and output file names
input_file = 'proxies.txt'
output_file = 'working_proxies.txt'

check_proxies(input_file, output_file)
