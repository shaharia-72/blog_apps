Completely Free Deployment Guide: Render + Supabase + Upstash
Since you want to host this for free and ensure the backend (Django + Celery), Database (PostgreSQL), and Cache (Redis) are always running without sleeping, I've designed the perfect free architecture for you.

Render's free tier has limitations (like putting the app to sleep after 15 minutes of no visits). Render also doesn't provide a free Celery worker, and their free PostgreSQL expires after 90 days.

Here is the ultimate "Free Forever" stack:

Database: Supabase (Free forever PostgreSQL)
Redis: Upstash (Free forever Redis, up to 10k requests/day)
Backend & Celery: Render Free Web Service (We combined Django, Celery Worker, and Celery Beat into ONE single container using the start.sh script to avoid paying for extra servers).
Anti-Sleep: cron-job.org (Free pinging service to keep Render awake).
🛠️ Step 1: Set up Free Redis (Upstash)
Since you are using Supabase for PostgreSQL, you also need a free Redis server for Celery and Caching. Render's free Redis is very limited and eventually costs money.

Go to Upstash.com and create a free account.
Click Create Database under the "Redis" section.
Give it a name (e.g., blog-redis), select the free tier, and create it.
Once created, scroll down to the "Connect to your database" section.
Copy the Redis URL (It will look like rediss://default:PASSWORD@endpoint.upstash.io:PORT).
Save this URL for later.
🚀 Step 2: Push Your Code to GitHub
Make sure all your code (including the new build.sh, start.sh, and render.yaml I created for you) is committed and pushed to your GitHub repository.

bash
git add build.sh start.sh render.yaml
git commit -m "Add Render deployment scripts"
git push origin main
🌐 Step 3: Deploy on Render
Go to Render.com and log in with GitHub.
Click New + and select Blueprint.
Connect your GitHub account and select your blog-shaha repository.
Render will automatically read the render.yaml file I created.
It will ask you to fill in the Missing Environment Variables. Fill them in:
DATABASE_URL: Your Supabase connection string (make sure it ends with ?sslmode=require or uses the transaction pooler).
REDIS_URL: Your Upstash Redis URL (paste it here).
REDIS_SESSION_URL: Your Upstash Redis URL (same as above).
JWT_SECRET_KEY: A strong random string.
FRONTEND_URL: Your frontend URL (e.g., <https://blog.shaharia.com>).
ALLOWED_HOSTS: Your Render domain (e.g., blog-shaha-backend.onrender.com).
CSRF_TRUSTED_ORIGINS: <https://blog-shaha-backend.onrender.com>.
Click Apply.
Render will now start building and deploying your app automatically. It runs build.sh (installs packages and runs migrations) and then start.sh (starts Django and Celery in the background).
TIP

The start.sh script is the magic here. It runs Gunicorn (for the web API) and Celery (for background tasks like email and analytics) inside the same free 512MB container, saving you $14/month for a separate Celery worker on Render!

⏰ Step 4: Fix Render's "Sleep Issue" (Keep-Alive Cron Job)
Render free web services go to sleep if nobody visits them for 15 minutes. To fix this, you wanted a ping every 9 minutes. We will use a free external service to hit the /api/v1/health/ endpoint we created earlier.

Go to cron-job.org and create a free account.
Click Create Cronjob.
In the URL field, paste your Render health check URL (e.g., <https://blog-shaha-backend.onrender.com/api/v1/health/>).
Set the execution schedule to Every 9 minutes.
Save it.
Result: Every 9 minutes, cron-job.org visits your site invisibly. Since it hits the server, Render thinks there is active traffic and never goes to sleep. Additionally, because we hit the /api/v1/health/ endpoint, it also checks if your Database and Redis are responding securely without hitting the database too hard (since it's cached).

🎓 Summary of What You Learned
Supabase & Upstash: You learned how to decouple your database and cache to fully serverless, free-forever providers rather than relying on host-specific free tiers that expire.
Micro-Containerization (start.sh): You learned how to run both asynchronous workers (Celery) and synchronous web servers (Gunicorn) in a single constrained environment using Bash backgrounding (&) and wait.
Render Blueprints (render.yaml): You adopted "Infrastructure as Code". Instead of manually configuring the dashboard, your codebase now tells Render exactly how to build and configure the app.
Uptime Engineering: You utilized external cron jobs to artificially stimulate traffic and bypass PaaS sleep limitations safely using a dedicated health endpoint.
