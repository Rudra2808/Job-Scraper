import os
import json
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from scraper.Talent_scraper import scrape_talent_com
from scraper.Timejobs_scraper import scrape_all_jobs

# Predefined cities (Indian cities)
PREDEFINED_CITIES = [
    "Ahmedabad",
    "Bangalore",
    "Chennai",
    "Delhi",
    "Gurgaon",
    "Hyderabad",
    "Kolkata",
    "Mumbai",
    "Pune",
    "Noida",
    "Jaipur",
    "Chandigarh",
    "Indore",
    "Kochi",
    "Coimbatore",
    "Vadodara",
    "Nagpur",
    "Lucknow",
    "Bhopal",
    "Visakhapatnam",
]

# Predefined job roles/designations
PREDEFINED_JOB_ROLES = [
    "Python Developer",
    "Java Developer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "React Developer",
    "Node.js Developer",
    "Angular Developer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Software Engineer",
    "Senior Software Engineer",
    "Software Architect",
    "Product Manager",
    "Project Manager",
    "Business Analyst",
    "QA Engineer",
    "Test Engineer",
    "UI/UX Designer",
    "Web Developer",
    "Mobile App Developer",
    "Android Developer",
    "iOS Developer",
    "Database Administrator",
    "System Administrator",
    "Network Engineer",
    "Cybersecurity Analyst",
    "Sales Executive",
    "Marketing Manager",
    "HR Manager",
    "Accountant",
    "Financial Analyst",
]

st.set_page_config(page_title="Job Scraper UI", layout="wide")

st.title("Job Scraper Dashboard")
st.write(
    "This Streamlit app lets you run the existing scrapers from `Talent_scraper.py` "
    "(Talent.com) and `Timejobs_scraper.py` (TimesJobs) with a simple UI."
)


def show_text_file(path: str, label: str):
    if not os.path.exists(path):
        st.warning(f"No `{path}` file found yet. Run the scraper first.")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    st.download_button(
        label=f"Download {label}",
        data=content,
        file_name=os.path.basename(path),
        mime="text/plain",
    )
    st.text_area(label, value=content, height=400)


def parse_jobs_file(path: str, source: str):
    """Parse the text output files into a structured list of jobs.

    This relies on the known 'Job #', 'Title:', 'Company:', 'URL:', 'Description:'
    (and optional 'Skills:') pattern used in t2.py and t3.py.
    """
    if not os.path.exists(path):
        return []

    jobs = []
    current = None

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            if line.startswith("Job #"):
                # Save previous job if any
                if current:
                    jobs.append(current)
                current = {
                    "source": source,
                    "title": "",
                    "company": "",
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
                    "url": "",
                    "description": "",
                    "skills": "",
                }
            elif current is not None:
                if line.startswith("Title:"):
                    current["title"] = line.split("Title:", 1)[1].strip()
                elif line.startswith("Company:"):
                    current["company"] = line.split("Company:", 1)[1].strip()
                elif line.startswith("Experience:"):
                    current["experience"] = line.split("Experience:", 1)[1].strip()
                elif line.startswith("Salary:"):
                    current["salary"] = line.split("Salary:", 1)[1].strip()
                elif line.startswith("Job Function:"):
                    current["job_function"] = line.split("Job Function:", 1)[1].strip()
                elif line.startswith("Industry:"):
                    current["industry"] = line.split("Industry:", 1)[1].strip()
                elif line.startswith("Specialization:"):
                    current["specialization"] = line.split("Specialization:", 1)[1].strip()
                elif line.startswith("Graduate Courses:"):
                    current["graduate_courses"] = line.split("Graduate Courses:", 1)[1].strip()
                elif line.startswith("Post Graduate Courses:"):
                    current["post_graduate_courses"] = line.split("Post Graduate Courses:", 1)[1].strip()
                elif line.startswith("Employment Type:"):
                    current["employment_type"] = line.split("Employment Type:", 1)[1].strip()
                elif line.startswith("Job Type:"):
                    current["job_type"] = line.split("Job Type:", 1)[1].strip()
                elif line.startswith("Gender:"):
                    current["gender"] = line.split("Gender:", 1)[1].strip()
                elif line.startswith("URL:"):
                    current["url"] = line.split("URL:", 1)[1].strip()
                elif line.startswith("Description:"):
                    desc = line.split("Description:", 1)[1].strip()
                    current["description"] = desc
                elif line.startswith("Skills:"):
                    skills = line.split("Skills:", 1)[1].strip()
                    current["skills"] = skills

    if current:
        jobs.append(current)

    return jobs


st.header("Combined Scraper (Talent.com + TimesJobs)")

col1, col2, col3 = st.columns(3)

with col1:
    designation_option = st.selectbox(
        "Designation / Job Title",
        options=["Select or type custom..."] + PREDEFINED_JOB_ROLES,
        index=1,  # Default to Python Developer
    )
    if designation_option == "Select or type custom...":
        designation = st.text_input("Or enter custom designation", value="Python Developer")
    else:
        designation = designation_option

with col2:
    city_option = st.selectbox(
        "City",
        options=["Select or type custom..."] + PREDEFINED_CITIES,
        index=1,  # Default to Ahmedabad
    )
    if city_option == "Select or type custom...":
        city = st.text_input("Or enter custom city", value="Ahmedabad")
    else:
        city = city_option

with col3:
    experience_years = st.number_input(
        "Experience (years, optional)", min_value=0, max_value=40, value=0, step=1
    )

if st.button("Run combined scraper"):

    designation_clean = designation.strip() or "Python"
    city_clean = city.strip() or "Ahmedabad"
    keyword_combined = designation_clean

    with st.spinner("Scraping Talent.com and TimesJobs... this may take a while."):
        # Run Talent.com scraper
        talent_jobs = scrape_talent_com(
            location=city_clean,
            keyword=keyword_combined,
            radius=None,
            date_posted=None,
            remote=None,
            promoted=None,
            job_type=None,
            company=None,
            page=1,
        )

        timesjobs_jobs = scrape_all_jobs(
            keyword=keyword_combined,
            location=city_clean,
            max_pages=None,
            experience=int(experience_years) if experience_years > 0 else None,
        )

    st.success(
        "Combined scraping completed. Merging results from both sites..."
    )
    
    if talent_jobs is None:
        talent_jobs = []
    if timesjobs_jobs is None:
        timesjobs_jobs = []

    st.session_state.talent_jobs = talent_jobs
    st.session_state.timesjobs_jobs = timesjobs_jobs
    st.session_state.merged_jobs = talent_jobs + timesjobs_jobs
    st.session_state.show_filter = "all"  # Default to showing all

    # Save merged jobs to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_json_path = f"output/merged_jobs_{timestamp}.json"
    with open(merged_json_path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.merged_jobs, f, indent=2, ensure_ascii=False)
    
    # Store JSON path in session state
    st.session_state.merged_json_path = merged_json_path

    st.write(
        f"Found **{len(talent_jobs)}** jobs from Talent.com and "
        f"**{len(timesjobs_jobs)}** jobs from TimesJobs. "
        f"Total merged jobs: **{len(st.session_state.merged_jobs)}**."
    )
    st.success(
        f"✅ Merged jobs saved to JSON file: `{merged_json_path}`"
    )

# Display filter buttons and data
if "merged_jobs" in st.session_state:
    st.subheader("Filter Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Show All Jobs", use_container_width=True):
            st.session_state.show_filter = "all"
    
    with col2:
        if st.button("Show Talent.com Only", use_container_width=True):
            st.session_state.show_filter = "talent"
    
    with col3:
        if st.button("Show TimesJobs Only", use_container_width=True):
            st.session_state.show_filter = "timesjobs"
    
    # Display filtered data
    st.subheader("Job Results")
    
    if st.session_state.show_filter == "all":
        jobs_to_show = st.session_state.merged_jobs
        st.info(f"Showing all **{len(jobs_to_show)}** jobs from both sources")
    elif st.session_state.show_filter == "talent":
        jobs_to_show = st.session_state.talent_jobs
        st.info(f"Showing **{len(jobs_to_show)}** jobs from Talent.com")
    else:  # timesjobs
        jobs_to_show = st.session_state.timesjobs_jobs
        st.info(f"Showing **{len(jobs_to_show)}** jobs from TimesJobs")
    
    if jobs_to_show:
        st.dataframe(jobs_to_show)
        
        # Download Excel button
        st.subheader("Download Data")
        if jobs_to_show:
            # Convert jobs data to DataFrame
            df = pd.DataFrame(jobs_to_show)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Jobs')
                # Auto-adjust column widths
                worksheet = writer.sheets['Jobs']
                from openpyxl.utils import get_column_letter
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                        len(str(col))
                    )
                    # Limit max width to 50 for readability
                    max_length = min(max_length, 50)
                    column_letter = get_column_letter(idx)
                    worksheet.column_dimensions[column_letter].width = max_length + 2
            
            output.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"merged_jobs_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 Download Merged Jobs Excel",
                data=output,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.warning(
            "No jobs to display. Please run the scraper first or check that the scrapers ran successfully."
        )
