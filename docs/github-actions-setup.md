# GitHub Actions Setup

This project is ready for a GitHub Actions based weekly run, but the current workspace was not originally a Git repository. Use this checklist to move it into production.

## 1. Create the repository

1. Create a new **private** GitHub repository for this workspace.
2. Initialise the local repository if it is not already initialised:

```bash
git init -b main
git add .
git commit -m "Initial weekly newsletter automation"
```

3. Add the GitHub remote and push:

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 2. Workflow file

The scheduled workflow is already present at [weekly-newsletter.yml](/Users/sarahtucci/Documents/Newsletter automations/.github/workflows/weekly-newsletter.yml).

It provides:

- `workflow_dispatch` for manual runs
- Monday schedule coverage for **08:00 Europe/London**
- artifact upload for the issue data and drafts
- a GitHub Actions run summary based on the generated issue

GitHub Actions cron uses UTC, so the workflow includes two Monday cron entries and only proceeds when the actual local time in `Europe/London` is 08:00.

## 3. Repository variables

Add these as **Repository variables** in GitHub:

- `NEWSLETTER_TIMEZONE`
- `NEWSLETTER_BRAND_NAME`
- `NEWSLETTER_LOGO_URL`
- `NEWSLETTER_LOGO_ALT`
- `NEWSLETTER_EDITOR_NAME`
- `NEWSLETTER_CONTACT_NAME`
- `NEWSLETTER_CONTACT_CREDENTIALS`
- `NEWSLETTER_CONTACT_COMPANY`
- `NEWSLETTER_CONTACT_LOCATION`
- `NEWSLETTER_CONTACT_PHONE`
- `NEWSLETTER_CONTACT_WEBSITE`
- `NEWSLETTER_SITE_URL`

Recommended values for launch:

- `NEWSLETTER_TIMEZONE=Europe/London`
- `NEWSLETTER_BRAND_NAME=Vet Weekly Digest`
- `NEWSLETTER_LOGO_URL=https://mobilevetreferral.co.uk/wp-content/uploads/2024/01/mobile-vet-referral-high-resolution-logo-transparent.png`
- `NEWSLETTER_LOGO_ALT=Mobile Vet Referral`
- `NEWSLETTER_EDITOR_NAME=Fabrizio Tucciarone`
- `NEWSLETTER_CONTACT_NAME=Fabrizio Tucciarone`
- `NEWSLETTER_CONTACT_CREDENTIALS=DVM MRCVS GPcert(SAM) MSc PgCert(Endo) CertAVP`
- `NEWSLETTER_CONTACT_COMPANY=Mobile Vet Referral Ltd`
- `NEWSLETTER_CONTACT_LOCATION=Northampton`
- `NEWSLETTER_CONTACT_PHONE=07440765031`
- `NEWSLETTER_CONTACT_WEBSITE=https://www.mobilevetreferral.co.uk`
- `NEWSLETTER_SITE_URL=https://www.mobilevetreferral.co.uk`

## 4. First run checks

After pushing the repository:

1. Run **Actions -> Weekly Veterinary Newsletter -> Run workflow**
2. Leave the inputs blank for a normal issue
3. Confirm the run uploads one artifact bundle
4. Open the workflow summary and confirm:
   - issue date
   - source window
   - article count
   - top article titles
   - output paths

## 5. Production expectation

The GitHub Actions workflow is the scheduled generator only.

It does **not**:

- create a Mailchimp campaign
- send the newsletter
- touch WordPress

Those remain manual launch tasks in v1.
