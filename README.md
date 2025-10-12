SkillSphere: AI-Powered Career Roadmap Generator
(Note: You can take a screenshot of your beautiful Aurora UI and upload it somewhere like Imgur to replace this link!)

SkillSphere is a full-stack web application that acts as a personal AI career coach. It analyzes a user's current skills and generates a personalized, step-by-step roadmap to help them achieve their future career goals.

This project was built from the ground up, integrating a modern frontend, a powerful backend API, multiple databases, and cutting-edge AI models to provide real, actionable career advice.

✨ Key Features
Secure User Authentication: Users can create an account, log in, and have their sessions securely managed using JWT tokens.

AI-Powered Resume Parser: Leverages Google's Gemini AI to intelligently parse resume text, extracting and categorizing skills, work experience, and education.

Dynamic & Personalized Career Roadmaps:

Users input their current role and desired future role.

The application sends this, along with the user's current skills from their resume, to the AI.

The AI generates a unique, step-by-step learning plan that focuses on filling the user's specific skill gaps.

Save & View Roadmaps: Users can permanently save their generated roadmaps to their account and view them at any time.

Beautiful & Modern UI: A stunning, fully responsive "Aurora" dark-mode interface built with React and Tailwind CSS, featuring smooth animations and a vibrant, engaging color palette.

💻 Technology Stack
This project utilizes a modern, scalable, and professional tech stack, just as you would find in a real-world software company.

Backend
Framework: Python with FastAPI

Databases:

PostgreSQL (via Supabase) for structured user data.

MongoDB (via MongoDB Atlas) for flexible storage of AI-generated roadmaps.

AI Integration: Direct API calls to Google's Gemini AI for all language model tasks.

Authentication: JWT (JSON Web Tokens) for secure, stateless user sessions.

Containerization: Docker for packaging the backend into a portable, scalable container.

Frontend
Framework: React (with Vite for a fast development experience).

Styling: Tailwind CSS for a modern, utility-first design system.

UI/UX: Custom-built components with a focus on a responsive, visually appealing, and interactive user experience.

🚀 Getting Started
To get a local copy up and running, follow these simple steps.

Prerequisites
Python 3.10+

Node.js & npm

Docker Desktop

Backend Setup
Navigate to the main project folder (Skillsphere).

Create and activate a virtual environment:

python -m venv .venv
.\.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create a .env file and fill in your secret keys (see .env.example).

Start the server:

python -m uvicorn main:app --reload

The backend will be running at http://127.0.0.1:8000.

Frontend Setup
Navigate to the frontend folder:

cd my-skillsphere-app

Install dependencies:

npm install

Start the development server:

npm run dev

The frontend will be running, typically at http://localhost:5173 or a similar port.
