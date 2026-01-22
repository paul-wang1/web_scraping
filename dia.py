from lxml import html
import requests

# Test with one game
test_url = "https://www.basketball-reference.com/boxscores/202506050OKC.html"

result = requests.get(test_url)
tree = html.fromstring(result.content)

print("=== Looking for scorebox ===")
scorebox = tree.xpath('//div[@class="scorebox"]')
print(f"Found {len(scorebox)} scorebox divs")

# Try alternative selectors
print("\n=== Trying alternative team selectors ===")
teams1 = tree.xpath('//div[@class="scorebox"]//strong/a/text()')
print(f"Teams (strong/a): {teams1}")

teams2 = tree.xpath('//div[@class="scorebox"]//div//a/text()')
print(f"Teams (div//a): {teams2[:10]}")  # First 10 to avoid clutter

print("\n=== Looking for scores ===")
scores1 = tree.xpath('//div[@class="scorebox"]//div[@class="score"]/text()')
print(f"Scores (class='score'): {scores1}")

scores2 = tree.xpath('//div[@class="scorebox"]//div[contains(@class, "score")]/text()')
print(f"Scores (contains 'score'): {scores2}")

print("\n=== Looking for any divs with numbers ===")
all_divs = tree.xpath('//div[@class="scorebox"]//div/text()')
print(f"All text in scorebox divs: {[t.strip() for t in all_divs if t.strip()][:20]}")

print("\n=== Looking for box score tables ===")
tables = tree.xpath('//table[contains(@id, "box-")]')
print(f"Found {len(tables)} box score tables")
for table in tables:
    print(f"  Table ID: {table.get('id')}")