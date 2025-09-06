# Security Configuration Guide

## 🔒 Required Environment Variables for Production

Before deploying to production, you **MUST** set these environment variables via your hosting platform's dashboard:

### Essential Security Variables

1. **SECRET_KEY** (Required)
   - Generate a secure 32+ character random string
   - Used for session security and encryption
   - Example: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **JWT_SECRET_KEY** (Required)
   - Generate a different secure 32+ character random string
   - Used for JWT token signing
   - Example: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Optional API Keys (Set if using these services)

3. **OPENAI_API_KEY** (Optional)
   - Your OpenAI API key for AI features
   - Only set if using OpenAI integration

4. **SENTRY_DSN** (Optional)
   - Sentry DSN for error monitoring
   - Only set if using Sentry

5. **SLACK_WEBHOOK_URL** (Optional)
   - Slack webhook for notifications
   - Only set if using Slack notifications

## 🚫 Security Best Practices

### Never Commit These to Git:
- `.env` files with real values
- API keys or tokens
- Database passwords
- Secret keys

### Always Use Environment Variables For:
- Database connection strings
- API keys
- JWT secrets
- Third-party service credentials

## 🛡️ Render.com Deployment

When deploying to Render:

1. Go to your service → Environment
2. Add these environment variables:
   - `SECRET_KEY=your-generated-secret-key`
   - `JWT_SECRET_KEY=your-generated-jwt-secret-key`
3. The database URL is automatically set via the `fromDatabase` configuration

## 🔍 Security Checklist

- [ ] All secrets removed from code/config files
- [ ] Environment variables set in hosting platform
- [ ] `.env` files added to `.gitignore`
- [ ] Database uses secure connection (SSL in production)
- [ ] CORS properly configured for your domain
- [ ] Rate limiting enabled
- [ ] Error monitoring configured (optional)

## 🆘 If Secrets Were Accidentally Committed

1. Immediately rotate/regenerate all exposed secrets
2. Update environment variables with new values
3. Consider using `git filter-branch` or BFG to remove from history
4. Force push the cleaned repository

## 📞 Security Contact

For security issues, please create a private issue or contact the development team directly.