# Workflow One Architecture

## Goal

Generate a weekly newsletter about newly published veterinary medicine research relevant to dogs and cats, then deliver it to an email list.

## Core Workflow

1. A subscriber joins through a signup form.
2. The subscriber is stored in an email audience system.
3. A weekly job searches for new publications from the previous 7 days.
4. The workflow ranks and summarises the most relevant papers.
5. A draft newsletter is created in Markdown and HTML.
6. The draft is reviewed.
7. The newsletter is sent to the subscriber list.

## Recommended Stack

### Phase 1

- signup and list management: Mailchimp
- automation runner: Codex automation, cron, GitHub Actions, or server job
- literature source: Europe PMC
- draft generation: Python script in this workspace
- sending: manual send in Mailchimp after review

### Phase 2

- custom signup page on your website
- sync to Mailchimp via API
- optional AI rewrite of article summaries
- automatic campaign creation through Mailchimp API

### Phase 3

- full auto-send after rules-based checks
- segmentation by topic, profession, or species interest
- analytics feedback loop from opens and clicks

## Suggested Data Fields

For subscribers:

- email
- first_name
- last_name
- consent_status
- source
- created_at

For newsletter issues:

- issue_date
- source_window_start
- source_window_end
- article_count
- draft_markdown_path
- draft_html_path
- status

## Why Review-First Is Better At The Start

Even if full automation is possible, automatic sending is not the best first version. A review step protects you from:

- irrelevant papers
- duplicate topics
- weak summaries
- awkward wording
- accidental compliance mistakes

## What To Automate First

Automate this first:

1. article discovery
2. article ranking
3. newsletter draft generation

Automate this later:

1. audience syncing
2. campaign creation
3. final send

## Output Standard

Each weekly run should produce:

- one JSON file with the fetched papers
- one Markdown draft
- one HTML draft
- one short run summary for review

## Recommended Weekly Run

- frequency: weekly
- day: Monday
- time: 08:00
- timezone: Europe/London

That gives you time to review and send the newsletter later the same day.
