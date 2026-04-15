# WordPress Newsletter Page Setup

Create one dedicated newsletter landing page in WordPress.

Recommended page slug:

- `/newsletter`

Recommended page title:

- `Weekly Veterinary Newsletter`

## Purpose of the page

The page should:

- explain what readers will receive
- keep signups on-brand
- collect email, first name, and last name
- link clearly to the privacy policy
- use Mailchimp's embedded form for the actual submission

## Suggested page content

Use the ready-to-paste template at [wordpress-newsletter-page.html](/Users/sarahtucci/Documents/Newsletter automations/templates/wordpress-newsletter-page.html).

Before publishing, replace:

- the Mailchimp form placeholder with the real embedded form code
- the privacy-policy URL placeholder with the live page URL on the site

## Recommended build sequence

1. Create the Mailchimp audience and embedded form first.
2. Copy the template into a WordPress Custom HTML block or equivalent builder block.
3. Paste the Mailchimp embed code into the marked signup section.
4. Replace the privacy-policy placeholder URL.
5. Preview the page on desktop and mobile.
6. Submit a test signup and confirm the double opt-in email arrives.

## Minimum content blocks

- headline
- short description of the newsletter
- statement that the content is for veterinary clinical reading
- consent wording for marketing email
- privacy-policy link
- Mailchimp embedded form
- confirmation note under the form

## Recommended launch wording

Keep the signup promise narrow and credible:

- weekly
- veterinary medicine
- dogs and cats
- editorial digest
- practical relevance for first-opinion practice

## Mailchimp embed settings to keep

When you generate the embedded form in Mailchimp, keep:

- email address visible and required
- first name visible
- last name visible
- audience tag or hidden source field for `website-newsletter`
- the success / confirmation wording below the form on the WordPress page

Avoid adding too many extra fields at launch. A short form usually converts better.
