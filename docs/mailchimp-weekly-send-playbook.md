# Mailchimp Weekly Send Playbook

Use this playbook each time a newsletter issue is ready to send.

## Before you build the campaign

1. Open the latest GitHub Actions artifact.
2. Download the issue zip.
3. Review:
   - `newsletter.md`
   - `newsletter.html`
   - `review-summary.md`
4. Confirm:
   - issue date is correct
   - article order is sensible
   - branding, logo, and signature are present
   - links open correctly
   - the tone reads cleanly in British English

## Create the campaign in Mailchimp

Recommended campaign type:

- regular email campaign

Recommended sender settings:

- `From name`: `Fabrizio Tucciarone | Mobile Vet Referral`
- `From email`: your authenticated `mobilevetreferral.co.uk` mailbox
- `Reply-To`: the same business mailbox

Recommended audience:

- `Mobile Vet Referral Newsletter`

## Subject line formula

Use one of these simple patterns:

- `Vet Weekly Digest | 13/04/2026`
- `Weekly Veterinary Newsletter | 13/04/2026`
- `This Week in Veterinary Reading | 13/04/2026`

Keep the subject line factual and consistent. Do not over-promise.

## Preview text formula

Recommended style:

- `Editorial summaries of new dog and cat veterinary papers with practical first-opinion relevance.`

Alternative:

- `This week's selected papers in small-animal medicine, with concise editorial interpretation and clinical context.`

## Paste the HTML

1. In Mailchimp, choose the option to paste or import custom HTML.
2. Open `newsletter.html` locally.
3. Copy the full HTML.
4. Paste it into the Mailchimp HTML editor.
5. Save and open the preview.

## Pre-send check

Before sending any test email, confirm:

- logo loads
- date shows in `dd/mm/yyyy`
- links point to the correct article DOIs or source pages
- your signature appears at the end
- spacing still looks acceptable in Mailchimp preview

## Test-send sequence

Send tests to:

- your business mailbox
- one mobile inbox you can inspect easily

Review on both:

- desktop
- phone

Check:

- subject line
- preview text
- logo rendering
- spacing and paragraph breaks
- article links
- unsubscribe footer

## Final send rule

Only send to the full audience when:

- the test emails look correct
- the links work
- the copy reads cleanly
- the unsubscribe footer is present

If something looks off, edit the HTML or regenerate the issue first. Do not send a compromised draft just because the workflow succeeded.
