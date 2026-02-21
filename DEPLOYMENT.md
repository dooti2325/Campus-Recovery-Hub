# Deployment Guide for Campus Recovery Hub

This guide will help you deploy Campus Recovery Hub to various platforms.

## Table of Contents
- [Local Deployment](#local-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Vercel Deployment](#vercel-deployment)
- [AWS Deployment](#aws-deployment)
- [Docker Deployment](#docker-deployment)
- [Security Checklist](#security-checklist)

---

## Local Deployment

### Development Environment
```bash
# Navigate to project directory
cd Campus-Recovery-Hub

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run development server
python app.py
```

Visit: `http://localhost:5000`

### Production Environment (Local)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or with multiple workers for better performance
gunicorn --workers 8 --worker-class sync -b 0.0.0.0:5000 app:app
```

---

## Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Git repository initialized
- Heroku account

### Steps

1. **Create Heroku app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

2. **Set environment variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set FLASK_DEBUG=False
   heroku config:set SECRET_KEY=generate-a-strong-random-key-here
   heroku config:set MAIL_SERVER=smtp.gmail.com
   heroku config:set MAIL_PORT=587
   heroku config:set MAIL_USERNAME=your-email@gmail.com
   heroku config:set MAIL_PASSWORD=your-app-password
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **View logs**
   ```bash
   heroku logs --tail
   ```

### Files Included
- `Procfile` - Heroku configuration
- `requirements.txt` - Dependencies

---

## Vercel Deployment

### Prerequisites
- Vercel CLI installed
- Vercel account

### Steps

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Set environment variables in Vercel dashboard**
   - Go to Project Settings → Environment Variables
   - Add all variables from `.env`

### Notes
- `vercel.json` is already configured
- Flask runs as serverless function
- Database persists with SQLite

---

## AWS Deployment

### Using Elastic Beanstalk

1. **Install AWS CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize**
   ```bash
   eb init -p python-3.11 campus-recovery-hub
   ```

3. **Create environment**
   ```bash
   eb create production-app
   ```

4. **Set environment variables**
   ```bash
   eb setenv FLASK_ENV=production SECRET_KEY=your-key MAIL_USERNAME=email MAIL_PASSWORD=password
   ```

5. **Deploy**
   ```bash
   eb deploy
   ```

### Using EC2

1. **Launch Ubuntu 22.04 instance**
2. **SSH into instance**
3. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   ```

4. **Clone repository**
   ```bash
   git clone your-repo-url
   cd Campus-Recovery-Hub
   ```

5. **Setup Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Configure Nginx**
   ```bash
   # See nginx.conf in project
   sudo cp nginx.conf /etc/nginx/sites-available/default
   sudo systemctl restart nginx
   ```

7. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

---

## Docker Deployment

### Build Docker Image

1. **Create Dockerfile** (included in project)
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   ENV FLASK_DEBUG=False
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
   ```

2. **Build image**
   ```bash
   docker build -t campus-recovery-hub .
   ```

3. **Run container**
   ```bash
   docker run -p 5000:5000 \
     -e FLASK_ENV=production \
     -e SECRET_KEY=your-key \
     -e MAIL_USERNAME=email \
     -e MAIL_PASSWORD=password \
     campus-recovery-hub
   ```

### Docker Compose

```bash
docker-compose up -d
```

---

## Security Checklist

Before deploying to production:

### Essential
- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Set `FLASK_DEBUG=False`
- [ ] Set `FLASK_ENV=production`
- [ ] Configure email credentials (or disable email)
- [ ] Use HTTPS/SSL certificate
- [ ] Use strong database encryption

### Recommended
- [ ] Enable CORS if needed
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable CSRF protection (already enabled)
- [ ] Set secure cookie flags
- [ ] Enable password hashing (already enabled)
- [ ] Configure logging and monitoring
- [ ] Set up automated backups
- [ ] Enable security headers

### Email Security
- [ ] Use app-specific passwords (not main Gmail password)
- [ ] Enable 2-factor authentication on email account
- [ ] Use environment variables (not hardcoded values)
- [ ] Test email functionality before launch

### Database Security
- [ ] Regular backups
- [ ] Restrict database access
- [ ] Use parameterized queries (already implemented)
- [ ] Never commit database files to git
- [ ] Encrypt sensitive data if needed

---

## Configuration Examples

### Production Settings (.env)
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-production-secret-key-min-32-chars
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

APP_URL=https://your-domain.com
```

### Gunicorn Configuration
```bash
gunicorn \
  --workers 8 \
  --worker-class sync \
  --bind 0.0.0.0:5000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  app:app
```

---

## Monitoring & Maintenance

### Logs
- Monitor application logs regularly
- Set up log aggregation (CloudWatch, Papertrail, etc.)
- Archive old logs

### Backups
- Backup database daily
- Store backups in secure location
- Test restore procedures

### Updates
- Keep dependencies updated
- Apply security patches promptly
- Test updates in staging first

### Performance
- Monitor response times
- Monitor database performance
- Scale workers as needed
- Cache static assets

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Database Issues
```bash
# Delete and recreate database
rm database.db
python app.py
```

### Email Not Sending
- Verify SMTP credentials
- Check firewall allows SMTP
- Enable "Less secure apps" (Gmail)
- Use app-specific password

### Static Files Not Loading
- Check `static/` directory exists
- Verify file paths in templates
- Clear browser cache
- Check server logs

---

## Performance Tips

1. **Enable compression**
   ```bash
   gunicorn --with-grpc -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Use CDN for assets** (CloudFront, Cloudflare)

3. **Enable caching**
   - Browser caching
   - Server-side caching

4. **Database optimization**
   - Indexes (already implemented)
   - Query optimization
   - Connection pooling

5. **Load balancing**
   - Multiple Gunicorn workers
   - Nginx load balancing

---

## Support & Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Heroku Documentation](https://devcenter.heroku.com/)
- [AWS Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Docker Documentation](https://docs.docker.com/)
- [Vercel Documentation](https://vercel.com/docs)

---

**Last Updated**: 2024
**Version**: 2.0.0
