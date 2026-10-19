# Updating the Pack 12 website

You do not need to install software or edit code.

## Change a meeting time, contact, or event

1. Open the [website editor](https://forest-newark.github.io/durham-pack-12-site/edit/).
2. Expand the section you want. Type in the boxes or use the date picker. Meeting time and location are shared across the homepage, so update them once.
3. Click **Download your update**. Your browser saves **site.json**. If it adds a number to the name, rename the downloaded file to exactly **site.json**.
4. Click **Open GitHub upload** in the editor. Sign in to GitHub if asked.
5. Drop **site.json** into the **content** folder. Check that you are replacing **content/site.json**, not uploading it at the repository root.
6. Enter a short description, such as “Update November meetings.” Commit the change, or propose it on a branch if GitHub requires review.
7. Open the repository's **Actions** tab. When **Check and deploy Pack 12 Pages** is green, refresh the website. A build may take a few minutes. An unsuccessful build keeps the last successful website online.

The editor does not publish by itself. Only people with repository access can publish through GitHub. Never paste a password or access token into the editor.

## Add, hide, or remove an event

Open **Events and dates**, then **Add event**. Fill in its title, date, local Durham time, meeting place, and description. The details link is optional. Uncheck **Show this event** to keep a draft event off the site. Remove an entry to delete it.

Upcoming events are sorted by date and time. Events move into **Past events** after their calendar date, on the next daily build. Empty event lists show the contact message instead of made-up dates. Edit that message under **Events section introduction**.

## Replace a calendar or guide

1. [Upload the PDF to uploads](https://github.com/Forest-Newark/durham-pack-12-site/upload/main/uploads) first. Use a name such as **calendar-2027.pdf**.
2. Open the editor's **Calendars, guides, and resource links** section.
3. Change its description and resource link. For that example, enter **./uploads/calendar-2027.pdf**.
4. Download and upload **site.json** as above.

Use a full **https://** link for documents hosted elsewhere. The original documents and links remain accessible in the dated original-resources archive.

## Save work for later

**Save draft on this device** keeps work in this browser only. To continue, open **Import, restore, or discard a draft** and restore it. You can also import a previously downloaded site.json.

Start each new update from the current published content. A downloaded file contains the whole site’s editable content; uploading an old one can overwrite someone else's newer changes. Review GitHub’s file changes before committing.

## If an update fails

Read the failed workflow's **Validate editable content** or build step. Messages identify the section and entry to fix. Common causes are an empty required field, an impossible date, an incomplete URL, or a PDF filename that does not match the upload. Fix the form, download again, and replace site.json again.

To undo a published change, open content/site.json in GitHub, view its file history, and restore the previous version.

## Where things live

- **content/site.json**: all routine updates. The browser editor writes this for you.
- **uploads/**: new PDF documents and images.
- **templates/**, **scripts/**, **styles.css**, **edit/**: maintained by a developer; volunteers do not need to edit these.
- **PhotoBook/**: preserved original photo routes and album pages.
