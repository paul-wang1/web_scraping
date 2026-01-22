#cleaning and analysis 
import pandas as pd
df = pd.read_csv('nba_bench_players_2025_playoffs.csv')
#drop all players with NAN GmSc
df = df.dropna(subset=['GmSc'])


#yeah this sucks probably could have thought about this while scraping
TEAM_MAP = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHO",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS"
}


#abbreviations to match
df['Team1Abbr'] = df['Team1'].map(TEAM_MAP)
df['Team2Abbr'] = df['Team2'].map(TEAM_MAP)


#determine who won
df['Winner'] = df.apply(
    lambda r: r['Team1Abbr'] if r['Team1score'] > r['Team2score']
    else r['Team2Abbr'],
    axis=1
)
#determine who the oppositon is
df['Op'] = df.apply( 
    lambda r: r['Team1Abbr'] if r['Team2Abbr'] == r['PlayerTeam']
    else r['Team2Abbr'],
    axis=1
)

print(df.head())



#take average by each game 
df['GmSc'] = pd.to_numeric(df['GmSc'], errors='coerce')
#league average 
league_avg_gmsc = df['GmSc'].mean()
df['LeagueAvgGmSc'] = league_avg_gmsc

#define x as baseline
x = league_avg_gmsc

team_game_df = (
    df
    .groupby(
        ['PlayerTeam', 'Op', 'GameOfSeries', 'Winner'],
        as_index=False
    )
    .agg(
        AvgTeamGmSc=('GmSc', 'mean'),
        NumPlayersAboveLeagueAvg=('GmSc', lambda s: (s > x).sum()),
        LeagueAvgGmSc=('LeagueAvgGmSc', 'mean')
    )
    .rename(columns={
        'PlayerTeam': 'Team',
        'Op': 'Opponent'
    })
)



# #finalize df into queryable form
team_game_df['Won?'] = (team_game_df['Team'] == team_game_df['Winner']).astype(int)
finaldf = team_game_df.drop(columns=['Winner'])

print(finaldf.head(20))