import streamlit as st
import requests
import pandas as pd
import feedparser
from bs4 import BeautifulSoup
import base64
import time
from streamlit_lottie import st_lottie
import json

# Function to load and display Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Function to get base64 encoded image
def get_base64_from_url(url):
    response = requests.get(url)
    return base64.b64encode(response.content).decode("utf-8")

# Set page config with a favicon
st.set_page_config(
    page_title="Patient Corner",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for animations and styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 6px 6px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4285F4;
        color: white;
    }
    
    .card {
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 6px 10px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        margin-bottom: 20px;
        background-color: white;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.12);
    }
    
    .hospital-card {
        border-left: 5px solid #4285F4;
    }
    
    .news-card {
        border-left: 5px solid #0F9D58;
    }
    
    .book-card {
        border-left: 5px solid #F4B400;
    }
    
    .button-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 20px 0;
    }
    
    .custom-button {
        padding: 12px 24px;
        border-radius: 8px;
        background-color: #4285F4;
        color: white;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        border: none;
        font-weight: 500;
        width: calc(33.33% - 10px);
        min-width: 200px;
    }
    
    .custom-button:hover {
        background-color: #3367D6;
        transform: translateY(-2px);
    }
    
    .sidebar-icon {
        margin-right: 10px;
        vertical-align: middle;
    }
    
    .fade-in {
        animation: fadeIn 1s ease-in;
    }
    
    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    
    .slide-in {
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        0% { transform: translateX(-20px); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .symptom-tag {
        display: inline-block;
        background-color: #f1f3f4;
        padding: 5px 10px;
        border-radius: 20px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.9em;
        border: 1px solid #dadce0;
    }
    
    .header-container {
        display: flex;
        align-items: center;
        padding: 10px;
        background-color: #f0f8ff;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .logo-container {
        margin-right: 20px;
    }
    
    .header-text {
        flex-grow: 1;
    }
    
    .specialty-tag {
        display: inline-block;
        background-color: #e6f2ff;
        padding: 5px 10px;
        border-radius: 20px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.9em;
        border: 1px solid #b8daff;
    }
    
    /* Custom loader */
    .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 2s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# Load animations
lottie_medical = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_5njp3vgg.json")
lottie_games = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_xedpyc2z.json")
lottie_news = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_qp1q7mct.json")
lottie_books = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_v7KhZ2.json")
lottie_hospital = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_q4h7dqj6.json")
lottie_brain = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_hgxntv6m.json")

# Define logos
logos = {
    "medical": "https://cdn-icons-png.flaticon.com/512/4320/4320377.png",
    "games": "https://cdn-icons-png.flaticon.com/512/5211/5211735.png",
    "news": "https://cdn-icons-png.flaticon.com/512/2965/2965879.png",
    "books": "https://cdn-icons-png.flaticon.com/512/1245/1245679.png",
    "brain": "https://cdn-icons-png.flaticon.com/512/4743/4743009.png",
    "hospital": "https://cdn-icons-png.flaticon.com/512/2785/2785544.png",
    "policies": "https://cdn-icons-png.flaticon.com/512/3426/3426653.png"
}

# Define game categories with links to Poki
game_categories = {
    "Action Games": "https://poki.com/en/action",
    "Puzzle Games": "https://poki.com/en/puzzle",
    "Shooting Games": "https://poki.com/en/shooting",
    "Racing Games": "https://poki.com/en/racing",
    "Adventure Games": "https://poki.com/en/adventure",
    "Multiplayer Games": "https://poki.com/en/multiplayer",
    "Games for Girls": "https://poki.com/en/girls",
    "2 Player Games": "https://poki.com/en/2-player",
    ".io Games": "https://poki.com/en/io",
    "Funny Games": "https://poki.com/en/funny"
}

# Define news feeds for different languages
news_feeds = {
    "English": [
        {
            "name": "The Hindu",
            "url": "https://www.thehindu.com/life-and-style/fitness/feeder/default.rss",
            "logo": "https://www.thehindu.com/theme/images/th-online/logo.png"
        },
        {
            "name": "Times of India",
            "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "logo": "https://static.toiimg.com/photo/47529300.cms"
        },
        {
            "name": "NDTV",
            "url": "https://feeds.feedburner.com/ndtvcooks-latest",
            "logo": "https://th.bing.com/th/id/ODLS.1e22eac8-4860-4eb6-8f7d-319557e2aaf0?w=32&h=32&qlt=90&pcl=fffffc&o=6&pid=1.2"
        }
    ],
    "Marathi": [
        {
            "name": "Maharashtra Times",
            "url": "https://maharashtratimes.com/rssfeedsdefault.cms",
            "logo": "https://static.langimg.com/thumb/119164309/maharashtra-times.jpg?width=597&resizemode=4"
        },
        {
            "name": "Lokmat",
            "url": "https://www.lokmat.com/rss/india.xml",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAbFBMVEUEBAQCAgKioqLn5+ft7e3w8PDW1tZpaWn////////////7+/sBAQH509T3wMP4+Pj0sLLpS0/hAADjAAHqXGHjAA7nNTv85+j09PTvhYj////619jxmJvvgYX96+3lHCTtcHT0rK/3xMfgAABX3FmCAAAAIXRSTlMCBypyhZdQHNjl39EM4OTA5/n///3//t2y7v//6/////2ZvYRMAAABdElEQVR4AWWTBZLkMAxFHZYd6rZC62xw7n/H+XKwatRgeBEryksQBCoIozhJ4jQ8jrdgn8WkjYjWeVQ8VHaxNkRUVlWJRVOKy4tltSb6fK0INxVwcuqC5Yaq1nLrxdquJz0IFcXa0D/bPsL2A12xLP7ejL12RToVGGr63MxyZ1nWnnKxmxjimzXOja3F5iuqqjD0/zFqJ+fmhbEpqVYq1SQHZkacLQt1HfYr6UJFpofi0nVdu61YlmafxNICu3BZWTw37vvm3LTvI1QXH5KJ1OBjtd95Hp1rxu1nFbNvyIu7ZH3DwyxMMn4A0wseAdndzXZx03JDloAklY4BXYP4uxPaI5WjCBY30G1b/KNIO2BpBnQF5ZPKzHNjseyN3faFr/Kh8BISxDdTtuwLX8Bs8G4Z5G5ZgZYVR7P5hYTFAICFH5PlGZOvjAlYoDwd/g5YAUWIrJHxo1mWPQHl6clOmsW51sdQ11GBi5OBCi7C1L8OWXCzX0ieLYWbeLpCAAAAAElFTkSuQmCC"
        },
        {
            "name": "Loksatta",
            "url": "http://zeenews.india.com/marathi/rss/health-news.xml",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAbFBMVEX/AAD/YGD/pqb/srL/bW3/KCj/5ub/////3Nz/Fxf/8/P/SEj/j4//19f/+vr/7Oz/zs7/ra3/pKT/oqL/n5//nZ3/aGj/gID/y8v/29v/iIj/Dg7/ODj/cnL/WFj/Hx//Ly//d3f/Pj7/vLxDZSjZAAAAxklEQVR4AcWQRQKAQAgAsbu76/9/FLDr7Fi4swHA/wiiJH8oRdUQ3XiVqqkxFrwjs7fhA4es67nv1teIYM0wEMUwDKMoipEksV10XpyyjLRXRJaZnxO0m5ozVE9RwokKh6IlxKg+RBNFmUVZWK2B086ldqZ2wqkuUqchabcqnGSPsQ8waEUzNrTJeJIyxhl+p21mepMDbJA4n7k0y+BYwZ/zmdyiZDAn0PIJWyddJCRcggExffNznUwrdMv5TY9NmKQJP/8wAyoNDbHrJtsXAAAAAElFTkSuQmCC"
        }
    ],
    "Hindi": [
        {
            "name": "Dainik Bhaskar",
            "url": "https://www.bhaskar.com/rss-v1--category-7911.xml",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcBAMAAACAI8KnAAAAJFBMVEVHcEz3nRD8nxL7nhP8nhL6nRT7nBT5nBX6nBb5nBb5nBb5nBg5wgKHAAAAC3RSTlMADBsvRmeHpsHZ7lsu8oMAAACySURBVHgBVc7hEQQRDAXgUIHoQFRw+m/htoToQHTgHmbt3psxfF5+hFZYUlgPT0gUJC0uZcl5GXSocikiYVGQT1zjoIuxJMdRUgxgTMKEwEwe/xha5oSWOWw64eCZMbrDoEN54jy9gDbQGZ5rOPe0/8PImx0co98cIHBo5nFuWh/eXrTuybRutcnRbHO0ajRbrZ3m1UD8tq9aa1prB6mp6leRurdS5LpUz+6SSwr05H7/AFnDToXr4wcyAAAAAElFTkSuQmCC"
        },
        {
            "name": "Navbharat Times",
            "url": "https://navbharattimes.indiatimes.com/rssfeedsdefault.cms",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAZlBMVEUzLmYxLGUyLWYwKmcyLGciGl7Avs3////v7/QVC1gjHV+1s8X5+fvh4ekZEFkpI2EUCFp9e5onIWCDgZ4fF10SAlqIhqL09PfV1d6Zl645NGtJRXVCPXLOzdguKWOnpblkYYdZVX/Qvt+3AAAAj0lEQVR4AczNhRHDMBBE0ZPpYmbG/ptMYl5rrgC/AcEX0FsppDXDRNYj2w6jj4vR8zk48H8WRoRib2cnzKmbGdqnO+Ux5zG2HUQ9xYW9KYUYV/VBiEXDByFm7X+36fp+ECLZ/6tjNE22FJU3N8tE5EEEXmGSEJH3G9mSQuzsYjglWRQVZRhxJgk5OaDcAAIA1uEI9tbLHYQAAAAASUVORK5CYII="
        },
        {
            "name": "Amar Ujala",
            "url": "https://www.amarujala.com/rss/india-news.xml",
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAgVBMVEX9/f38/Pzu7O3v7e7w7u/t6+zs6uvq6Onx7/Dr6ery8PH39fb8+vutrq4WFhYAAACbmppFQ0RJRkdQTU5BQUHd3N0bGBlSUVKRkJAUEBGDgoLCwcGIh4dtbW1eXl65uLhkYmOVlJQsLCzIx8fOzc6lpaX8/fx6eXnU09Q7OjskISKytJ4LAAABVElEQVR4AXXOh3qDIBSG4SMcRDH2d9TR7ETNuv8L7CGb9OnnAl4XEUUUFt0jSemP2MT2GlGkmDn5jJVJbeTxXsguMXcM9R6Tx7AAjZYVR5TN7kWSe6LWLv9CUVZ1JXtdV+W3fkNusrbrQT/zBawlLDNm1tH9ydkK8zU01nNssMXG3VGJLRoq0Mu23iHt0GTqhUmzz7+FmnLYoLFY5TZ5oGjcz5vFPMncOLdyTO75TXbOZZnfJX/yI9YeY22HYRwkuYzj/TI2rA4em+KIYzFN+RHy01Mx1djilFxRsVlhnO3OXY0cw/68vbQFHHtMjYtz5BMNmASPGKoCBZIbZueGLuW+GbEUnINo+UJlK2BzArY5Jgznr2aOHZhVJGhUZrXjpHGxNdY4y6mNrdI3NEYpf/JX7XctyZKgjU2YundDnwkL8a+H+OnpgcgGpanstyxJ0T8R/QKbih6IckmOQwAAAABJRU5ErkJggg=="
        }
    ]
}

# Define hospital data
hospitals = [
    
    {
        "name": "All India Institute of Medical Sciences (AIIMS)",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi, Delhi 110029",
        "phone": "011-2658 8500",
        "specialties": ["Neurology", "Oncology", "Cardiology"],
        "website": "https://www.aiims.edu"
    },
    {
        "name": "Tata Memorial Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "Dr. E Borges Road, Parel, Mumbai, Maharashtra 400012",
        "phone": "022-2417 7000",
        "specialties": ["Cancer Treatment", "Neurosurgery", "Research"],
        "website": "https://tmc.gov.in"
    },
    {
        "name": "Apollo Hospitals",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "division": "South",
        "address": "21, Greams Lane, Off Greams Road, Chennai, Tamil Nadu 600006",
        "phone": "044-2829 3333",
        "specialties": ["Neurosurgery", "Oncology", "Cardiology"],
        "website": "https://www.apollohospitals.com"
    },
    {
        "name": "Fortis Memorial Research Institute",
        "city": "Gurugram",
        "state": "Haryana",
        "division": "North",
        "address": "Sector 44, Opposite HUDA City Centre, Gurugram, Haryana 122002",
        "phone": "0124-4921 000",
        "specialties": ["Neuroscience", "Cancer Care", "Cardiac Sciences"],
        "website": "https://www.fortishealthcare.com"
    },
    {
        "name": "Manipal Hospitals",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "98, HAL Old Airport Road, Bangalore, Karnataka 560017",
        "phone": "080-2502 4444",
        "specialties": ["Neurology", "Oncology", "Multi-specialty"],
        "website": "https://www.manipalhospitals.com"
    },
    {
        "name": "Max Super Specialty Hospital",
        "city": "Saket",
        "state": "Delhi",
        "division": "North",
        "address": "Press Enclave Road, Saket, New Delhi, Delhi 110017",
        "phone": "011-2651 5050",
        "specialties": ["Cardiology", "Neuro Sciences", "Orthopaedics"],
        "website": "https://www.maxhealthcare.in"
    },
    {
        "name": "Medanta - The Medicity",
        "city": "Gurugram",
        "state": "Haryana",
        "division": "North",
        "address": "Sector 38, Gurgaon, Haryana 122001",
        "phone": "0124-4141414",
        "specialties": ["Cardiology", "Neurosurgery", "Kidney Transplant"],
        "website": "https://www.medanta.org"
    },
    {
        "name": "CK Birla Hospital",
        "city": "Gurugram",
        "state": "Haryana",
        "division": "North",
        "address": "Near Huda City Centre, Sector 51, Gurugram, Haryana 122018",
        "phone": "0124-4606600",
        "specialties": ["Obstetrics", "Gynaecology", "Paediatrics"],
        "website": "https://www.ckbhospital.com"
    },
    {
        "name": "Kokilaben Dhirubhai Ambani Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "Four Bungalows, Andheri West, Mumbai, Maharashtra 400053",
        "phone": "022-4269 6969",
        "specialties": ["Cancer Care", "Cardiology", "Neurosurgery"],
        "website": "https://www.kokilabenhospital.com"
    },
    {
        "name": "Christian Medical College",
        "city": "Vellore",
        "state": "Tamil Nadu",
        "division": "South",
        "address": "Ida Scudder Road, Vellore, Tamil Nadu 632004",
        "phone": "0416-2281000",
        "specialties": ["Cancer Treatment", "Cardiology", "Orthopaedics"],
        "website": "https://www.cmch-vellore.edu"
    },
    
    {
        "name": "National Institute of Mental Health and Neurosciences (NIMHANS)",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "Hosur Road, Bangalore, Karnataka 560029",
        "phone": "080-2699 5000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Surgery", "Neuro-oncology"],
        "website": "https://www.nimhans.ac.in"
    },
    {
        "name": "Jaslok Hospital and Research Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "15, Dr. G Deshmukh Marg, Mumbai, Maharashtra 400026",
        "phone": "022-6657 3333",
        "specialties": ["Stereotactic Surgery", "Functional Neurosurgery", "Brain Tumor Surgery", "DBS Therapy"],
        "website": "https://www.jaslokhospital.net"
    },
    {
        "name": "Narayana Health (Narayana Hrudayalaya)",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "258/A, Bommasandra Industrial Area, Anekal Taluk, Bangalore, Karnataka 560099",
        "phone": "080-7122 2200",
        "specialties": ["Brain Tumor Surgery", "Stereotactic Radiosurgery", "Gamma Knife Surgery", "Neurorehabilitation"],
        "website": "https://www.narayanahealth.org"
    },
    {
        "name": "Aster Medcity",
        "city": "Kochi",
        "state": "Kerala",
        "division": "South",
        "address": "Kuttisahib Road, Near Kothad Bridge, South Chittoor, Cheranalloor, Kochi, Kerala 682027",
        "phone": "0484-6699 999",
        "specialties": ["Advanced Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Surgery", "Neuro-oncology"],
        "website": "https://www.astermedcity.com"
    },
    {
        "name": "Indraprastha Apollo Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Sarita Vihar, Delhi Mathura Road, New Delhi, Delhi 110076",
        "phone": "011-7179 1090",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Spine Surgery", "Gamma Knife Radiosurgery"],
        "website": "https://www.apollohospitals.com"
    },
    {
        "name": "Fortis Flt. Lt. Rajan Dhall Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Sector B, Pocket A-1, Aruna Asaf Ali Marg, Vasant Kunj, New Delhi, Delhi 110070",
        "phone": "011-4277 6222",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Neurosurgery", "Neuro-oncology"],
        "website": "https://www.fortishealthcare.com"
    },
    {
        "name": "Bombay Hospital and Medical Research Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "12, New Marine Lines, Mumbai, Maharashtra 400020",
        "phone": "022-2206 7676",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Skull Base Surgery", "Pediatric Neurosurgery"],
        "website": "https://www.bombayhospital.com"
    },
    {
        "name": "Sir Ganga Ram Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Rajinder Nagar, New Delhi, Delhi 110060",
        "phone": "011-2575 0000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Surgery", "Neuro-critical Care"],
        "website": "https://www.sgrh.com"
    },
    {
        "name": "Ruby Hall Clinic",
        "city": "Pune",
        "state": "Maharashtra",
        "division": "West",
        "address": "40, Sassoon Road, Pune, Maharashtra 411001",
        "phone": "020-2612 6700",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Endoscopic Surgery", "Neuro-rehabilitation"],
        "website": "https://www.rubyhall.com"
    },
    {
        "name": "Global Hospital",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "division": "South",
        "address": "439, Cheran Nagar, Perumbakkam, Chennai, Tamil Nadu 600100",
        "phone": "044-4444 1000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Radiosurgery", "Multi-organ Transplant"],
        "website": "https://www.globalhospitalsindia.com"
    },
    {
        "name": "Institute of Neurosciences Kolkata",
        "city": "Kolkata",
        "state": "West Bengal",
        "division": "East",
        "address": "185, AJC Bose Road, Kolkata, West Bengal 700017",
        "phone": "033-2287 2321",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Epilepsy Surgery", "Neuro-interventional Procedures"],
        "website": "https://www.instituteofneurosciences.net"
    },
    {
        "name": "Neurological Surgery Centre, King George Medical University",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "division": "North",
        "address": "Chowk, Lucknow, Uttar Pradesh 226003",
        "phone": "0522-2257540",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Pediatric Neurosurgery", "Neuro-trauma"],
        "website": "https://www.kgmcindia.edu"
    },
    {
        "name": "BGS Gleneagles Global Hospital",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "67, Uttarahalli Road, Kengeri, Bangalore, Karnataka 560060",
        "phone": "080-6121 4444",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Robotic Surgery", "Minimally Invasive Procedures"],
        "website": "https://www.bgsglobalhospitals.com"
    },
    
   
    {
        "name": "P.D. Hinduja Hospital & Medical Research Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "Veer Savarkar Marg, Mahim, Mumbai, Maharashtra 400016",
        "phone": "022-2444 9199",
        "specialties": ["Neurosurgery", "Cerebrovascular Surgery", "Skull Base Surgery", "Gamma Knife Radiosurgery"],
        "website": "https://www.hindujahospital.com"
    },
    {
        "name": "Lilavati Hospital & Research Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "A-791, Bandra Reclamation, Bandra West, Mumbai, Maharashtra 400050",
        "phone": "022-2675 1000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Spine Surgery", "Neuro-critical Care"],
        "website": "https://www.lilavatihospital.com"
    },
    {
        "name": "Wockhardt Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "1877, Dr Anand Rao Nair Road, Near Agripada Police Station, Mumbai Central, Mumbai, Maharashtra 400011",
        "phone": "022-2659 9000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Surgery", "Neuro-rehabilitation"],
        "website": "https://www.wockhardthospitals.com"
    },
    {
        "name": "Hiranandani Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "Hillside Avenue, Hiranandani Gardens, Powai, Mumbai, Maharashtra 400076",
        "phone": "022-2576 3300",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Endoscopic Surgery", "Pediatric Neurosurgery"],
        "website": "https://www.hiranandanihospital.org"
    },
    {
        "name": "Marengo CIMS Hospital",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "division": "West",
        "address": "Nr. Shukan Mall, Off Science City Road, Sola, Ahmedabad, Gujarat 380060",
        "phone": "079-3010 1010",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Surgery", "Neuro-oncology"],
        "website": "https://www.cims.org"
    },
    {
        "name": "Vikram Hospital",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "No.70/1, Millers Road, Vasanth Nagar, Bangalore, Karnataka 560052",
        "phone": "080-2227 7979",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Functional Neurosurgery", "Neuro-interventional Procedures"],
        "website": "https://www.vikramhospital.com"
    },
    {
        "name": "Columbia Asia Hospital",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "Kirloskar Business Park, Bellary Road, Hebbal, Bangalore, Karnataka 560024",
        "phone": "080-4962 8888",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Neurosurgery", "Neuro-critical Care"],
        "website": "https://www.columbiaasia.com"
    },
    {
        "name": "Sakra World Hospital",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "Sy No 52/2, Devarabeesanahalli, Varthur Hobli, Outer Ring Road, Bangalore, Karnataka 560103",
        "phone": "080-4969 4969",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Robotic Surgery", "Stereotactic Radiosurgery"],
        "website": "https://www.sakraworldhospital.com"
    },
    {
        "name": "Fortis Hospital Bannerghatta Road",
        "city": "Bangalore",
        "state": "Karnataka",
        "division": "South",
        "address": "154/9, Opposite IIM-B, Bannerghatta Road, Bangalore, Karnataka 560076",
        "phone": "080-6621 4444",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Spine Surgery", "Neuro-oncology"],
        "website": "https://www.fortishealthcare.com"
    },
    {
        "name": "Sterling Hospital",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "division": "West",
        "address": "Off Gurukul Road, Behind Drive-in Cinema, Memnagar, Ahmedabad, Gujarat 380052",
        "phone": "079-6677 0000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Endovascular Surgery", "Neuro-rehabilitation"],
        "website": "https://www.sterlinghospitals.com"
    },
    {
        "name": "Shalby Hospital",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "division": "West",
        "address": "SG Highway, Near Kiran Motors, Gota, Ahmedabad, Gujarat 382481",
        "phone": "079-4040 4040",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Surgery", "Neuro-critical Care"],
        "website": "https://www.shalbyhospitals.org"
    },
    {
        "name": "Yashoda Hospitals",
        "city": "Hyderabad",
        "state": "Telangana",
        "division": "South",
        "address": "Behind Hari Hara Kala Bhavan, S.P. Road, Secunderabad, Telangana 500003",
        "phone": "040-2378 5678",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Surgery", "Pediatric Neurosurgery"],
        "website": "https://www.yashodahospitals.com"
    },
    {
        "name": "KIMS Hospital",
        "city": "Hyderabad",
        "state": "Telangana",
        "division": "South",
        "address": "1-8-31/1, Minister Rd, Krishna Nagar Colony, Begumpet, Hyderabad, Telangana 500003",
        "phone": "040-4488 5000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Gamma Knife Surgery", "Neuro-interventional Procedures"],
        "website": "https://www.kimshospitals.com"
    },
    {
        "name": "Continental Hospitals",
        "city": "Hyderabad",
        "state": "Telangana",
        "division": "South",
        "address": "IT Park Rd, Nanakram Guda, Gachibowli, Hyderabad, Telangana 500032",
        "phone": "040-6737 0000",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Robotic Surgery", "Advanced Neuro-oncology"],
        "website": "https://www.continentalhospitals.com"
    },
    {
        "name": "Apollo Hospitals Jubilee Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "division": "South",
        "address": "Road No. 72, Opp. Bharatiya Vidya Bhavan, Film Nagar, Jubilee Hills, Hyderabad, Telangana 500033",
        "phone": "040-2360 7777",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Radiosurgery", "Functional Neurosurgery"],
        "website": "https://www.apollohospitals.com"
    },
    {
        "name": "Breach Candy Hospital Trust",
        "city": "Mumbai",
        "state": "Maharashtra",
        "division": "West",
        "address": "60-A, Bhulabhai Desai Road, Breach Candy, Mumbai, Maharashtra 400026",
        "phone": "022-2367 8888",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Skull Base Surgery", "Neuro-critical Care"],
        "website": "https://www.breachcandyhospital.org"
    },
    {
        "name": "Artemis Hospital",
        "city": "Gurugram",
        "state": "Haryana",
        "division": "North",
        "address": "Sector 51, Golf Course Extension Road, Gurugram, Haryana 122001",
        "phone": "0124-451 1111",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Minimally Invasive Surgery", "Neuro-rehabilitation"],
        "website": "https://www.artemishospital.com"
    },
    {
        "name": "Paras Hospital",
        "city": "Gurugram",
        "state": "Haryana",
        "division": "North",
        "address": "C-1, Sushant Lok Phase-I, Sector-43, Gurugram, Haryana 122002",
        "phone": "0124-458 5858",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Stereotactic Surgery", "Pediatric Neurosurgery"],
        "website": "https://www.parashospitals.com"
    },
    {
        "name": "BLK Super Speciality Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Pusa Road, Rajinder Nagar, New Delhi, Delhi 110005",
        "phone": "011-3040 3040",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Gamma Knife Surgery", "Neuro-interventional Procedures"],
        "website": "https://www.blkhospital.com"
    },
    {
        "name": "Venkateshwar Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "division": "North",
        "address": "Sector 18A, Dwarka, New Delhi, Delhi 110075",
        "phone": "011-4040 4040",
        "specialties": ["Neurosurgery", "Brain Tumor Surgery", "Endoscopic Surgery", "Neuro-critical Care"],
        "website": "https://www.venkateshwarhospital.com"
    }
]

# Define books data

books = [
    {
        "title": "Orientation to Caregiving  ",
        "author": "MPH1 Michael Rabow, Susan Folkman",
        "description": "Comprehensive guide covering brain tumor basics, treatment options, and care strategies.",
        "link": "https://braintumorcenter.ucsf.edu/sites/default/files/2022-04/3rd%20EditionCaregiver.pdf",
        "language": "English",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997873.png"
    },
    {
        "title": "Understanding Brain Tumors",
        "author": "National Cancer Institute",
        "description": "Patient guide to brain tumor diagnosis, treatment, and recovery.",
        "link": "https://www.cancer.gov/types/brain",
        "language": "English",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997714.png"
    },
    {
        "title": "Brain Tumor Handbook",
        "author": "American Brain Tumor Association",
        "description": "Educational resource for patients and families dealing with brain tumors.",
        "link": "https://www.abta.org/about-brain-tumors/brain-tumor-education/",
        "language": "English",
        "cover": "https://cdn-icons-png.flaticon.com/512/3376/3376599.png"
    },
    {
        "title": "मस्तिष्क ट्यूमरच्या उपचारांचा मार्गदर्शक",
        "author": "भारत सरकार",
        "description": "मस्तिष्क ट्यूमर आणि उपचारावरील मार्गदर्शन.",
        "link": "https://www.healzone.co.in/blog-details/brain-tumor-treatment-in-india-a-comprehensive-guide",
        "language": "Marathi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997757.png"
    },
    {
        "title": "मस्तिष्क कर्करोगासंबंधी माहिती",
        "author": "मनोविकार संस्था",
        "description": "मस्तिष्क कर्करोगावर संशोधन आणि त्याचे उपचार.",
        "link": "hhttps://marathivishwakosh.org/4221/",
        "language": "Marathi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997809.png"
    },
    {
        "title": "ब्रेन ट्यूमरच्या लक्षणांची ओळख",
        "author": "आंतरराष्ट्रीय कर्करोग संस्था",
        "description": "ब्रेन ट्यूमरच्या लक्षणांची आणि त्यांच्या उपचारांची माहिती.",
        "link": "https://my.clevelandclinic.org/health/diseases/6149-brain-cancer-brain-tumor",
        "language": "Marathi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997794.png"
    },
    {
        "title": "ब्रेन ट्यूमर: लक्षण और उपचार",
        "author": "आयुष मंत्रालय",
        "description": "ब्रेन ट्यूमर की पहचान और उपचार के तरीके.",
        "link": "https://www.mayoclinic.org/diseases-conditions/brain-tumor/symptoms-causes/syc-20350084",
        "language": "Hindi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997801.png"
    },
    {
        "title": "ब्रेन ट्यूमर का गाइड",
        "author": "नेशनल कैंसर संस्थान",
        "description": "ब्रेन ट्यूमर के लक्षण, निदान और उपचार की जानकारी.",
        "link": "https://www.maxhealthcare.in/blogs/hi/brain-tumors-symptoms-and-types",
        "language": "Hindi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3376/3376589.png"
    },
    {
        "title": "ब्रेन ट्यूमर: उपचार और देखभाल",
        "author": "आधिकारिक चिकित्सा पद्धति",
        "description": "ब्रेन ट्यूमर के उपचार और देखभाल से संबंधित महत्वपूर्ण जानकारी.",
        "link": "https://www.radiologyinfo.org/en/info/thera-brain",
        "language": "Hindi",
        "cover": "https://cdn-icons-png.flaticon.com/512/3997/3997838.png"
    }
]

# Define brain tumor symptoms for animated display
brain_tumor_symptoms = [
    {"symptom": "Headaches", "description": "Especially in the morning or when lying down"},
    {"symptom": "Seizures", "description": "From mild to severe"},
    {"symptom": "Vision Problems", "description": "Blurred vision, double vision, or loss of peripheral vision"},
    {"symptom": "Balance Issues", "description": "Difficulty walking or coordinating movements"},
    {"symptom": "Speech Changes", "description": "Difficulty finding words or expressing thoughts"},
    {"symptom": "Personality Changes", "description": "Mood swings, irritability, or confusion"},
    {"symptom": "Memory Problems", "description": "Short-term memory issues or concentration difficulties"},
    {"symptom": "Nausea & Vomiting", "description": "Especially in the morning or without apparent cause"}
]

# Create main header with animation
col1, col2 = st.columns([1, 3])
with col1:
    if lottie_medical:
        st_lottie(lottie_medical, height=150, key="medical_animation")
with col2:
    st.markdown("<h1 class='fade-in' style='color:#4285F4;'>Welcome to Patient Corner</h1>", unsafe_allow_html=True)
    st.markdown("<p class='slide-in'>Your comprehensive healthcare information portal</p>", unsafe_allow_html=True)

# Enhanced sidebar with icons
st.sidebar.markdown("""
<div style='display: flex; align-items: center; margin-bottom: 20px;'>
    <img src='https://cdn-icons-png.flaticon.com/512/4320/4320379.png' width='40'>
    <h2 style='margin-left: 10px;'>Navigation</h2>
</div>
""", unsafe_allow_html=True)

# Create sidebar with icons
options = ["Games", "Policies", "News", "Books", "Brain Tumor Symptoms & Remedies", "Hospitals"]
icons = ["🎮", "📜", "📰", "📚", "🧠", "🏥"]

sidebar_options = [f"{icon} {option}" for icon, option in zip(icons, options)]
selected_sidebar_option = st.sidebar.radio("", sidebar_options)
selected_option = selected_sidebar_option.split(" ", 1)[1]

# Add a loading spinner for visual effect
with st.spinner("Loading content..."):
    time.sleep(0.5)  # Simulate loading for animation effect

# Content display based on selected option
if selected_option == "Games":
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        if lottie_games:
            st_lottie(lottie_games, height=150, key="games_animation")
    with col2:
        st.markdown("<h2 class='fade-in'>Games for Relaxation</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slide-in'>Choose a game category to play and relax</p>", unsafe_allow_html=True)
    
    # Game categories in an attractive grid
    st.markdown("<div class='button-container'>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    for i, (category, url) in enumerate(game_categories.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <a href="{url}" target="_blank">
            <div class="card pulse" style="cursor: pointer; text-align: center;">
                <img src="{logos['games']}" width="50" style="margin-bottom: 10px;">
                <h3>{category}</h3>
                <p>Click to play</p>
            </div>
            </a>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

elif selected_option == "Policies":
    # Header with animation
    st.markdown(f"""
    <div class="header-container fade-in">
        <div class="logo-container">
            <img src="{logos['policies']}" width="60">
        </div>
        <div class="header-text">
            <h2>Insurance Policies</h2>
            <p>View healthcare insurance policies and regulations</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Policy section with animated loading
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.spinner("Fetching the latest policies..."):
            try:
                response = requests.get("https://irdai.gov.in/list-of-tpas")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                policies = soup.find_all('table')
                if policies:
                    data = []
                    for row in policies[0].find_all('tr'):
                        cols = row.find_all('td')
                        if cols:
                            data.append([col.get_text(strip=True) for col in cols])
                    
                    if data:
                        st.success("Policies loaded successfully!")
                        df = pd.DataFrame(data[1:], columns=data[0])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("No data found in the table.")
                else:
                    st.warning("No policies found on the website.")
            except Exception as e:
                st.error(f"Error fetching policies: {e}")
                
                # Provide sample data in case of error
                st.markdown("""
                ### Sample Policy Information
                
                Here are some common insurance policies for healthcare:
                
                1. Health Insurance
                2. Critical Illness Cover
                3. Hospital Cash Benefits
                4. Accident Insurance
                5. Senior Citizen Health Insurance
                
                Please check the official IRDAI website for actual policy details.
                """)
        st.markdown('</div>', unsafe_allow_html=True)

elif selected_option == "News":
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        if lottie_news:
            st_lottie(lottie_news, height=150, key="news_animation")
    with col2:
        st.markdown("<h2 class='fade-in'>Latest News</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slide-in'>Stay updated with the latest  news and research</p>", unsafe_allow_html=True)
    
    # Language selection with better styling
    language = st.select_slider(
        "Select Language:",
        options=["English", "Marathi", "Hindi"],
        value="English"
    )
    
    # Progress bar for loading effect
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress_bar.progress(i + 1)
    st.success("News loaded successfully!")
    
    if language in news_feeds:
        sources = [feed["name"] for feed in news_feeds[language]]
        tabs = st.tabs(sources)
        
        for tab, feed_info in zip(tabs, news_feeds[language]):
            with tab:
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <img src="{feed_info.get('logo', logos['news'])}" width="100" style="margin-right: 15px;">
                    <h3>{feed_info["name"]}  News</h3>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    feed = feedparser.parse(feed_info["url"])
                    if feed.entries:
                        for entry in feed.entries[:5]:
                            title = entry.get('title', 'No Title')
                            link = entry.get('link', '#')
                            description = entry.get('description', 
                                                 entry.get('summary', 'No description available'))
                            
                            st.markdown(f"""
                                <div class="card news-card fade-in">
                                    <h4><a href='{link}' target='_blank'>{title}</a></h4>
                                    <p>{description}</p>
                                    <div style="text-align: right">
                                        <a href="{link}" target="_blank" style="text-decoration: none; color: #4285F4;">Read More →</a>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning(f"No news articles found from {feed_info['name']}")
                except Exception as e:
                    st.error(f"Error fetching news from {feed_info['name']}: {str(e)}")
                    # Show sample news in case of error
                    st.markdown(f"""
                        <div class="card news-card fade-in">
                            <h4>Health Ministry Launches New Vaccination Drive</h4>
                            <p>The Ministry of Health has announced a nationwide vaccination program targeting preventable diseases.</p>
                            <div style="text-align: right">
                                <a href="#" style="text-decoration: none; color: #4285F4;">Read More →</a>
                            </div>
                        </div>
                        
                        <div class="card news-card fade-in">
                            <h4>New Research on Brain Health</h4>
                            <p>Scientists have discovered a potential breakthrough in early detection of brain disorders.</p>
                            <div style="text-align: right">
                                <a href="#" style="text-decoration: none; color: #4285F4;">Read More →</a>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

elif selected_option == "Books":
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        if lottie_books:
            st_lottie(lottie_books, height=150, key="books_animation")
    with col2:
        st.markdown("<h2 class='fade-in'>Medical Reference Books</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slide-in'>Educational resources for patients and caregivers</p>", unsafe_allow_html=True)
    
    # Language filter with better styling
    language_options = ["All", "English", "Marathi", "Hindi"]
    selected_language = st.select_slider("Filter by Language:", options=language_options, value="All")
    
    # Filter books
    filtered_books = books
    if selected_language != "All":
        filtered_books = [book for book in books if book["language"] == selected_language]
    
    # Display books in an attractive card layout
    cols = st.columns(3)
    for i, book in enumerate(filtered_books):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card book-card fade-in">
                <div style="text-align: center; margin-bottom: 15px;">
                    <img src="{book['cover']}" width="100">
                </div>
                <h3>{book["title"]}</h3>
                <p><strong>Author:</strong> {book['author']}</p>
                <p><strong>Language:</strong> {book['language']}</p>
                <p>{book["description"]}</p>
                <div style="text-align: center; margin-top: 15px;">
                    <a href="{book['link']}" target="_blank" style="text-decoration: none;">
                        <div style="background-color: #F4B400; color: white; padding: 8px 15px; border-radius: 5px;">
                            Read More
                        </div>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

elif selected_option == "Brain Tumor Symptoms & Remedies":
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        if lottie_brain:
            st_lottie(lottie_brain, height=150, key="brain_animation")
    with col2:
        st.markdown("<h2 class='fade-in'>Brain Tumor Information</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slide-in'>Learn about symptoms, treatments, and care strategies</p>", unsafe_allow_html=True)
    
    # Create tabs for organization
    tabs = st.tabs(["Symptoms", "Treatment Options", "Lifestyle Recommendations", "When to Seek Help"])
    
    with tabs[0]:
        st.markdown("<h3 class='fade-in'>Common Symptoms</h3>", unsafe_allow_html=True)
        
        # Display symptoms with animation
        cols = st.columns(2)
        for i, symptom in enumerate(brain_tumor_symptoms):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="card fade-in" style="animation-delay: {i*0.2}s;">
                    <h4>{symptom['symptom']}</h4>
                    <p>{symptom['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.info("Note: These symptoms can also be related to other medical conditions. Consult a doctor for proper diagnosis.")
    
    with tabs[1]:
        st.markdown("<h3 class='fade-in'>Treatment Options</h3>", unsafe_allow_html=True)
        
        # Treatment options with visual indicators
        treatments = [
            {"name": "Surgery", "description": "Removal of tumor tissue when possible", "icon": "🔪"},
            {"name": "Radiation Therapy", "description": "Using high-energy beams to kill tumor cells", "icon": "📡"},
            {"name": "Chemotherapy", "description": "Using drugs to kill cancer cells", "icon": "💊"},
            {"name": "Targeted Therapy", "description": "Using drugs that target specific abnormalities in cancer cells", "icon": "🎯"},
            {"name": "Alternative Treatments", "description": "Complementary approaches including dietary changes and stress management", "icon": "🌿"}
        ]
        
        for treatment in treatments:
            st.markdown(f"""
            <div class="card slide-in">
                <div style="display: flex; align-items: center;">
                    <div style="font-size: 2rem; margin-right: 15px;">{treatment['icon']}</div>
                    <div>
                        <h4>{treatment['name']}</h4>
                        <p>{treatment['description']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tabs[2]:
        st.markdown("<h3 class='fade-in'>Lifestyle Recommendations</h3>", unsafe_allow_html=True)
        
        # Recommendations with progress bars
        recommendations = [
            {"name": "Healthy Diet", "description": "Focus on fruits, vegetables, whole grains, and lean proteins", "importance": 90},
            {"name": "Regular Exercise", "description": "As permitted by your doctor", "importance": 85},
            {"name": "Adequate Rest", "description": "Ensure proper sleep and rest periods", "importance": 95},
            {"name": "Stress Management", "description": "Meditation, yoga, or other relaxation techniques", "importance": 80},
            {"name": "Support Groups", "description": "Connect with others who understand your journey", "importance": 75}
        ]
        
        for rec in recommendations:
            st.markdown(f"""
            <div class="card slide-in">
                <h4>{rec['name']}</h4>
                <p>{rec['description']}</p>
                <div style="margin-top: 10px;">
                    <div style="color: #666; margin-bottom: 5px;">Importance Level</div>
                    <div style="background-color: #f1f3f4; border-radius: 10px; height: 10px; width: 100%;">
                        <div style="background-color: #4285F4; border-radius: 10px; height: 10px; width: {rec['importance']}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tabs[3]:
        st.markdown("<h3 class='fade-in'>When to Seek Medical Attention</h3>", unsafe_allow_html=True)
        
        # Warning signs with alert styling
        warnings = [
            "Sudden, severe headaches",
            "New onset seizures",
            "Sudden vision problems or changes",
            "Difficulty with balance or speech",
            "Progressive weakness or numbness",
            "Persistent vomiting without apparent cause"
        ]
        
        st.markdown("""
        <div class="card" style="border-left: 5px solid #DB4437;">
            <h4>Seek immediate medical attention if you experience:</h4>
            <ul>
        """, unsafe_allow_html=True)
        
        for warning in warnings:
            st.markdown(f"<li style='margin-bottom: 10px;'>{warning}</li>", unsafe_allow_html=True)
        
        st.markdown("""
            </ul>
            <div style="background-color: #fce8e6; padding: 10px; border-radius: 5px; margin-top: 15px;">
                <strong>Emergency Contact:</strong> If symptoms are severe, call emergency services or go to the nearest emergency room immediately.
            </div>
        </div>
        """, unsafe_allow_html=True)

elif selected_option == "Hospitals":
    st.header("Hospitals Directory")
    
    # Add filtering options
    st.subheader("Filter Hospitals")
    col1, col2 = st.columns(2)
    
    with col1:
        # Filter by division
        all_divisions = list(set(hospital["division"] for hospital in hospitals))
        selected_division = st.selectbox("Select Division:", ["All"] + all_divisions)
    
    with col2:
        # Filter by state
        all_states = list(set(hospital["state"] for hospital in hospitals))
        selected_state = st.selectbox("Select State:", ["All"] + all_states)

    # Filter hospitals based on selection
    filtered_hospitals = hospitals
    if selected_division != "All":
        filtered_hospitals = [h for h in filtered_hospitals if h["division"] == selected_division]
    if selected_state != "All":
        filtered_hospitals = [h for h in filtered_hospitals if h["state"] == selected_state]

    # Display hospitals
    for hospital in filtered_hospitals:
        with st.expander(f"{hospital['name']} - {hospital['city']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Address:** {hospital['address']}")
                st.write(f"**Phone:** {hospital['phone']}")
                st.write("**Specialties:**")
                for specialty in hospital['specialties']:
                    st.write(f"- {specialty}")
            
            with col2:
                st.write(f"**State:** {hospital['state']}")
                st.write(f"**Division:** {hospital['division']}")
                if hospital['website']:
                    st.markdown(f"[Visit Website]({hospital['website']})")


# Add Emergency Services section in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background-color: #fce8e6; padding: 15px; border-radius: 10px; border-left: 5px solid #DB4437;">
    <h3 style="color: #DB4437;">Emergency Services</h3>
    <p><strong>National Emergency:</strong> 112</p>
    <p><strong>Ambulance:</strong> 108</p>
    <p><strong>Health Helpline:</strong> 1056</p>
</div>
""", unsafe_allow_html=True)


# Add a footer with pulsing animation
st.markdown("""
---
<div style='text-align: center; color: gray;' class='pulse'>
    <p>Patient Corner - Your Health Information Portal</p>
    <p>For medical emergencies, please contact your nearest hospital or call emergency services.</p>
    <p style='font-size: 0.8rem;'>© 2025 Patient Corner. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)

# Add a chat support button that appears floating at the bottom right
st.markdown("""
<div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
    <div style="background-color: #4285F4; color: white; padding: 15px; border-radius: 50%; width: 60px; height: 60px; display: flex; justify-content: center; align-items: center; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <span style="font-size: 24px;">💬</span>
    </div>
</div>
""", unsafe_allow_html=True)