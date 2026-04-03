import os
import asyncio
import feedparser
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from supabase import create_client
from telegram import Bot

# YOUR CREDENTIALS (PRE-FILLED)
SUPABASE_URL = "https://lcjtkggyalebvmkexisp.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxjanRrZ2d5YWxlYnZta2V4aXNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUxOTMzNzEsImV4cCI6MjA5MDc2OTM3MX0.PKDG49DQ5DO3c5rlt5fa4X49tgCVkU7R2UnD43dAtNI")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8608807245:AAEjdlq41Ke7TYfBqmnTpA41qDwau4pe0b8")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=BOT_TOKEN)

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', str(text)).lower()).strip()

def calculate_match(resume, job_desc):
    if not resume or not job_desc: return 0
    r_clean, j_clean = clean_text(resume), clean_text(job_desc)
    
    # Keyword matching for technical skills
    r_words, j_words = set(r_clean.split()), set(j_clean.split())
    common = r_words & j_words
    keyword_score = (len(common) / len(j_words) * 100) if j_words else 0
    
    # Semantic similarity
    try:
        vec = TfidfVectorizer(stop_words='english', max_features=150)
        tfidf = vec.fit_transform([r_clean, j_clean])
        semantic = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
    except:
        semantic = keyword_score
    
    return round((semantic * 0.7) + (keyword_score * 0.3), 1)

def location_matches(job_loc, user_locs):
    if not user_locs: return True
    job = str(job_loc).lower()
    return any(pref.lower() in job for pref in user_locs)

def get_ai_internships_indeed():
    """Search for AI/ML internships and fresher roles"""
    searches = [
        ("ai intern", "remote"),
        ("machine learning intern", "india"),
        ("data scientist fresher", "bangalore"),
        ("ml engineer entry level", "india"),
        ("artificial intelligence intern", "remote"),
        ("deep learning intern", "india"),
        ("nlp intern", "remote"),
        ("computer vision intern", "india"),
        ("data analyst fresher", "bangalore"),
        ("ai engineer 0-1 years", "india"),
    ]
    
    all_jobs = []
    for query, loc in searches:
        try:
            rss = f"https://www.indeed.com/rss?q={query.replace(' ', '+')}&l={loc.replace(' ', '+')}"
            feed = feedparser.parse(rss)
            
            for entry in feed.entries:
                if not entry.title: continue
                parts = entry.title.split(' - ')
                
                # Filter for internship/fresher keywords in title
                title_lower = entry.title.lower()
                if any(k in title_lower for k in ['intern', 'fresher', 'entry', 'graduate', 'trainee', '0-1', '1-2 years']):
                    all_jobs.append({
                        'title': parts[0].strip(),
                        'company': parts[1].strip() if len(parts) > 1 else 'Unknown',
                        'location': loc,
                        'description': entry.get('summary', ''),
                        'url': entry.link,
                        'source': 'Indeed'
                    })
        except Exception as e:
            continue
    return all_jobs

def get_ai_internships_internshala():
    """AI/ML specific internships from Internshala"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # Specific AI/ML categories
        urls = [
            "https://internshala.com/internships/data-science-internship/",
            "https://internshala.com/internships/machine-learning-internship/",
            "https://internshala.com/internships/artificial-intelligence-ai-internship/",
            "https://internshala.com/internships/data-analytics-internship/",
        ]
        
        jobs = []
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for card in soup.find_all('div', class_='individual_internship') or soup.find_all('div', class_='job_tuple_card'):
                    title = card.find('h3', class_='heading_4_5') or card.find('h3', class_='job-title')
                    company = card.find('h4', class_='company_name') or card.find('p', class_='company-name')
                    loc = card.find('span', class_='location_link') or card.find('p', class_='location')
                    link = card.find('a', href=True)
                    
                    if title and link:
                        jobs.append({
                            'title': title.text.strip(),
                            'company': company.text.strip() if company else 'Unknown',
                            'location': loc.text.strip() if loc else 'Remote/India',
                            'description': f"{title.text.strip()} - AI/ML Internship",
                            'url': 'https://internshala.com' + link['href'] if not link['href'].startswith('http') else link['href'],
                            'source': 'Internshala'
                        })
            except:
                continue
        return jobs
    except:
        return []

def get_linkedin_jobs():
    """LinkedIn via RSS for AI/ML"""
    try:
        # LinkedIn job RSS (public)
        keywords = ["ai-engineer", "machine-learning-engineer", "data-scientist"]
        jobs = []
        
        for keyword in keywords:
            url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&f_TPR=r86400&position=1&pageNum=0"
            # Note: LinkedIn scraping is hard, keeping this as backup
        return jobs
    except:
        return []

async def main():
    print("🤖 AI/ML Job Scraper Started")
    
    # Get users
    users = supabase.table('users').select('*').execute().data
    if not users:
        await bot.send_message(1415309098, "⚠️ No profile found. Run SQL setup first.")
        return
    
    # Scrape AI/ML specific sources
    all_jobs = []
    all_jobs.extend(get_ai_internships_indeed())
    all_jobs.extend(get_ai_internships_internshala())
    
    # Remove duplicates
    seen = set()
    unique = [j for j in all_jobs if j['url'] not in seen and not seen.add(j['url'])]
    print(f"Found {len(unique)} AI/ML jobs/internships")
    
    total_sent = 0
    
    for user in users:
        uid = user['telegram_id']
        resume = user.get('resume_text', '')
        locations = user.get('preferred_locations', [])
        min_score = user.get('min_match_percent', 55)
        
        if not resume or resume == 'PASTE_YOUR_RESUME_TEXT_HERE':
            await bot.send_message(uid, "⚠️ Please update your resume in the database. Paste your resume text in Supabase SQL Editor.")
            continue
        
        for job in unique:
            # Check duplicate
            exists = supabase.table('jobs').select('id').eq('url', job['url']).eq('user_id', uid).execute().data
            if exists: continue
            
            # Location check
            if not location_matches(job['location'], locations): continue
            
            # Match calculation
            score = calculate_match(resume, job['description'])
            if score < min_score: continue
            
            # Send
            msg = f"""🎯 <b>AI/ML Match: {score}%</b>

<b>{job['title']}</b>
🏢 {job['company']}
📍 {job['location']}
🔗 <a href="{job['url']}">Apply Now</a>
💼 {job['source']}

<i>Fresher/Internship Role Detected</i>"""
            
            try:
                await bot.send_message(uid, msg, parse_mode='HTML', disable_web_page_preview=True)
                supabase.table('jobs').insert({
                    'title': job['title'], 'company': job['company'],
                    'location': job['location'], 'url': job['url'],
                    'source': job['source'], 'match_score': score,
                    'user_id': uid, 'sent': True
                }).execute()
                total_sent += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Send error: {e}")
    
    await bot.send_message(1415309098, f"✅ AI/ML Scan Complete! Sent {total_sent} fresher/internship opportunities.")

if __name__ == "__main__":
    asyncio.run(main())
