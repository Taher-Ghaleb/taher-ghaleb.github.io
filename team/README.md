# Member profiles

Both the homepage carousel and `members.html` read `team/members.json`.
Replace the sample profiles or add more objects to the `members` array.
Members are sorted by start month/year, newest first; array order breaks ties for
members with the same start date. Current members appear in the homepage
carousel; the Members page includes both current members and alumni.
The top-level `categories` array sets the category labels and order on the Members
page; empty categories are hidden. The same date sorting applies within each category.

Profile fields:

- `id`: a unique, stable identifier.
- `name`: the member's name.
- `role`: degree or research role.
- `category`: `"phd"`, `"masters"`, or `"undergrad-interns"`, used to group profiles under both Current Members and Alumni.
- `university`: an object with `name` (full name, used on hover) and `shortName` (badge label), e.g. `{"name": "Trent University", "shortName": "Trent"}` or `{"name": "École de technologie supérieure", "shortName": "ÉTS"}`.
- `university.accent`: `"green"` for Trent or `"red"` for ÉTS, controlling the university badge color.
- `topics`: an array of research topics.
- `startDate` and `endDate`: `YYYY-MM` strings, e.g. `"2026-09"`, displayed as `Sep 2026`. Use `null` for an ongoing end date (shown as `Present`). Unknown start dates display as `Start date to be added`.
- `status`: `"current"` or `"alumni"`.
- Photos are automatically discovered by full name or member ID, e.g.
  `Bushra-Anjum-Khan.png` for Bushra Anjum Khan. Just add the image to `team/photos/`;
  no profile edits are needed. Supported formats: WebP, JPG/JPEG, PNG, AVIF, GIF, SVG.
  Matching ignores uppercase/lowercase, including the extension.
- `photo`: optional filename override for a real photo with a different name.
  A configured placeholder does not prevent automatic discovery of a real photo.
  GitHub Pages automatically builds `photo-index.json` through
  Jekyll; the local Python preview reads its photo directory listing. Keep Jekyll
  processing enabled when publishing, and do not store two photos that differ
  only in letter case.
- `placeholderPhoto`: fallback portrait, e.g. `"placeholder-male.svg"` or
  `"placeholder-female.svg"`. Missing or broken photos use this automatically.
- `photoPosition`: crop focus, e.g. `"center"` or `"50% 30%"`. Move this toward the face if a photo's automatic centered crop needs adjustment.
- `placeholder`: set to `false` once the profile is real. Placeholder profiles show a label and date placeholders instead of suggesting actual membership dates.

Photos use fixed circular frames with `object-fit: cover`: landscape, portrait,
and square photos keep their proportions and fill the same frame. Missing photos
fall back to `team/photos/placeholder.svg`. Use a clear photo with some space
around the face; `photoPosition` can refine the crop without editing the image.
