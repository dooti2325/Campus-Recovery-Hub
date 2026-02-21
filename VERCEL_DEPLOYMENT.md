# Vercel Deployment Guide - Campus Recovery Hub

This guide will help you deploy Campus Recovery Hub to Vercel in minutes.

## Prerequisites

- Vercel account (free at https://vercel.com)
- Git repository (GitHub, GitLab, or Bitbucket)
- Node.js and npm installed locally

## Step 1: Install Vercel CLI

Open your terminal and run:
```bash
npm install -g vercel
```

Verify installation:
```bash
vercel --version
```

## Step 2: Authenticate with Vercel

```bash
vercel login
```

This will open your browser to authenticate. Follow the prompts.

## Step 3: Initialize Git Repository (if not already done)

```bash
cd "d:\Dooti\VS Code Files 2\Campus Recovery Hub\Campus-Recovery-Hub"

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "feat: Initial commit - Campus Recovery Hub production ready"

# Add remote (replace with your repository)
git remote add origin https://github.com/yourusername/Campus-Recovery-Hub.git

# Push to remote
git push -u origin main
```

## Step 4: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

```bash
cd "d:\Dooti\VS Code Files 2\Campus Recovery Hub\Campus-Recovery-Hub"
vercel
```

Follow the interactive prompts:
- Confirm project setup
- Select framework (Python)
- Override settings if needed

### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Import your GitHub repository
4. Select the Campus-Recovery-Hub project
5. Configure environment variables
6. Deploy

## Step 5: Configure Environment Variables

After deployment, set up environment variables:

### Using Vercel CLI:
```bash
vercel env add SECRET_KEY
vercel env add MAIL_SERVER
vercel env add MAIL_PORT
vercel env add MAIL_USE_TLS
vercel env add MAIL_USERNAME
vercel env add MAIL_PASSWORD
vercel env add MAIL_DEFAULT_SENDER
```

### Using Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add each variable:
   - `SECRET_KEY` - Passcode
   - `FLASK_ENV` - Set to `production`
   - `FLASK_DEBUG` - Set to `False`
   - `MAIL_SERVER` - smtp.gmail.com
   - `MAIL_PORT` - 587
   - `MAIL_USE_TLS` - True
   - `MAIL_USERNAME` - Your Gmail address
   - `MAIL_PASSWORD` - App-specific password
   - `MAIL_DEFAULT_SENDER` - noreply@campusrecoveryhub.com

## Step 6: Test Deployment

After deployment completes:

1. Click the deployment URL
2. Your app should be live!
3. Test features:
   - Sign up
   - Log in
   - Report item
   - Browse items
   - Upload image
   - Check QR code

## Configuration Details

### vercel.json Summary
- Configured for Python runtime
- Routes all requests to app.py
- Supports Flask application

### Database Note
- SQLite database is created automatically
- Stored in serverless function temporary storage
- **For production with persistent data**, consider:
  - PostgreSQL (recommended)
  - AWS DynamoDB
  - Vercel Postgres (in beta)

### File Uploads
- Currently stored in serverless temp storage
- **Limitation**: Files deleted after function execution
- **Solution for production**:
  - Use AWS S3 or similar
  - Use Vercel Blob Storage
  - Set up database for file references

## Production Considerations

### Database Persistence
For persistent data in production, update app.py to use PostgreSQL:

```python
import os
from sqlalchemy import create_engine

# For serverless, use PostgreSQL instead of SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')
engine = create_engine(DATABASE_URL)
```

### File Storage
For file uploads to persist:

```python
# Install boto3 for AWS S3
pip install boto3

# Add S3 upload function
def upload_to_s3(file, bucket):
    s3 = boto3.client('s3')
    s3.upload_fileobj(file, bucket, file.filename)
```

### Email Configuration
Gmail works out of the box with app passwords. For production volume:
- SendGrid (recommended)
- AWS SES
- Mailgun

## Troubleshooting

### Build Fails
```bash
# Check logs
vercel logs

# Rebuild
vercel --prod
```

### Environment Variables Not Updating
```bash
# Redeploy after adding env vars
vercel --prod
```

### Cold Starts
- Normal for serverless
- Use Vercel Pro for improved performance
- Keep dependencies minimal

### Database Not Persisting
- Export data before redeployment
- Implement cloud database
- See Production Considerations above

## Monitoring

### Vercel Dashboard
- https://vercel.com/dashboard
- View deployments
- Check function logs
- Monitor performance

### Analytics
- Built-in analytics in Vercel
- View request counts
- Monitor response times

## Custom Domain

1. In Vercel dashboard, go to Settings
2. Click "Domains"
3. Add your domain
4. Follow DNS configuration
5. Configure SSL (automatic)

## Alternative: Use Vercel Postgres

For persistent database:

1. In Vercel dashboard, create Postgres database
2. Get connection string
3. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
4. Update requirements.txt
5. Redeploy

## Cost Estimation

- **Free Plan**: Up to 100GB bandwidth/month
- **Pro Plan**: $20/month, unlimited bandwidth
- **Enterprise**: Custom pricing

## Next Steps

1. ✅ Code cleanup (DONE)
2. ✅ Configure vercel.json (DONE)
3. ⏳ Initialize Git repo
4. ⏳ Deploy to Vercel
5. ⏳ Configure environment variables
6. ⏳ Test application
7. ⏳ Set up custom domain (optional)
8. ⏳ Configure persistent database (recommended)

## Quick Command Summary

```bash
# Navigate to project
cd "d:\Dooti\VS Code Files 2\Campus Recovery Hub\Campus-Recovery-Hub"

# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy to Vercel
vercel

# Deploy to production
vercel --prod

# View logs
vercel logs

# Add environment variable
vercel env add VARIABLE_NAME

# Check status
vercel status
```

## Support

- Vercel Docs: https://vercel.com/docs
- Flask Guide: https://flask.palletsprojects.com/
- Issues: Check deployment logs in Vercel dashboard

---

**Version**: 2.0.0
**Last Updated**: 2024
**Status**: Ready for Production
