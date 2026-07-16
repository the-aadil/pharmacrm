# Pharma CRM AI Agent

An AI-powered CRM tool designed for pharmaceutical sales representatives to log HCP (Healthcare Professional) interactions. The application features a dual-panel interface: a structured input form on the left and a conversational AI Chat Assistant on the right. The backend uses LangGraph and an LLM to parse natural language notes, automatically populate the form, and persist data to a SQL database.

---

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Redux Toolkit, Tailwind CSS
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **AI / LLM**: LangGraph, Groq (gemma2-9b-it model)
- **Database**: MySQL or PostgreSQL

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed and set up:

- **Node.js** (v18 or higher) and **npm**
- **Python** (v3.10 or higher) and **pip**
- **MySQL** or **PostgreSQL** database server (running locally)
- **Groq API Key** (Get one for free at console.groq.com)

---

## 🚀 Step-by-Step Setup Instructions

Follow these steps in order to get the application running on your local machine.

### 1. Clone the Repository

Open your terminal and run:

```bash
git clone <your-github-repo-url>
cd <your-repo-folder>
```

### 2. Backend Setup (FastAPI + LangGraph)

**A. Configure environment variables**

Navigate to the backend folder:

```bash
cd backend
```

Copy the `.env.example` file from the root folder into `backend/.env`.

Open the `.env` file and paste your actual Groq API key and database connection URL.

**B. Install Python dependencies**

Make sure you are inside the backend folder, then run:

```bash
pip install -r requirements.txt
```

**C. Start the Backend Server**

Run the FastAPI development server:

```bash
uvicorn main:app --reload --port 8000
```

Keep this terminal running.

### 3. Frontend Setup (React + Vite)

Open a second terminal window and navigate to the root of your project.

**A. Install Node dependencies**

Navigate to the frontend folder and install packages:

```bash
cd frontend
npm install
```

**B. Start the Frontend Server**

```bash
npm run dev
```

Open the URL shown in the terminal (usually `http://localhost:5173`) in your browser.

---

## ✅ How to Test the Application

1. Open your web browser to `http://localhost:5173`.
2. You will see the empty CRM form on the left and the AI Chat on the right.

### Scenario 1: AI Auto-Fill (Testing `log_interaction`)

Copy and paste the following test interaction into the chat box and click the "Log" button:

> "I just completed an in-person 40-minute meeting at 2:30 PM with Dr. Emily Carter. Her nurse Sarah attended. We discussed Drug X. Her sentiment was positive. She agreed to enroll 5 patients. My follow-up is to email forms by Thursday."

Wait 2-3 seconds. The fields on the left will automatically populate.

### Scenario 2: AI Edit / Correction (Testing `edit_interaction`)

Without refreshing the browser, paste this correction into the chat and click "Log":

> "Actually, change the sentiment to neutral and the follow-up date to Wednesday."

The Left Form will update the existing record in the SQL database, proving the edit feature works.
