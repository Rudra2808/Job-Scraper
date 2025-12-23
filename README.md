# Job Aggregation Tool (Python + Selenium/BS4)

## 📌 Project Overview
This tool is a **Job Scraping System** designed to scrape, normalize, and combine job listings from multiple job portals into a single structured dataset. It was developed as part of the **Coding Logical Test (2nd Interview Round)**.

The tool currently supports scraping from:
1.  **Talent.com** (Assigned Portal)
2.  **TimesJobs** (Selected 2nd Portal)

It features a **Streamlit Web UI** for easy interaction and exports data to both **JSON** and **Excel** formats.

---

## 🛠️ Tech Stack & Libraries
* **Language:** Python 3.x
* **Scraping Tools:**
    * `Selenium` (for dynamic content & navigation)
    * `BeautifulSoup` (bs4) (for HTML parsing)
* **Frontend / UI:** `Streamlit`
* **Data Handling:** `Pandas`, `JSON`
* **Utilities:** `datetime`, `urllib`

---

## 📂 Project Structure
```text
job_scraper/
│
├── scraper/
│   ├── Talent_scraper.py   # Scraper logic for Talent.com
│   ├── Timejobs_scraper.py # Scraper logic for TimesJobs
│
├── output/                 # Folder where JSON/Excel files are saved
│
├── main.py                 # Main application (Streamlit UI + Controller)
├── requirements.txt        # List of dependencies
└── README.md               # Project documentation
```

## 🚀 How to Run the Project

### 1. Prerequisites
Ensure you have Python (3.8 or higher) installed on your system. You also need the Google Chrome browser installed, as Selenium uses it for automation.

### 2. Set Up a Virtual Environment (Recommended)
It is best practice to run this project in a virtual environment to avoid conflicts.

**For Windows:**

```bash
# Create the environment
python -m venv venv

# Activate the environment
.\venv\Scripts\activate
```

**For macOS / Linux:**

```bash
# Create the environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate
```

You will know it is activated when you see `(venv)` at the start of your terminal line.

### 3. Install Dependencies
Once the environment is active, install the required libraries:

```bash
pip install selenium beautifulsoup4 streamlit pandas openpyxl requests
```

### 4. Run the Application
Execute the main.py file using Streamlit:

```bash
streamlit run main.py
```

### 5. Usage
A web interface will open in your browser (usually at http://localhost:8501).

1. **Select Job Role:** Choose from the dropdown (e.g., "Python Developer") or type a custom role.
2. **Select Location:** Choose a city (e.g., "Ahmedabad") or type a custom location.
3. **Set Experience:** Optionally filter by years of experience.
4. **Click "Run combined scraper".**
5. **Wait for the process to finish.** The tool will:
   - Launch headless Chrome browsers to scrape both sites.
   - Merge the results.
   - Display the data in a table.
6. **Download:** Click the buttons to download the results as JSON or Excel.

---

## 📊 Sample Input & Output

### Input Criteria
- **Designation:** Python Developer
- **City:** Ahmedabad
- **Experience:** 0 Years

### Output Data (JSON Format)
The tool generates a structured JSON file (e.g., `merged_jobs_20251223.json`):

```json
[
  {
    "source": "Talent.com",
    "title": "Junior Python Developer",
    "company": "Tech Solutions Ltd",
    "url": "https://in.talent.com/view?id=...",
    "description": "We are looking for a python developer...",
    "skills": "Python, Django, SQL"
  },
  {
    "source": "TimesJobs",
    "title": "Python Engineer",
    "company": "Global IT Services",
    "url": "https://www.timesjobs.com/job-detail/...",
    "experience": "0-3 Years",
    "salary": "3.5 - 5.0 LPA"
  }
]
```

---

## ⚠️ Challenges Faced & Solutions

### 1. Dynamic Content Loading
**Challenge:** Talent.com uses infinite scrolling and lazy loading, meaning not all jobs are visible in the initial HTML.

**Solution:** Implemented Selenium to simulate a real browser, scrolling down (`window.scrollTo`) to trigger JavaScript events before passing the HTML to BeautifulSoup.

### 2. Anti-Bot Detection
**Challenge:** Frequent requests caused connection timeouts or blocking.

**Solution:** Added random time delays (`time.sleep(random.uniform(2, 4))`) and rotated User-Agent headers to mimic human behavior.

### 3. Inconsistent HTML Structure
**Challenge:** TimesJobs detail pages vary significantly; some use different class names for "Job Description" or "Skills".

**Solution:** Wrote robust fallback logic (e.g., if `class="job-desc"` isn't found, search for headers containing the text "Job Description").

---

## ✅ Bonus Features Implemented
* **Frontend UI:** Built a fully interactive dashboard using Streamlit.
* **Excel Export:** Used Pandas to allow users to download clean .xlsx reports.
* **Deep Scraping:** The tool doesn't just grab the list; it visits every job link to extract full descriptions and skills.

