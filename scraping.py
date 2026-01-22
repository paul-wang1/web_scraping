from lxml import html
import requests
import time
import pandas as pd
import re
from random import uniform

def get_playoff_game_urls(year=2025):
    """
    Scrape all playoff game URLs from Basketball Reference
    """
    playoffs_url = f"https://www.basketball-reference.com/playoffs/NBA_{year}.html"
    
    print(f"Fetching playoff schedule for {year}...")
    result = requests.get(playoffs_url)
    tree = html.fromstring(result.content)
    
    # Find all boxscore links
    boxscore_links = tree.xpath('//a[contains(@href, "/boxscores/")]/@href')
    
    # Filter to unique game URLs
    game_urls = []
    seen = set()
    
    for link in boxscore_links:
        if '/boxscores/' in link and link not in seen and link.endswith('.html'):
            if 'index' not in link:
                full_url = f"https://www.basketball-reference.com{link}"
                game_urls.append(full_url)
                seen.add(link)
    
    print(f"Found {len(game_urls)} unique playoff games")
    return game_urls

def scrape_bench_players(game_url):
    """
    Scrape bench player stats from a single game with the requested data structure
    """
    print(f"Scraping: {game_url}")
    
    result = requests.get(game_url)
    
    # Check if we got blocked (status code 429 or 403)
    if result.status_code == 429:
        print("⚠️  Rate limited! Waiting 60 seconds...")
        time.sleep(60)
        result = requests.get(game_url)
    elif result.status_code == 403:
        print("⚠️  Access forbidden! Waiting 120 seconds...")
        time.sleep(120)
        result = requests.get(game_url)
    
    tree = html.fromstring(result.content)
    
    bench_data = []
    
    # Extract game date from URL
    game_date_match = re.search(r'/boxscores/(\d{8})', game_url)
    game_date = game_date_match.group(1) if game_date_match else 'unknown'
    
    # Get scoreboard info - using the working selectors
    scorebox = tree.xpath('//div[@class="scorebox"]')
    
    if not scorebox:
        print(f"Could not find scorebox for {game_url}")
        return bench_data
    
    # Extract team names using strong/a selector that worked
    teams = tree.xpath('//div[@class="scorebox"]//strong/a/text()')
    
    # Extract scores using class='score' that worked
    scores = tree.xpath('//div[@class="scorebox"]//div[@class="score"]/text()')
    
    if len(teams) < 2 or len(scores) < 2:
        print(f"Could not extract team/score info for {game_url}")
        print(f"  Teams found: {teams}")
        print(f"  Scores found: {scores}")
        return bench_data
    
    team1 = teams[0].strip()
    team2 = teams[1].strip()
    team1_score = scores[0].strip()
    team2_score = scores[1].strip()
    
    # Extract series info from H1 tag
    h1_text = tree.xpath('//h1/text()')
    game_of_series = "Unknown"
    
    if h1_text:
        h1 = h1_text[0]
        match = re.search(r'Game\s+(\d+)', h1)
        if match:
            game_of_series = f"Game {match.group(1)}"
    
    # Find both team box score tables (only the game-basic ones)
    box_tables = tree.xpath('//table[contains(@id, "-game-basic")]')
    
    for table in box_tables:
        table_id = table.get('id')
        
        # Skip if not a game-basic table
        if 'game-basic' not in table_id:
            continue
        
        # Extract team abbreviation from table ID
        player_team_abbr = table_id.replace('box-', '').replace('-game-basic', '').upper()
        
        # Find the reserves section
        rows = table.xpath('.//tbody/tr')
        
        is_reserves = False
        for row in rows:
            row_class = row.get('class', '')
            
            # Check if this is the reserves header
            if 'thead' in row_class:
                header_text = row.text_content()
                if 'Reserves' in header_text or 'Bench' in header_text:
                    is_reserves = True
                    continue
                elif is_reserves:
                    # Team totals or another section - stop
                    break
            
            # Skip if we haven't reached reserves yet
            if not is_reserves:
                continue
            
            # Get player name
            player_cell = row.xpath('.//th[@data-stat="player"]')
            if not player_cell:
                continue
            
            player_name = player_cell[0].text_content().strip()
            
            # Skip DNP rows or empty names
            if not player_name or 'Did Not Play' in row.text_content() or 'Not With Team' in row.text_content():
                continue
            
            # Extract GameScore (data-stat="game_score")
            game_score_cell = row.xpath('.//td[@data-stat="game_score"]')
            game_score = game_score_cell[0].text_content().strip() if game_score_cell else ''
            
            # Store data in requested format
            bench_data.append({
                'Player name': player_name,
                'PlayerTeam': player_team_abbr,
                'Team1': team1,
                'Team2': team2,
                'Team1score': team1_score,
                'Team2score': team2_score,
                'GmSc': game_score,
                'GameOfSeries': game_of_series
            })
    
    return bench_data

def scrape_all_bench_stats(year=2025, max_games=None, checkpoint_every=10):
    """
    Scrape all bench player stats for a playoff year with checkpointing
    """
    game_urls = get_playoff_game_urls(year)
    
    if max_games:
        game_urls = game_urls[:max_games]
        print(f"Limiting to {max_games} games for testing\n")
    
    all_bench_data = []
    
    # Check if we have a checkpoint file to resume from
    checkpoint_file = f'checkpoint_bench_data_{year}.csv'
    start_index = 0
    
    try:
        checkpoint_df = pd.read_csv(checkpoint_file)
        all_bench_data = checkpoint_df.to_dict('records')
        # Figure out where we left off by checking game URLs
        scraped_urls = set(checkpoint_df['game_url'].unique())
        start_index = len([url for url in game_urls if url in scraped_urls])
        print(f"📂 Resuming from checkpoint at game {start_index + 1}")
    except FileNotFoundError:
        print("Starting fresh scrape")
    
    for i, game_url in enumerate(game_urls[start_index:], start=start_index):
        try:
            bench_stats = scrape_bench_players(game_url)
            all_bench_data.extend(bench_stats)
            
            # Random delay between 3-6 seconds to appear more human
            delay = uniform(3.0, 6.0)
            time.sleep(delay)
            
            # Save checkpoint every N games
            if (i + 1) % checkpoint_every == 0:
                df_checkpoint = pd.DataFrame(all_bench_data)
                df_checkpoint.to_csv(checkpoint_file, index=False)
                print(f"💾 Checkpoint saved at game {i + 1}/{len(game_urls)}")
            
            if (i + 1) % 10 == 0:
                print(f"✓ Processed {i + 1}/{len(game_urls)} games...")
                
        except Exception as e:
            print(f"❌ Error scraping {game_url}: {e}")
            # Save what we have so far
            df_emergency = pd.DataFrame(all_bench_data)
            df_emergency.to_csv(f'emergency_backup_{year}.csv', index=False)
            print(f"💾 Emergency backup saved")
            
            # Wait longer before continuing
            print("Waiting 30 seconds before continuing...")
            time.sleep(30)
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_bench_data)
    
    # Clean up checkpoint file if we finished successfully
    import os
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print("✓ Checkpoint file cleaned up")
    
    return df

# Test with 3 games first
print("Testing with 3 games...\n")
df_test = scrape_all_bench_stats(year=2025, max_games=3)
print(f"\nScraped {len(df_test)} bench player performances")
print("\nSample data:")
print(df_test.head(15))

# Save test results
df_test.to_csv('nba_bench_test.csv', index=False)
print("\nTest data saved to 'nba_bench_test.csv'")

# Uncomment below to scrape all games with safety features:
print("\n\n" + "="*50)
print("Scraping ALL 2025 playoff games with checkpointing...")
print("="*50 + "\n")
df_full = scrape_all_bench_stats(year=2025, checkpoint_every=10)
df_full.to_csv('nba_bench_players_2025_playoffs.csv', index=False)
print(f"\n✓ Saved {len(df_full)} bench player performances to 'nba_bench_players_2025_playoffs.csv'")