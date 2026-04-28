# AI-Powered Conversational Career Assistant
### Final Year Project - BSc Computer Science, University of Bradford

## Overview
An AI-powered web application that allows users to build and tailor CVs through 
natural conversation. Instead of manually filling out forms, users simply chat 
with an AI agent that extracts their information, structures it, and generates 
a professional CV, then tailors it to specific job descriptions automatically.

## Key Features
- Conversational CV Builder — chat naturally, AI extracts and saves your info
- ATS Analyser — paste a job description, get scored and tailored suggestions
- CV Generation — structured CV produced from conversation history
- User Authentication — secure login and registration system
- Profile Management — stored and editable user data

## Tech Stack
- **Backend:** Python, Flask, SQLAlchemy
- **AI/LLM:** LangChain, NVIDIA LLM API (OpenAI-compatible)
- **Vector Store:** ChromaDB (RAG pipeline)
- **Database:** PostgreSQL
- **Frontend:** Jinja2, HTML, CSS

## Architecture
The core of the system is an AI agent loop with tool-calling capabilities. 
The agent decides which tools to invoke based on user input — extracting CV 
data, querying the database, or generating ATS feedback — across an iterative 
reasoning loop.

## Project Status
Academic final year project — core features functional, deployment in progress.

## Author
Muhammad Mansoor Ghauri,
University of Bradford — BSc Computer Science
