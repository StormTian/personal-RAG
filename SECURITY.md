# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible
receiving such patches depend on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to our security team.
You can reach us via email at security@example.com.

**Please do not report security vulnerabilities through public GitHub issues.**

Please include the requested information listed below (as much as you can provide)
to help us better understand the nature and scope of the possible issue:

* Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Response Process

1. Your report will be acknowledged within 5 business days
2. We will investigate and determine the impact and severity
3. We will work on a fix and keep you informed of progress
4. Once fixed, we will release a security update
5. We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Measures

This project implements the following security measures:

* **Input Validation**: All user inputs are validated and sanitized
* **Dependency Scanning**: Regular security scans of dependencies using Bandit and Safety
* **Code Review**: All changes require review before merging
* **Secret Detection**: Pre-commit hooks detect accidental commits of secrets
* **Container Security**: Docker images run as non-root user
* **Rate Limiting**: API endpoints have rate limiting to prevent abuse

## Known Security Considerations

### Document Processing

* The application processes user-provided documents (PDF, Word, Markdown, Text)
* Documents are processed locally and not sent to external services
* When using OpenAI embeddings, only text chunks are sent (not full documents)

### API Security

* The API does not implement authentication by default
* In production, deploy behind a reverse proxy (Nginx) with appropriate access controls
* Consider adding API key authentication for multi-user deployments

### Environment Variables

* API keys and secrets should be stored in environment variables
* Never commit `.env` files to version control
* Use `.env.example` as a template

## Security Best Practices

When deploying this application:

1. **Use HTTPS**: Always use HTTPS in production
2. **Regular Updates**: Keep dependencies up to date
3. **Access Control**: Restrict access to the application
4. **Logging**: Monitor logs for suspicious activity
5. **Backups**: Regularly back up your document library
6. **Secrets Management**: Use a secrets manager for API keys

## Security Tools Used

* **Bandit**: Python security linter
* **Safety**: Python dependency vulnerability scanner
* **Gitleaks**: Secret detection in commits
* **Trivy**: Container vulnerability scanner
* **Hadolint**: Dockerfile linter

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions
2. Audit code to find any potential similar problems
3. Prepare fixes for all supported versions
4. Release new versions and notify users
5. Publicly disclose the issue after 30 days or once users have had time to update

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a
pull request or open an issue to discuss.
