
import time
import random
from urllib.parse import urlencode, quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# CONFIGURATION 
def get_driver():
    options = Options()
    # options.add_argument('--headless')  # Uncomment to run in background
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Suppress Chrome error messages
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    return driver

# --- FILTER URL BUILDER ---
def build_filter_url(
    location="Ahmedabad",
    keyword=None,
    radius=None,
    date_posted=None,  # '24h', '3d', '7d', '30d'
    remote=None,  # True/False
    promoted=None,  # True/False
    job_type=None,  # 'fulltime', 'parttime', 'contract', 'internship'
    company=None,
    page=1
):
    """
    Build Talent.com URL with filters.
    
    Example URL format:
    https://in.talent.com/jobs?l=Ahmedabad&radius=25&date=7d&workplace=remote&company=Sikich%20India&p=1
    """
    base_url = "https://in.talent.com/jobs"
    params = {}
    
    # Location (always required)
    params['l'] = location
    
    # Keyword search
    if keyword:
        params['k'] = keyword
    
    # Radius in km
    if radius:
        params['radius'] = str(radius)
    
    # Date posted (from parameter)
    if date_posted:
        params['date'] = date_posted
    
    # Remote filter (1 for true, 0 for false)
    if remote is not None:
        params['workplace'] = 'remote' if remote else ''
    
    # Promoted filter (1 for true, 0 for false)
    if promoted is not None:
        params['promoted'] = '1' if promoted else '0'
    
    # Job type (fulltime, parttime, contract, internship)
    if job_type:
        params['job_type'] = job_type
    
    # Company filter
    if company:
        params['company'] = company
    
    # Page number
    if page > 1:
        params['p'] = str(page)
    
    # Build final URL
    if params:
        query_string = urlencode(params, doseq=True)
        url = f"{base_url}?{query_string}"
    else:
        url = base_url
    
    return url


def extract_talent_description(detail_soup):
    """
    Extract full job description text from Talent.com detail page.

    This targets the rich description container you showed (a big div with
    multiple <p>, <ul>, <li> elements) and falls back to the older
    'job-description' container if needed.
    """
    
    desc_div = detail_soup.find(
        "div",
        class_=lambda c: c and "sc-fcd630a4-10" in c,
    )
    if desc_div:
        text = desc_div.get_text(" ", strip=True)
        if text and len(text) > 50:
            return text

    # 2) Fallback: look for a container that includes a <b> with "Job Description"
    try:
        for b in detail_soup.find_all("b"):
            if "job description" in b.get_text(strip=True).lower():
                # Climb to a nearby div container
                container = b
                for _ in range(4):
                    if container.parent and container.parent.name == "div":
                        container = container.parent
                text = container.get_text(" ", strip=True)
                if text and len(text) > 50:
                    return text
    except Exception:
        pass

    # 3) Original fallback: id/class 'job-description'
    desc_container = detail_soup.find("div", id="job-description") or detail_soup.find(
        "div", class_="job-description"
    )
    if desc_container:
        text = desc_container.get_text(" ", strip=True)
        if text:
            return text

    return "Description not found."

# --- MAIN LOGIC ---
def scrape_talent_com(
    location="Ahmedabad",
    keyword=None,
    radius=None,
    date_posted=None,
    remote=None,
    promoted=None,
    job_type=None,
    company=None,
    page=1
):
    """
    Scrape Talent.com jobs with filters.
    
    Parameters:
        location: str - City name (default: "Ahmedabad")
        keyword: str - Search keyword for job title/description
        radius: int - Radius in km (e.g., 10, 25, 50)
        date_posted: str - '24h', '3d', '7d', '30d'
        remote: bool - True for remote jobs, False for on-site
        promoted: bool - True for promoted jobs only
        job_type: str - 'fulltime', 'parttime', 'contract', 'internship'
        company: str - Company name filter
        page: int - Page number (default: 1)
    """
    driver = get_driver()
    base_url = "https://in.talent.com"  # Important for fixing relative links
    
    # Build URL with filters
    url = build_filter_url(
        location=location,
        keyword=keyword,
        radius=radius,
        date_posted=date_posted,
        remote=remote,
        promoted=promoted,
        job_type=job_type,
        company=company,
        page=page
    )
    
    print(f"[*] Opening URL: {url}")
    
    try:
        # --- PHASE 1: COLLECT LINKS (List Page) ---
        driver.get(url)
        print("[*] Waiting for page to load...")
        time.sleep(5) 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        
        print("[*] Handing over HTML source to BeautifulSoup...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Using YOUR specific class name
        job_cards = soup.find_all('div', class_='gXOxBJ') 
        
        # Fallback
        if not job_cards:
            job_cards = soup.find_all('div', class_='link-job-wrap')

        print(f"[*] Found {len(job_cards)} job cards. Collecting links...")

        # Store basic info + LINK for every job found
        jobs_to_visit = []
        for card in job_cards:
            try:
                # Extract Title
                title_tag = card.find('h2', class_='card__job-title') or card.find('div', class_='card__job-title') or card.find('h2')
                title = title_tag.text.strip() if title_tag else "N/A"
                
                # Extract Link (The most important part for Deep Scraping)
                link_tag = card.find('a', href=True)
                if link_tag:
                    href = link_tag['href']
                    # Fix relative links (e.g., "/view?id=...")
                    if href.startswith('/'):
                        full_link = base_url + href
                    else:
                        full_link = href
                    
                    jobs_to_visit.append({
                        "title": title,
                        "url": full_link
                    })
            except Exception as e:
                continue

        # --- PHASE 2: VISIT EACH LINK (Detail Pages) ---
        print(f"[*] Starting Deep Scrape on {len(jobs_to_visit)} jobs...")
        
        # Collect all job data in a list
        jobs_data = []
        
        for index, job in enumerate(jobs_to_visit, 1):
            print(f"[*] Visiting Job #{index}: {job['title']}")
            
            try:
                # 1. Navigate to the job page
                driver.get(job['url'])
                
                # 2. Random sleep to avoid blocking
                time.sleep(random.uniform(2, 4))
                
                # 3. Parse the Detail Page
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # 4. Extract full Description (rich text block + fallbacks)
                full_description = extract_talent_description(detail_soup)

                # 5. Extract Company/Location from Detail Page (More accurate here)
                company = "N/A"
                company_tag = detail_soup.find('div', class_='job-header__company') or detail_soup.find('span', class_='hwHBRV')
                if company_tag:
                    company = company_tag.text.strip()

                # 6. Store job data in dictionary
                job_data = {
                    "source": "Talent.com",
                    "title": job['title'],
                    "company": company,
                    "url": job['url'],
                    "description": full_description,
                    "experience": "",
                    "salary": "",
                    "job_function": "",
                    "industry": "",
                    "specialization": "",
                    "graduate_courses": "",
                    "post_graduate_courses": "",
                    "employment_type": "",
                    "job_type": "",
                    "gender": "",
                    "skills": ""
                }
                jobs_data.append(job_data)
                
            except Exception as e:
                print(f"[!] Error processing job #{index}: {e}")
                continue

        print(f"[*] Success! Scraped {len(jobs_data)} jobs")
        return jobs_data

    except Exception as e:
        print(f"[!] Critical Error: {e}")
        return []
    
    finally:
        driver.quit()

if __name__ == "__main__":
    print("=" * 60)
    print("Talent.com Job Scraper - Filter Configuration")
    print("=" * 60)
    print("Press Enter to skip optional filters (use default values)\n")
    
    # Location (required, with default)
    location_input = input("Enter location/city (default: Ahmedabad): ").strip()
    location = location_input if location_input else "Ahmedabad"
    
    # Keyword
    keyword_input = input("Enter search keyword (optional, e.g., 'Python Developer'): ").strip()
    keyword = keyword_input if keyword_input else None
    
    # Radius
    radius_input = input("Enter radius in km (optional, e.g., 10, 25, 50): ").strip()
    radius = int(radius_input) if radius_input.isdigit() else None
    
    # Date posted
    print("\nDate posted options: 24h, 3d, 7d, 30d")
    date_posted_input = input("Enter date posted filter (optional): ").strip().lower()
    if date_posted_input == '24h':
        date_posted = '1'
    elif date_posted_input == '3d':
        date_posted = '3'
    elif date_posted_input == '7d':
        date_posted = '7'
    elif date_posted_input == '30d':
        date_posted = '30'
    else:
        date_posted = None
    # date_posted = date_posted_input if date_posted_input in ['24h', '3d', '7d', '30d'] else None
    
    # Remote filter
    print("\nRemote filter options: yes, no, or leave blank for all")
    remote_input = input("Filter for remote jobs? (yes/no/blank): ").strip().lower()
    remote = None
    if remote_input == 'yes' or remote_input == 'y':
        remote = True
    elif remote_input == 'no' or remote_input == 'n':
        remote = False
    
    # Promoted filter
    promoted_input = input("Filter for promoted jobs only? (yes/no/blank): ").strip().lower()
    promoted = True if (promoted_input == 'yes' or promoted_input == 'y') else None
    
    # Job type
    print("\nJob type options: fulltime, parttime, contract, internship")
    job_type_input = input("Enter job type (optional): ").strip().lower()
    job_type = job_type_input if job_type_input in ['fulltime', 'parttime', 'contract', 'internship'] else None
    
    # Company
    company_input = input("Enter company name to filter (optional): ").strip()
    company = company_input if company_input else None
    
    # Page number
    page_input = input("Enter page number (default: 1): ").strip()
    page = int(page_input) if page_input.isdigit() else 1
    
    # Build filter parameters
    filter_params = {
        'location': location,
        'keyword': keyword,
        'radius': radius,
        'date_posted': date_posted,
        'remote': remote,
        'promoted': promoted,
        'job_type': job_type,
        'company': company,
        'page': page
    }
    
    # Show summary
    print("\n" + "=" * 60)
    print("Filter Summary:")
    print("=" * 60)
    active_filters = {k: v for k, v in filter_params.items() if v is not None}
    for key, value in active_filters.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    
    # Confirm before scraping
    confirm = input("\nProceed with scraping? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Scraping cancelled.")
        exit(0)
    
    print("\n[*] Starting scraper...\n")
    
    # Run scraper with filters
    scrape_talent_com(**filter_params)