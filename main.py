# Import dependicies, make sure to download them on your computer too 
import discord
from discord.ext import tasks, commands 
import aiohttp
import os


intents = discord.Intents.default()  # Default intents settings can customize 
intents.message_content = True

client = commands.Bot(command_prefix = '%', intents=intents)

# USAJOBS API Tutorial https://developer.usajobs.gov/tutorials/search-jobs

# Test
async def fetch_jobs_api(keyword, num_results=10, location='All', hiring_paths=[]):
    url = "https://data.usajobs.gov/api/search"
    headers = {
        'Host': 'data.usajobs.gov',
        'User-Agent': os.environ.get('EMAIL'), 
        'Authorization-Key': os.environ.get('JOB_KEY') # Secrets
    }
    params = {
        'Keyword': keyword,
        'ResultsPerPage': str(num_results),
        'HiringPath' : ';'.join(hiring_paths) if hiring_paths else 'public',
        'LocationName': location if location != 'All' else None  
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                jobs = await response.json()
                total_results = jobs['SearchResult']['SearchResultCountAll']  # Extract total results
                return jobs, total_results
            else:
                print(f"Failed to fetch jobs for keyword: {keyword} with status code: {response.status}")
                return None # Failure 
            

# Send request of parsed jobs
async def send_jobs(ctx, jobs, num_results):
    # First, check if job data exists and has items
    if jobs and 'SearchResult' in jobs and 'SearchResultItems' in jobs['SearchResult'] and jobs['SearchResult']['SearchResultItems']:
        job_items = jobs['SearchResult']['SearchResultItems'][:num_results]  # Limit the output to requested number of results
        if job_items:
            # Send each job as a message; consider using embeds for better formatting
            for job in job_items:
                title = job['MatchedObjectDescriptor']['PositionTitle']
                location = job['MatchedObjectDescriptor']['PositionLocation'][0]['LocationName']
                job_url = job['MatchedObjectDescriptor']['PositionURI']  # Assuming URI is available for the job posting link
                hiring_paths = ", ".join(job['MatchedObjectDescriptor'].get('UserArea', {}).get('Details', {}).get('HiringPath', ['Not specified']))  # Adjust based on actual API response

                # Sending an embed for each job listing
                embed = discord.Embed(title=title, url=job_url, description=f"Location: {location}", color=discord.Color.blue())
                embed.set_author(name="USAJobs Listing")
                embed.add_field(name="Hiring Paths", value=hiring_paths, inline=False)
                embed.add_field(name="Apply Here", value=f"[Click to view job posting]({job_url})", inline=False)
                await ctx.send(embed=embed)
        else:
            # If no job items found in the list
            await ctx.send("There are no job listings available for the specified criteria.")
    else:
        # If the jobs object is empty or missing expected data
        await ctx.send("No jobs found or there was an error retrieving jobs. Please try again.")

            


# Fetch Jobs Discord Command
@client.command(brief="Searches jobs based on user criteria", help="""Fetches jobs based on a keyword and optional flags.

Usage:
    %fetchjobs <keyword> [-n number] [-l location]

Arguments:
    keyword : The job keyword(s) to search for.
    -n number : The number of results to return. Default is 10. Max is 30
    -l location : The geographic location to filter jobs. Default is 'All'. Can only use one location at a time

Example:
    %fetchjobs developer -n 5 -l "New York"
    This will fetch 5 developer jobs in New York.""")


async def fetchjobs(ctx, *args):
    keyword = []
    num_results = 10  # Default number of results
    max_results = 30  # Maximum number of results allowed
    location = 'All'  # Default location
    hiring_paths = [] 

    args = list(args)  # Convert tuple to list for easier manipulation
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('-'):
            # Handle flags
            if 'n' in arg and i + 1 < len(args):
                try:
                    # Try to parse the next element as the number of results
                    num_results = int(args[i + 1])
                    if num_results > max_results:
                        num_results = max_results
                        await ctx.send(f"Number of results limited to maximum of {max_results}.")
                    i += 1  # Increment to skip next element since it's part of this flag
                except ValueError:
                    await ctx.send("Please enter a valid number for results.")
                    return
            elif 'l' in arg and i+1 < len(args):
                location = args[i + 1]
                i += 1  # Increment to skip the location value
            elif 'p' in arg and i+1 < len(args):
                hiring_paths.append(args[i + 1]) 
                i += 1  # Increment to skip the location value
        else:
            # Assume it's part of the keyword if it's not a flag
            keyword.append(arg)
        i += 1

    if not keyword:
        await ctx.send("Please specify a keyword for job searching. Example usage: `%fetchjobs cybersecurity -n 5`")
        return

    keyword = ' '.join(keyword)  # Join list into a single string
    jobs, total_results = await fetch_jobs_api(keyword, num_results, location, hiring_paths)  # Ensure this matches the fetch function
    if jobs:
        await ctx.send(f"Total jobs found for '{keyword}' in '{location}' with hiring paths '{hiring_paths}': {total_results}")
        await send_jobs(ctx, jobs, num_results)
    else:
        await ctx.send(f"No jobs found or there was an error in fetching jobs for '{keyword}'.")

# Background task to fetch jobs every week (604800 seconds in a week)
@tasks.loop(seconds=604800)
async def weekly_internship_fetch():
    channel_id = os.environ.get('CHANNEL_ID1')
    channel = client.get_channel(int(channel_id)) if channel_id else None # Convert to int, might be a type error if not

    if not channel:
        print(f"⚠️ ERROR: Channel ID {channel_id} not found!")
        return
    
    keyword = ["computer science", "IT", "cybersecurity"]
    location = "hawaii"
    hiring_paths = ["student"]
    num_results = 15

    jobs, total_results = await fetch_jobs_api(keyword, num_results, location, hiring_paths)
    if jobs:
        await channel.send(f"Weekly internship search results for '{keyword}' in '{location}' with hiring paths '{hiring_paths}': {total_results}")
        await send_jobs(channel, jobs, num_results)
    else:
        await channel.send("No jobs found or there was an error fetching jobs this week.")

@tasks.loop(seconds=604800)
async def weekly_job_fetch():
    channel_id = os.environ.get('CHANNEL_ID2')
    channel = client.get_channel(int(channel_id)) if channel_id else None # Convert to int, might be a type error if not

    if not channel:
        print(f"⚠️ ERROR: Channel ID {channel_id} not found!")
        return

    keyword = ["computer science", "IT", "cybersecurity"]
    location = ["hawaii", "remote"]
    hiring_paths = ["graduates"]
    num_results = 15

    jobs, total_results = await fetch_jobs_api(keyword, num_results, location, hiring_paths)
    if jobs:
        await channel.send(f"Weekly job search results for '{keyword}' in '{location}' with hiring paths '{hiring_paths}': {total_results}")
        await send_jobs(channel, jobs, num_results)
    else:
        await channel.send("No jobs found or there was an error fetching jobs this week.")

# On Ready
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} ({client.user.id})")
    if not weekly_internship_fetch.is_running():  # Check if the task is already running
        weekly_internship_fetch.start()  # Start the background task when the bot is ready
    if not weekly_job_fetch.is_running():  # Check if the task is already running
        weekly_job_fetch.start()  # Start the background task when the bot is ready
    print("Ready to start receiving commands and the weekly job fetch task has started.")
    print("---------------------------------")


# Hello Discord Command
@client.command(brief="Greets the user", help="This command sends a greeting message and offers help.")
async def hello(ctx):
   await ctx.send("Hello I am a bot, do %help for more info")

client.run(os.environ.get('TOKEN')) # Secrets



