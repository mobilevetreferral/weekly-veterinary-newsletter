# Workflow One: Weekly Veterinary Newsletter

This workspace contains a starter workflow for a weekly newsletter focused on new veterinary medicine articles about dogs and cats.

## Is It Possible?

Yes. The full system is realistic and can be built in stages:

1. Collect subscribers with a hosted, embedded, or custom signup form.
2. Run a weekly research workflow to find new dog and cat veterinary papers.
3. Generate a draft newsletter in Markdown and HTML.
4. Send the approved newsletter through a delivery platform such as Mailchimp.

## Recommended Rollout

The safest launch path is:

1. Use Mailchimp to collect subscribers and manage unsubscribes.
2. Run the weekly research and draft-generation automatically.
3. Review the draft before sending.
4. Add full API-based sending later, once the content and audience workflow are stable.

This reduces compliance risk and avoids sending weak or off-topic summaries automatically.

## What This Starter Already Does

The script at [scripts/newsletter_workflow.py](/Users/sarahtucci/Documents/Newsletter automations/scripts/newsletter_workflow.py) will:

1. Search Europe PMC for the last 7 days of dog and cat veterinary articles.
2. Rank and select the most relevant papers.
3. Save raw article data as JSON.
4. Generate richer abstract-level analyses with technical synopsis, study design, key findings, and first-opinion relevance.
5. Generate a branded newsletter draft in Markdown.
6. Generate a branded HTML version that can be adapted for email platforms.
7. Generate a review summary for GitHub Actions and weekly editorial approval.

## Quick Start

Run the workflow:

```bash
python3 scripts/newsletter_workflow.py run
```

The script automatically reads branding values from [`.env`](/Users/sarahtucci/Documents/Newsletter automations/.env) when present.

Run it for a custom window:

```bash
python3 scripts/newsletter_workflow.py run --start-date 2026-04-01 --end-date 2026-04-08 --max-articles 8
```

Generated files are written to:

- `data/issue-YYYY-MM-DD/articles.json`
- `output/issue-YYYY-MM-DD/newsletter.md`
- `output/issue-YYYY-MM-DD/newsletter.html`
- `output/issue-YYYY-MM-DD/review-summary.md`

## Launch Automation Assets

The launch MVP now includes:

- [weekly-newsletter.yml](/Users/sarahtucci/Documents/Newsletter automations/.github/workflows/weekly-newsletter.yml) for GitHub Actions scheduling and artifacts
- [github-actions-setup.md](/Users/sarahtucci/Documents/Newsletter automations/docs/github-actions-setup.md) for repository and workflow setup
- [mailchimp-launch-checklist.md](/Users/sarahtucci/Documents/Newsletter automations/docs/mailchimp-launch-checklist.md) for audience, consent, and sender setup
- [mailchimp-weekly-send-playbook.md](/Users/sarahtucci/Documents/Newsletter automations/docs/mailchimp-weekly-send-playbook.md) for the week-by-week campaign build and send steps
- [monday-review-sop.md](/Users/sarahtucci/Documents/Newsletter automations/docs/monday-review-sop.md) for the weekly review and send process
- [wordpress-newsletter-page.md](/Users/sarahtucci/Documents/Newsletter automations/docs/wordpress-newsletter-page.md) and [wordpress-newsletter-page.html](/Users/sarahtucci/Documents/Newsletter automations/templates/wordpress-newsletter-page.html) for the WordPress signup page handoff

## Suggested Production Architecture

### Option A: Recommended MVP

- Signup form: Mailchimp hosted form or embedded Mailchimp form on your site
- Subscriber storage: Mailchimp audience
- Weekly agent: scheduled automation or cron job
- Research source: Europe PMC or PubMed
- Draft creation: local Python workflow plus optional AI editing
- Sending: manual review, then send with Mailchimp

This is the fastest path to launch.

### Option B: Full Custom System

- Signup form on your website
- Subscriber database in your own backend
- Sync subscribers to Mailchimp through API
- Weekly article search and draft generation
- Auto-create and send campaigns through Mailchimp API

This gives more control, but it is more work and carries more compliance responsibility.

## Subscriber Form Options

You asked whether the input system can be a page on your website or another form system. Both are possible.

### Simplest

Use Mailchimp's hosted or embedded signup form and collect:

- email address
- first name
- last name

Advantages:

- unsubscribe handling is already included
- consent settings are easier
- list management is easier
- no custom database is required to start

### More Custom

Build your own form and send the data to:

- your own database first, then sync to Mailchimp
- Mailchimp directly through API

Use this only if you need custom logic, custom branding, or extra fields.

## Compliance Notes

If you are collecting subscribers in the UK or EU, make sure you:

1. collect explicit consent for marketing email
2. keep unsubscribe links enabled
3. consider double opt-in
4. store proof of consent

Mailchimp can help with this when configured correctly.

## Next Build Steps

1. Choose whether subscriber capture should live directly in Mailchimp or on your website.
2. Decide whether newsletter sending should be review-first or fully automatic.
3. Customize the query terms for your clinical interests.
4. Add Mailchimp API integration only after the draft quality is reliable.

## References

- [Mailchimp signup form options](https://mailchimp.com/help/about-signup-form-options/)
- [Mailchimp hosted signup forms](https://mailchimp.com/help/create-a-hosted-signup-form/)
- [Mailchimp subscriber API](https://mailchimp.com/developer/marketing/api/list-members/add-or-update-list-member/)
- [Mailchimp campaigns API](https://mailchimp.com/developer/marketing/api/campaigns/)
- [Mailchimp GDPR consent guidance](https://mailchimp.com/help/collect-consent-with-gdpr-forms/)
- [Mailchimp double opt-in guidance](https://mailchimp.com/help/about-double-opt-in/)
- [Europe PMC REST API](https://europepmc.org/RestfulWebService)
- [NCBI Entrez E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
