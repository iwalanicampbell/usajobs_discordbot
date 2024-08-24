# Import dependicies, make sure to download them on your computer too 
import discord
from discord.ext import commands 
import aiohttp
from datetime import datetime, timedelta

# Import config file
from config import *

intents = discord.Intents.default()  # Default intents settings can customize 
intents.message_content = True

client = commands.Bot(command_prefix = '%', intents=intents)

# USAJOBS API Tutorial https://developer.usajobs.gov/tutorials/search-jobs

def get_this_week():
   current_date = datetime.now()
   two_weeks_ago = current_date - timedelta(weeks=2)
   start_date = two_weeks_ago.strftime('%Y-%m-%d')
   end_date = current_date.strftime('%Y-%m-%d')
   print(start_date)
   print(end_date)
   return start_date,end_date


# Test
async def fetch_jobs_keyword(keyword, num_results=10):
    current_date = datetime.now()
    two_weeks_ago = current_date - timedelta(weeks=2)
    start_date = two_weeks_ago.strftime('%Y-%m-%d')
    end_date = current_date.strftime('%Y-%m-%d')

    url = "https://data.usajobs.gov/api/search"
    headers = {
        'Host': 'data.usajobs.gov',
        'User-Agent': EMAIL, 
        'Authorization-Key': USAJOBS_KEY  # Secrets
    }
    params = {
        'Keyword': keyword,
        'ResultsPerPage': str(num_results)
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                jobs = await response.json()
                total_results = jobs['SearchResult']['SearchResultCountAll']  # Extract total results
                return jobs, total_results
            else:
                print(f"Failed to fetch jobs for keyword: {keyword} with status code: {response.status}")
                return None

# Send request of parsed jobs
async def send_jobs(ctx, jobs, num_results):
    if jobs['SearchResult']['SearchResultItems']:
        for job in jobs['SearchResult']['SearchResultItems'][:num_results]:
            title = job['MatchedObjectDescriptor']['PositionTitle']
            location = job['MatchedObjectDescriptor']['PositionLocation'][0]['LocationName']
            await ctx.send(f"**{title}** - {location}")
            


# Fetch Jobs Discord Command
@client.command()
async def fetchjobs(ctx, *args):
    keyword = None
    num_results = 10  # Default number of results
    for arg in args:
        if arg.startswith('-'):
            # Handle flags
            if 'n' in arg:
                # Expect the next element to be the number of results
                num_index = args.index(arg) + 1
                if num_index < len(args):
                    num_results = int(args[num_index])
        else:
            # Assume it's the keyword if it's not a flag
            keyword = arg

    if keyword is None:
        await ctx.send("Please specify a keyword for job searching. Example usage: `%fetchjobs cybersecurity -n 5`")
        return

    jobs, total_results = await fetch_jobs_keyword(keyword, num_results)  # Ensure this matches the fetch function
    if jobs:
        await ctx.send(f"Total jobs found for '{keyword}': {total_results}")
        await send_jobs(ctx, jobs, num_results)
    else:
        await ctx.send(f"No jobs found or there was an error in fetching jobs for '{keyword}'.")



# Fetch Jobs By Cybersecurity Discord Command
@client.command()
async def fetchjobs_cybersecurity(ctx):
    jobs = await fetch_jobs_keyword('cybersecurity')
    if jobs and 'SearchResult' in jobs and 'SearchResultItems' in jobs['SearchResult']:
        for job in jobs['SearchResult']['SearchResultItems']:
            title = job['MatchedObjectDescriptor']['PositionTitle']
            location = job['MatchedObjectDescriptor']['PositionLocation'][0]['LocationName']
            await ctx.send(f"**{title}** - {location}")
    else:
        await ctx.send("No jobs found or there was an error in fetching jobs.")


# On Ready
@client.event
async def on_ready():
   print("Ready to start receiving commands")
   print("---------------------------------")


# Hello Discord Command
@client.command()
async def hello(ctx):
   await ctx.send("Hello I am a bot")

# Help command
@client.command()
async def helpme(ctx):
   await ctx.send("The prefix to this bot is %, the current commands you can do is %hello, %help, and %fetch_jobs, the fetch_jobs function finds jobs with the keyword cybersecurity")

client.run(TOKEN) # Secrets