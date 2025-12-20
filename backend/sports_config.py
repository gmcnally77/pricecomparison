# backend/sports_config.py

# This list controls which leagues the Universal Engine tracks.
#
# HOW TO ADD NEW LEAGUES:
# 1. Find the key from The Odds API (https://the-odds-api.com/sports-odds-data/sports-api.html)
# 2. Match it to the correct Betfair ID (Bucket):
#    - 7522     = Basketball (All)
#    - 6423     = American Football (All)
#    - 26420387 = MMA (All)
#    - 1        = Soccer (All)

# backend/sports_config.py

SPORTS_CONFIG = [
    # --- MMA (WORKING) ---
    {
        "name": "MMA",
        "betfair_id": "26420387",
        "odds_api_key": "mma_mixed_martial_arts",
        "strict_mode": False  # <--- ADD THIS. Trust the Alias Map, skip the Event Name check.
    },
    # --- AMERICAN FOOTBALL (WORKING) ---
    {
        "name": "NFL",
        "betfair_id": "6423",
        "text_query": "NFL",
        "odds_api_key": "americanfootball_nfl"
    },
{
        "name": "NFL", 
        "betfair_id": "6423",
        "text_query": "NCAA Football",
        "odds_api_key": "americanfootball_ncaaf",
        "strict_mode": False  # <--- MUST BE FALSE for College prices to appear
    },
    {
        "name": "NFL",
        "betfair_id": "6423",
        "text_query": "FCS",
        "odds_api_key": "americanfootball_ncaaf",
        "strict_mode": False  # <--- MUST BE FALSE
    },
    # --- BASKETBALL (RESTRICTED TO NBA ONLY) ---
    {
        "name": "Basketball",
        "betfair_id": "7522",
        "text_query": "NBA",
        "odds_api_key": "basketball_nba"
    }
]

# --- ALIAS MAP ---
ALIAS_MAP = {
    # MMA Specifics
    "alexandervolkanovski": ["alexvolkanovski"], 
    "alexvolkanovski": ["alexandervolkanovski"],

    # Just in case for Lopes
    "diegolopes": ["diegolopez"],
    "diegolopez": ["diegolopes"],
    
    # NFL
    "washington": ["washingtoncommanders", "commanders"],
    "washingtoncommanders": ["washington"],
    "detroit": ["detroitlions"],
    "detroitlions": ["detroit"],
    "minnesota": ["minnesotavikings"],
    "minnesotavikings": ["minnesota"],
    "dallas": ["dallascowboys"],
    "dallascowboys": ["dallas"],
    "nygiants": ["newyorkgiants"],
    "newyorkgiants": ["nygiants"],
    "nyjets": ["newyorkjets"],
    "newyorkjets": ["nyjets"],
    
    # NCAAF
    "miami": ["miamifl", "miamiflorida", "miamihurricanes"],
    "miamifl": ["miami", "miamiflorida", "miamihurricanes"],
    "miamiflorida": ["miami", "miamifl", "miamihurricanes"],
    "olemiss": ["mississippi", "mississippistate"],
    "mississippi": ["olemiss"],
    "ncstate": ["northcarolinastate"],
    "northcarolinastate": ["ncstate"],
    "usc": ["southerncalifornia"],
    "southerncalifornia": ["usc"],
    
    
    # NCAA FCS
    "northdakotastate": ["ndsu", "northdakotast"],
    "ndsu": ["northdakotastate"],
    "southdakotastate": ["sdsu", "southdakotast"],
    "sdsu": ["southdakotastate"],
    "montana": ["montanagrizzlies"],
    "montanastate": ["montanast"],
    "delaware": ["delawarebluehens"],
    "villanova": ["villanova wildcats"],
    "illinoisstate": ["illstate", "ilstate", "illinoisst", "illinoisstredbirds"],
    "villanova": ["villanovawildcats", "nova"],
    "montanastate": ["montanast", "montanastbobcats", "montanastatebobcats"],
    "montana": ["montanagrizzlies", "griz", "univmontana"],

    # EuroLeague / Int'l (Safe to keep for later)
    "olympiacos": ["olympiakos", "olympiacospiraeus"],
    "olympiakos": ["olympiacos", "olympiacospiraeus"],
    "panathinaikos": ["panathinaikosathens", "panathinaikosbc"],
    "realmadrid": ["realmadridbaloncesto"],
    "barcelona": ["fcbarcelona", "barca", "barcelonabasket"],
    "fenerbahce": ["fenerbahcebeko", "fenerbahceistanbul"],
    "anadoluefes": ["efes", "anadolu", "anadoluefesistanbul"],
    "baskonia": ["cazoobaskonia", "laboralkutxa"],
    "virtusbologna": ["virtussegafredobologna"],
    "monaco": ["asmonaco", "monacobasket"],
    "maccabitelaviv": ["maccabiplaytikatelaviv", "maccabi"],
    "partizan": ["partizanmozzartbet", "partizanbelgrade"],
    "redstar": ["crvenazvezda", "kkcrvenazvezda", "redstarbelgrade"],
    "crvenazvezda": ["redstar", "redstarbelgrade"],
    "zalgiris": ["zalgiriskaunas"],
    "alba": ["albaberlin"],
    "bayern": ["bayernmunich", "fcbayernmunich"]
}