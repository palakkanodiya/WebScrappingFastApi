# High-Performance Web Scraping API Using FastAPI

##  Description

A simple FastAPI project that scrapes product information from a Walmart product page using Selenium/BeautifulSoup, stores the data in MongoDB, and exposes it via RESTful APIs.

---

## Tech Stack

- FastAPI – High-performance web framework for APIs
- Pydantic – Data validation and serialization
- Requests – For sending HTTP requests
- BeautifulSoup / Selenium – HTML parsing and dynamic content scraping
- PyMongo – MongoDB driver for Python
- MongoDB NoSQL database (local or cloud with MongoDB Atlas)

---

## Requirements

- Python 3.10+ (Recommended: 3.11)
- MongoDB (local or Atlas cloud instance)
- All dependencies from `requirements.txt`
- pip install -r requirements.txt


---



### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/WebScrappingFastApi.git
cd WebScrappingFastApi


```

### 2. Set Up Virtual Environment

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate

```

### For macOS/Ubuntu/Linux:

```bash
python3 -m venv venv
source venv/bin/activate

```

### Start the FastAPI Server

uvicorn main:app --reload

