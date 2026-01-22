from lxml import html
import requests

test_url = "https://www.basketball-reference.com/boxscores/202506050OKC.html"

result = requests.get(test_url)
tree = html.fromstring(result.content)

print("=== Looking for series/game info ===")
scorebox_meta = tree.xpath('//div[@class="scorebox_meta"]')
print(f"Found {len(scorebox_meta)} scorebox_meta divs")

if scorebox_meta:
    # Get all text
    all_text = scorebox_meta[0].xpath('.//text()')
    print("\nAll text in scorebox_meta:")
    for i, text in enumerate(all_text):
        if text.strip():
            print(f"  [{i}] {text.strip()}")
    
    # Try different selectors
    divs = scorebox_meta[0].xpath('./div')
    print(f"\nFound {len(divs)} divs inside scorebox_meta")
    for i, div in enumerate(divs):
        print(f"  Div {i}: {div.text_content().strip()}")

# Also check for h1 or title
print("\n=== Looking for page title/header ===")
h1 = tree.xpath('//h1/text()')
print(f"H1: {h1}")

title_text = tree.xpath('//div[@class="scorebox"]//h1/text()')
print(f"Title in scorebox: {title_text}")