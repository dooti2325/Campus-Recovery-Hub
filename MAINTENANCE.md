# Maintenance Guide for Campus Recovery Hub

This guide provides instructions for maintaining and operating Campus Recovery Hub in production.

## Table of Contents
- [Regular Maintenance](#regular-maintenance)
- [Monitoring](#monitoring)
- [Backups](#backups)
- [Updates and Upgrades](#updates-and-upgrades)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## Regular Maintenance

### Daily
- Monitor application logs
- Check for errors in user reports
- Review system health

### Weekly
- Review database size
- Check upload folder size
- Monitor disk space
- Review user activity

### Monthly
- Update dependencies
- Review security logs
- Optimize database
- Clean up old files
- Review and respond to user feedback

### Quarterly
- Security audit
- Performance review
- Backup verification
- Update documentation

### Annually
- Full system review
- Major version updates
- Infrastructure review
- Capacity planning

---

## Monitoring

### Application Monitoring

**Key Metrics:**
- Response time
- Error rate
- Uptime
- Database performance
- Memory usage
- Disk usage

### Tools
- Application Insights (Azure)
- CloudWatch (AWS)
- Datadog (Multi-cloud)
- New Relic (APM)
- Sentry (Error tracking)

### Logs

**Log Locations:**
- Flask logs: Console/Application
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

**Monitoring:**
```bash
# View live logs
tail -f /var/log/nginx/access.log

# Check errors
grep ERROR app.log

# Count 404s
grep "404" /var/log/nginx/access.log | wc -l
```

---

## Backups

### Database Backups

**Automatic Backup (Daily)**
```bash
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp /app/database.db "$BACKUP_DIR/database_$TIMESTAMP.db"
gzip "$BACKUP_DIR/database_$TIMESTAMP.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "database_*.db.gz" -mtime +30 -delete
```

**Manual Backup**
```bash
cp database.db database_backup_$(date +%Y%m%d).db
```

**Restore from Backup**
```bash
# Stop application
systemctl stop campus-recovery-hub

# Restore backup
cp database_backup_20240101.db database.db

# Start application
systemctl start campus-recovery-hub
```

### User Uploads Backup

```bash
# Backup uploads folder
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz static/uploads/
tar -czf qrcodes_backup_$(date +%Y%m%d).tar.gz static/qr_codes/
```

### Remote Backup

```bash
# AWS S3 backup script
aws s3 cp database.db s3://your-bucket/backups/database_$(date +%Y%m%d).db
aws s3 cp static/uploads/ s3://your-bucket/uploads/ --recursive
```

### Backup Verification

```bash
# Test backup integrity
sqlite3 database_backup.db ".tables"

# Verify file size
ls -lh database_backup.db
```

---

## Updates and Upgrades

### Dependency Updates

**Check for outdated packages**
```bash
pip list --outdated
```

**Update specific package**
```bash
pip install --upgrade package_name
```

**Update all packages safely**
```bash
# In test environment first
pip install -r requirements_latest.txt
# Test thoroughly
# Then update production
```

### Flask Updates

```bash
# Check current version
pip show Flask

# Update Flask
pip install --upgrade Flask

# Check compatibility
python -c "import flask; print(flask.__version__)"
```

### Python Version Updates

1. Test new Python version in development
2. Install on staging server
3. Run full test suite
4. Deploy to production

---

## Performance Tuning

### Database Optimization

**Check database size**
```bash
sqlite3 database.db "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"
```

**Optimize database**
```bash
sqlite3 database.db "VACUUM;"
sqlite3 database.db "ANALYZE;"
```

**Monitor slow queries**
```python
# Enable query logging in app.py
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
```

### Gunicorn Tuning

**Optimal worker count**
```bash
# CPU cores * 2 + 1
# For 4 cores: 9 workers
gunicorn -w 9 app:app
```

**Increase timeout for slow requests**
```bash
gunicorn --timeout 120 app:app
```

### Nginx Optimization

```nginx
# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=cache:10m;
proxy_cache cache;
proxy_cache_valid 200 1h;
```

### Image Optimization

```bash
# Compress uploaded images
mogrify -resize 1920x1920 -quality 85 static/uploads/*.jpg
```

---

## Troubleshooting

### High Memory Usage

```bash
# Check memory
free -h

# Find memory hogs
ps aux --sort=-%mem | head

# Restart application
systemctl restart campus-recovery-hub
```

### Database Issues

```bash
# Check database integrity
sqlite3 database.db "PRAGMA integrity_check;"

# Repair corrupted database
sqlite3 database.db ".dump" > dump.sql
rm database.db
sqlite3 database.db < dump.sql
```

### Slow Requests

1. Check database indexes
2. Review database queries
3. Check network issues
4. Monitor server resources

### Email Issues

```bash
# Test SMTP connection
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).quit()"

# Check credentials
grep MAIL_ .env
```

### Upload Issues

```bash
# Check permissions
chmod -R 755 static/uploads
chmod -R 755 static/qr_codes

# Check disk space
df -h

# Check file size limit
curl -X POST -F "file=@large.jpg" http://localhost:5000/
```

---

## Security

### Regular Security Checks

- Update dependencies
- Review access logs for suspicious activity
- Check SSL/TLS certificate validity
- Monitor for brute force attempts
- Review user permissions

### Password Management

```bash
# Generate secure password for .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Access Control

```bash
# Use firewall to restrict access
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

### SSL/TLS Certificates

```bash
# Let's Encrypt renewal
certbot renew

# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/domain/cert.pem -noout -dates
```

### Monitoring for Threats

```bash
# Monitor login attempts
grep "Failed login" app.log | wc -l

# Monitor for SQL injection attempts
grep "SQL" /var/log/nginx/error.log

# Monitor for XSS attempts
grep "script" /var/log/nginx/access.log
```

---

## Scaling

### Horizontal Scaling

1. Set up load balancer (Nginx, HAProxy)
2. Deploy multiple application instances
3. Use shared database
4. Share file storage (S3, NFS)

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Optimize database queries
3. Increase Gunicorn workers
4. Add caching layer

### Database Scaling

1. Basic: Regular maintenance and optimization
2. Advanced: Read replicas, database sharding
3. Cloud: Managed database services (RDS, Firestore)

---

## Documentation

Keep documentation updated:
- Update README for new features
- Document configuration changes
- Maintain deployment procedures
- Keep runbooks for common tasks
- Document known issues

---

## Support

For issues or questions:
1. Check this guide first
2. Review logs and error messages
3. Search issues in repository
4. Create detailed bug report

---

**Last Updated**: 2024
**Version**: 2.0.0
