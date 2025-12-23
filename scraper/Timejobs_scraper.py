"""
TimesJobs Multi-Page Scraper - Complete Working Version
This scraper collects all job listings from all pages on TimesJobs
and extracts detailed information for each job.
"""

import time
import random
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys

#  CONFIGURATION 

def get_driver():
    """Initialize Chrome WebDriver with optimized settings"""
    options = Options()
    options.add_argument('--headless')  
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    return driver

# URL BUILDERS 

def build_timesjobs_url(keyword=None, location=None, experience=None, page=1):
    """
    Build TimesJobs search URL using the public-facing parameters, e.g.:
    https://www.timesjobs.com/job-search?keywords=%22xyz%22%2C&location=Ahmedabad%2C+&experience=2&refreshed=true
    """
    base_url = "https://www.timesjobs.com/job-search"
    params = {
        "refreshed": "true",
    }

    if keyword:
        params["keywords"] = f"\"{keyword}\""
    if location:
        params["location"] = f"{location},"
    if experience is not None:
        params["experience"] = str(experience)
    if page > 1:
        params["page"] = str(page)

    return f"{base_url}?{urlencode(params)}"

# WAIT HANDLERS 

def wait_for_jobs_to_load(driver, timeout=20):
    """
    Wait for job cards to load on the page.
    This is critical for Selenium + React sites.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/job-detail/')]"))
        )
        print("   [✓] Jobs loaded")
        return True
    except Exception as e:
        print(f"   [⚠] Load timeout: {str(e)[:50]}")
        return False

def wait_for_pagination(driver, timeout=10):
    """Wait for pagination buttons to appear"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[contains(text(), '2')]"))
        )
        return True
    except:
        return False

# PAGE NAVIGATION 

def load_page(driver, url, page_num=1):
    """Load a page with proper waits"""
    print(f"   [→] Loading page {page_num}...")
    driver.get(url)
    
    # Wait for jobs to appear
    if not wait_for_jobs_to_load(driver, timeout=20):
        print("   [⚠] Jobs didn't load, proceeding anyway...")
    
    # Additional JavaScript rendering time
    time.sleep(4)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    return BeautifulSoup(driver.page_source, 'html.parser')

# PAGINATION 

def get_total_pages(soup):
    """
    Extract total number of pages from pagination buttons.
    Pagination buttons are located at: button "1", button "2", button "13" etc.
    """
    try:
        buttons = soup.find_all('button')
        max_page = 1
        
        for button in buttons:
            text = button.get_text(strip=True)
            if text.isdigit():
                page_num = int(text)
                if page_num > 1:
                    max_page = max(max_page, page_num)
        
        print(f"   [✓] Detected {max_page} total pages")
        return max_page
    except Exception as e:
        print(f"   [⚠] Could not detect pages: {e}")
        return 1

def check_for_no_results(soup):
    """Check if page contains 'no jobs matching' error"""
    try:
        page_text = soup.get_text().lower()
        if "no jobs matching" in page_text or "no results found" in page_text:
            return True
    except:
        pass
    return False

# JOB EXTRACTION 

def extract_jobs_from_page(soup, base_url="https://www.timesjobs.com"):
    """
    Extract all job links and titles from current page.
    Each job card contains:
    - A link with href containing '/job-detail/'
    - An h2 heading with the job title
    """
    jobs = []
    seen_urls = set()
    
    try:
        # Find all anchor tags with job-detail links
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            
            if '/job-detail/' not in href:
                continue
            
            if href in seen_urls:
                continue
            
            seen_urls.add(href)
            
            # Build full URL
            full_url = base_url + href if href.startswith('/') else href
            
            title = "N/A"
            parent = link.find_parent('div')
            
            if parent:
                # Look for h2 heading (job title) in parent
                heading = parent.find('h2')
                if heading:
                    title = heading.get_text(strip=True)
            
            # Only add if we found a valid title
            if title and title != 'N/A':
                jobs.append({
                    "title": title,
                    "url": full_url
                })
        
        return jobs
    except Exception as e:
        print(f"   [!] Error extracting jobs: {e}")
        return []

# DETAIL PAGE SCRAPING 

def extract_company_from_detail(soup):
    """Extract company name from job detail page"""
    try:
        # h2 on detail page
        h2 = soup.find('h3', class_='inline mr-2')
        if h2:
            return h2.get_text(strip=True)
    except:
        pass
    return "N/A"

def extract_description_from_detail(soup):
    """
    Extract the full job description text from TimesJobs detail page.
    """
    
    rtd = soup.find("div", class_=lambda c: c and "rtd-content" in c)
    if rtd:
        text = rtd.get_text(" ", strip=True)
        if text and len(text) > 50:
            return text

    possible_blocks = soup.find_all(
        ['div', 'section', 'article'],
        class_=lambda c: c and ('jd-cont' in c or 'job-desc' in c or 'job-description' in c)
    )
    for block in possible_blocks:
        text = block.get_text(" ", strip=True)
        if text and len(text) > 50:
            return text

    try:
        desc_heading = None
        for tag in soup.find_all(['h2', 'h3', 'h4', 'h5']):
            if 'description' in tag.get_text(strip=True).lower():
                desc_heading = tag
                break

        if desc_heading:
            parts = []
            for sibling in desc_heading.find_next_siblings():
                txt = sibling.get_text(" ", strip=True)
                if txt:
                    parts.append(txt)
            if parts:
                return " ".join(parts)
    except:
        pass

    return "N/A"

def extract_skills_from_detail(soup):
    """
    Extract skills from job detail page.
    """
    try:
        skills_heading = None
        
        for element in soup.find_all(['h2', 'h3', 'h4', 'h5', 'heading']):
            element_text = element.get_text(strip=True).lower()
            if 'key skill' in element_text:
                skills_heading = element
                break
        
        if not skills_heading:
            print("   [⚠] Key Skills heading not found")
            return "N/A"
        
        # Collect all skills after the heading
        skills = []
        
        # Get all siblings after the Key Skills heading
        for sibling in skills_heading.find_next_siblings():
            # Stop if we hit another main heading (About Company, etc)
            if sibling.name and sibling.name.lower().startswith('h'):
                break
            
            # Get text from generic elements
            sibling_text = sibling.get_text(strip=True)
            
            # Filter for valid skill entries
            if sibling_text and len(sibling_text) > 0:
                # Exclude non-skill content
                if not any(exclude in sibling_text.lower() for exclude in 
                          ['year', 'experience', 'about', 'company', 'description', 
                           'required', 'please', 'call', 'opening', 'job id', 'location']):
                    skills.append(sibling_text)
        
        # Return as comma-separated string
        if skills:
            return ", ".join(skills)
        else:
            print("   [⚠] No skills extracted after heading found")
            return "N/A"
            
    except Exception as e:
        print(f"   [!] Error extracting skills: {str(e)[:60]}")
        return "N/A"


def extract_experience_from_detail(soup):
    """
    Extract experience (e.g. '4-7 Years') from TimesJobs detail page.
    Adjust selectors if TimesJobs changes its HTML.
    """
   
    return (soup.find_all("span", class_="mr-2 inline flex items-center")[1].get_text(strip=True))
   
def extract_salary_from_detail(soup):
    """
    Extract salary (e.g. '10-12 LPA', 'Not Disclosed by Recruiter').
    """
    spans = soup.find_all("span", class_="mr-2 inline flex items-center")
    if len(spans) >= 3:
        return spans[2].get_text(" ", strip=True)
    return "N/A"


def extract_label_value(detail_soup, label_text):
    """
    Generic helper to extract values like:
    Job Function: IT Software : Software Products & Services
    Industry: CRM/CallCentres/BPO/ITES/Med.Trans
    """
    try:
        # Look for li, div, or span that contains the label followed by ':'
        candidates = detail_soup.find_all(["li", "div", "span", "p"])
        target_prefix = (label_text + ":").lower()
        for tag in candidates:
            txt = tag.get_text(" ", strip=True)
            low = txt.lower()
            if low.startswith(target_prefix):
                # Return text after "Label:"
                return txt.split(":", 1)[1].strip()
    except Exception:
        pass
    return "N/A"
# MAIN SCRAPER 

def scrape_all_jobs(keyword="Python", location="Ahmedabad", max_pages=None, experience=None):
    """
    Main scraper function - orchestrates the entire scraping process.
    
    Phase 1: Collect all job links from all pages
    Phase 2: Visit each job detail page and extract information
    """
    driver = get_driver()
    base_url = "https://www.timesjobs.com"
    all_jobs = []
    
    try:
        #  PHASE 1: COLLECT LINKS 
        print(f"\n{'='*80}")
        print(f"PHASE 1: COLLECTING JOB LINKS FROM ALL PAGES")
        print(f"{'='*80}\n")
        
        # Load first page to detect total pages
        first_url = build_timesjobs_url(keyword=keyword, location=location, experience=experience, page=1)
        print(f"[*] First page URL:\n    {first_url}\n")
        
        soup = load_page(driver, first_url, page_num=1)
        
        # Check for errors BEFORE using any recommended/alternative jobs
        if check_for_no_results(soup):
            print("[!] ERROR: Website returned 'No jobs matching' message for this search.")
            print("[!] No jobs will be scraped for this query (ignoring suggested/other jobs).")
            print("[!] Possible reasons:")
            print("    1. Search parameters are too specific")
            print("    2. No jobs exist for this combination")
            print("    3. Site structure changed")
            return []
        
        # Detect total pages
        total_pages = get_total_pages(soup)
        
        if max_pages and max_pages < total_pages:
            total_pages = max_pages
            print(f"[*] Limited to {max_pages} pages (user preference)")
        
        print(f"[*] Will scrape {total_pages} pages\n")
        
        # LOOP THROUGH ALL PAGES 
        for page_num in range(1, total_pages + 1):
            print(f"\n[PAGE {page_num}/{total_pages}]")
            
            try:
                page_url = build_timesjobs_url(keyword=keyword, location=location, experience=experience, page=page_num)
                
                soup = load_page(driver, page_url, page_num=page_num)

                # If the site shows "no jobs matching", stop without using any
                # fallback/suggested jobs that might still appear on the page.
                if check_for_no_results(soup):
                    if page_num == 1 and not all_jobs:
                        print("   [!] This search has 0 real results on TimesJobs.")
                    else:
                        print(f"   [✓] Reached end of real results at page {page_num}")
                    break

                # Extract jobs from this page
                page_jobs = extract_jobs_from_page(soup, base_url)
                print(f"   [✓] Found {len(page_jobs)} jobs on this page")
                
                all_jobs.extend(page_jobs)
                
                # Respectful delay between pages
                if page_num < total_pages:
                    delay = random.uniform(3, 6)
                    print(f"   [⏱] Waiting {delay:.1f}s before next page...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"   [!] Error on page {page_num}: {str(e)[:60]}")
                continue
        
        # PHASE 2: SCRAPE DETAILS 
        print(f"\n{'='*80}")
        print(f"PHASE 2: SCRAPING DETAIL PAGES")
        print(f"{'='*80}\n")
        print(f"[*] Total jobs to process: {len(all_jobs)}\n")
        
        if len(all_jobs) == 0:
            print("[!] ERROR: No jobs collected!")
            return []
        
        processed = 0
        jobs_data = []
        
        # Process each job
        for idx, job in enumerate(all_jobs, 1):
            try:
                # Show progress
                sys.stdout.write(f"\r[{idx}/{len(all_jobs)}] {job['title'][:40]}...")
                sys.stdout.flush()
                
                # Load job detail page
                driver.get(job['url'])
                time.sleep(random.uniform(1, 2))
                
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extract information
                company = extract_company_from_detail(detail_soup)
                description = extract_description_from_detail(detail_soup)
                skills = extract_skills_from_detail(detail_soup)
                experience = extract_experience_from_detail(detail_soup)
                salary = extract_salary_from_detail(detail_soup)

                # Extra meta fields (label-based)
                job_function = extract_label_value(detail_soup, "Job Function")
                industry = extract_label_value(detail_soup, "Industry")
                specialization = extract_label_value(detail_soup, "Specialization")
                grad_courses = extract_label_value(detail_soup, "Graduate Courses")
                post_grad_courses = extract_label_value(detail_soup, "Post Graduate Courses")
                employment_type = extract_label_value(detail_soup, "Employment Type")
                job_type = extract_label_value(detail_soup, "Job Type")
                gender = extract_label_value(detail_soup, "Gender")
                
                # Store job data in dictionary
                job_data = {
                    "source": "TimesJobs",
                    "title": job['title'],
                    "company": company,
                    "url": job['url'],
                    "description": description,
                    "experience": experience,
                    "salary": salary,
                    "job_function": job_function,
                    "industry": industry,
                    "specialization": specialization,
                    "graduate_courses": grad_courses,
                    "post_graduate_courses": post_grad_courses,
                    "employment_type": employment_type,
                    "job_type": job_type,
                    "gender": gender,
                    "skills": skills
                }
                jobs_data.append(job_data)
                
                processed += 1
                
            except Exception as e:
                print(f"\n[!] Error processing job #{idx}: {e}")
                continue
        
        # Print completion message
        print(f"\n\n{'='*80}")
        print(f"✓ SCRAPING COMPLETE!")
        print(f"{'='*80}")
        print(f"[✓] Collected: {len(all_jobs)} jobs")
        print(f"[✓] Processed: {processed} job details")
        print(f"{'='*80}\n")
        
        return jobs_data
    except Exception as e:
        print(f"[!] Critical error in scrape_all_jobs: {e}")
        return []
    finally:
        # Ensure the driver is closed even if an error occurs
        driver.quit()


# CLI ENTRYPOINT 

if __name__ == "__main__":
    print("=" * 80)
    print("TimesJobs Multi-Page Scraper")
    print("=" * 80)
    print("Leave inputs blank to use defaults (keyword=Python, location=India, all pages)")
    print()

    try:
        keyword = input("Enter job keyword (e.g. Python Developer): ").strip() or "Python"
        location = input("Enter location (e.g. Ahmedabad): ").strip() or ""
        experience_input = input("Enter years of experience (optional, e.g. 2): ").strip()
        experience = int(experience_input) if experience_input.isdigit() else None
        max_pages_input = input("Enter maximum pages to scrape (blank for all): ").strip()
        max_pages = int(max_pages_input) if max_pages_input else None

        print("\n[*] Starting scraper...")
        scrape_all_jobs(keyword=keyword, location=location, max_pages=max_pages, experience=experience)
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.")
    except Exception as e:
        print(f"[!] Failed to start scraper: {e}")
