Design Specification — Classroom-style LMS Dashboard UI
Reusable system, extended for a Voting module and a MOS (Mean Opinion Score) TTS Evaluation tool

Source: single screenshot of a Google Classroom "Classwork" screen (course dashboard, list of assignments). Sections marked [Inferred] are not directly visible in the source screenshot and have been extrapolated from the visible tokens to keep the system internally consistent and reusable. Sections marked [Observed] are read directly off the screenshot. Note: the floating panel in the bottom-right of the screenshot ("เครื่องมือสนิป" / Snipping Tool) is an OS-level screenshot-utility overlay, not part of the site's UI — it is excluded from this spec.

1. Overview
A dense, utilitarian productivity/dashboard UI (Material Design language). Two-region app shell: a persistent left navigation rail and a content area with its own secondary tab bar. Optimized for scanning lists of items (assignments, classes) rather than a single focused task — the opposite pattern from a single-purpose login screen, and a good base for any "manage many items, drill into one" flow (a lab list, a set of votes, a queue of audio clips to rate).

Design principles to carry forward:

One primary accent color (blue) for the one primary action + all interactive links/active states; everything else neutral gray/white.
Flat, low-elevation surfaces — color-fill "promo" cards instead of shadowed cards; ordinary content is just rows on white, separated by hairline dividers.
Icon-first affordances: every list row, nav item, and secondary action is anchored by a small monochrome icon.
Left rail for global navigation + entity switching (classes); top-of-content tabs for switching views within the current entity.
2. Visual Style
Attribute	Value
Overall tone	Utilitarian, calm, productivity-tool (Google Material Design)
Shape language	Mostly rounded rectangles (8–12px radius) for buttons/cards/inputs; fully circular avatars and icon buttons
Surface style	Flat, minimal elevation; one soft accent-tint card (the promo banner) is the only non-white surface [Observed]
Contrast strategy	White/near-white base, gray dividers, blue used sparingly and only for interactive/primary elements
Imagery	Small flat vector illustrations only (the promo banner icon); no photography
3. Color Palette
Token	Approx. Hex	Usage
--color-primary-blue	#1A73E8	Primary button fill, active tab underline + label, links, "Create" CTA
--color-accent-tint	#E8F0FE	Promo/informational banner background
--color-bg	#FFFFFF	Page and sidebar background
--color-bg-subtle	#F8F9FA [Inferred]	Hover state background for nav/list rows
--color-text-primary	#202124	Headings, primary body text
--color-text-secondary	#5F6368	Nav labels, metadata, status text ("Draft")
--color-border	#DADCE0	Dividers, input/dropdown borders
--color-avatar-1 (orange)	#F9AB00	Class/entity avatar accent
--color-avatar-2 (blue)	#1A73E8	Class/entity avatar accent
--color-avatar-3 (teal)	#12B5CB	Class/entity avatar accent
--color-avatar-4 (purple)	#9334E6	Class/entity avatar accent
--color-selected-bg	#C2E7FF [Observed]	Background of the currently-selected sidebar entity
Usage rule: blue = "this is interactive / this is primary / this is currently active." Everything else stays gray or white. Avatar colors are decorative/identifying only — never reused for functional meaning (status, error, etc.).

4. Typography
Role	Weight	Approx. Size	Notes
App bar title ("Classroom")	Medium	~22px	Text-primary, paired with small logo icon
Breadcrumb / course name	Regular	~18–20px	Text-secondary → text-primary, truncates with ellipsis when long
Sidebar nav item	Regular	~14px	Text-primary, icon + label pair
Section header ("Labs")	Medium	~16px	Text-primary
List item label ("Lab 15")	Regular	~14px	Text-primary
Status text ("Draft")	Regular, italic	~13px	Text-secondary
Link text ("Learn more", "Collapse all")	Medium	~13–14px	Primary blue, no underline except inline text links
Banner heading	Regular/Medium	~20px	Text-primary
Banner body	Regular	~14px	Text-secondary
Typeface [Inferred]: Consistent with Google's Material Design system — Google Sans for headings/emphasis, Roboto for body/UI text.

font-family: "Google Sans", "Roboto", -apple-system, "Segoe UI", sans-serif;
5. Spacing System
Base unit: 8px (standard Material Design grid).

Token	Value	Usage
--space-1	8px	Icon-to-label gap, tight internal padding
--space-2	16px	Padding inside list rows, gap between related controls
--space-3	24px	Padding inside the promo banner card, section top margins
--space-4	32px	Gap between major content blocks (banner → filter bar → section list)
--space-6	48–56px	Top app bar height
--space-8	260–280px [Inferred]	Left sidebar width
6. Grid / Layout
App shell: fixed-height top app bar (~64px) spanning full width; below it, a fixed-width left sidebar + fluid main content area, both scrolling independently.
Top app bar: three-zone flex — [menu icon + logo + product name + breadcrumb] (left, grows) — [utility icons: apps grid, avatar] (right, fixed).
Sidebar: vertical stack of icon+label nav rows, grouped into sections (top-level items, then "Teaching" as a collapsible group containing the class list, then "Enrolled" as a second collapsible group). No columns — single list, indentation implies grouping.
Content area: top-anchored secondary tab bar (Stream/Classwork/People/Grades) with right-aligned utility icons, then a vertical stack of: promo banner → filter/actions row → collapsible sections, each section containing a vertical list of rows.
List rows: consistent [icon] [label] ......flex-grow spacer...... [meta/status] [overflow menu] pattern, full-width, divided by 1px hairlines.
7. Navigation
Primary (left sidebar): icon + label rows (Home, Calendar, Resources, Gemini w/ notification dot). Two collapsible groups below (chevron-toggled): "Teaching" (currently expanded, listing classes as colored circular initials + two-line label) and "Enrolled" (collapsed). The active/selected class row gets a filled pill background (--color-selected-bg) spanning the full row width.
Secondary (content tabs): Stream / Classwork / People / Grades, plain text tabs, active tab = blue text + blue underline (2–3px, full label width); inactive tabs = gray text, no underline. "Grades" carries a small blue notification dot.
Breadcrumb: single-level, Classroom > [Course name], chevron separator, truncates long course names with an ellipsis.
Utility icons (top-right of content): calendar, an AI/practice-set icon, and settings (gear) — plain outline icons, no labels, tooltip-only affordances [Inferred].
8. Buttons
Variant	Fill	Text	Border	Icon	Use for
Primary (filled)	Solid --color-primary-blue, rounded rect (~24px radius / stadium)	White, medium weight	none	White leading icon (e.g. "+")	The one main creation/submission action per screen (e.g. "+ Create")
Text/link button	Transparent	--color-primary-blue, medium weight	none	Optional small leading icon	Secondary actions inline with content ("Learn more", "Select class standard sets", "Share class content", "Collapse all")
Icon-only button	Transparent, circular hit area	--color-text-secondary icon, turns primary-blue or gets a tinted circular background on hover/active	none	Single glyph	Overflow menus (⋮), close (×), app-bar utilities
Rule: exactly one filled/primary button per screen (the "Create" action); all other actions are text links or icon buttons — this keeps the dense list-heavy layout from feeling button-heavy.

9. Cards
Two distinct card patterns are actually present in this source (unlike the earlier login-only spec):

A. Promo/info banner card [Observed]

Property	Value
Background	--color-accent-tint (light blue fill)
Corner radius	~12px
Padding	24px
Content	Small flat illustration (left) + heading + body copy + inline links (right-aligned "Select class standard sets")
Dismiss	× icon, top-right corner
B. List-row "card" [Observed]

Property	Value
Background	White (no fill distinction from page)
Border	none — separated only by a 1px bottom divider (--color-border)
Padding	16px vertical, 24px horizontal
Content	Leading circular icon badge + label (grows) + trailing meta text/status + overflow icon
Grouping	Rows are grouped under a collapsible section header with its own chevron + overflow menu
Use pattern A for one-off announcements/callouts; use pattern B for any repeating list of items — this is the natural fit for a list of votes, ballots, or queued audio samples.

10. Forms
Element	Style
Dropdown/select ("Topic filter")	White fill, 1px --color-border, ~4–8px radius, floating label above the box, chevron icon right-aligned
Filled primary button	See Section 8
Text input [Inferred — not present in source]	Same treatment as the dropdown: bordered box, floating label, focus state switches border to --color-primary-blue (2px)
Checkbox/radio [Inferred]	Square (checkbox) or circular (radio) outline in --color-border, fills solid --color-primary-blue with white check/dot when selected — matches Material Design conventions
11. Icons
Style: Material Design outline/filled icon set — simple, single-color, consistent 24px grid.
Usage split: outline style for neutral/nav icons (calendar, settings, overflow); filled circular badges for avatars and list-item leading icons (e.g. the assignment/document icon).
Notification affordance: small solid blue dot overlaid on an icon or tab label (seen on "Gemini" and "Grades") indicates unread/new state.
New icons for extensions [Inferred]: reuse the same 24px outline grid — a checkmark-in-circle for "vote submitted," a play/pause + waveform glyph for the MOS TTS audio row, a star or numeric badge for the rating control.
12. Responsive Behavior [Inferred — single desktop breakpoint visible]
Breakpoint	Behavior
≥1024px (desktop)	As observed: full labeled sidebar + wide content column
768–1023px (tablet)	Sidebar collapses to icon-only (labels hidden), toggled by the hamburger; content column keeps full-width rows
<768px (mobile)	Sidebar becomes an off-canvas drawer (hidden by default, opened via hamburger, overlays content); secondary tab bar becomes horizontally scrollable; list-row meta text (e.g. "Draft") may drop to a second line or an icon-only badge
13. Hover / Active States [Inferred — static image, limited direct evidence]
Element	Rest	Hover	Active/Selected
Sidebar nav row	Transparent bg	--color-bg-subtle fill	Filled --color-selected-bg pill (full row width, rounded ends) — [Observed] for the current class
Content tab	Gray text, no underline	Text darkens slightly	Blue text + blue underline — [Observed] for "Classwork"
List row	White bg	--color-bg-subtle fill across the row	n/a (rows aren't persistently selected)
Primary button	Solid blue	Slightly darker blue (~8%)	Darker still (~15%) + subtle inset/ripple
Icon button	No visible bg	Light circular tinted bg appears behind the icon	Slightly darker circular bg
14. Animation & Motion [Inferred — none visible in a static screenshot]
Section expand/collapse (chevron toggle on "Labs", "Teaching", "Enrolled"): height/opacity transition, ~200ms ease-in-out, chevron rotates 180°.
Sidebar drawer open/close (mobile): 250ms slide + backdrop fade.
Buttons: Material-style ripple emanating from the click point on primary/icon buttons.
Banner dismiss (×): fade + collapse height, ~150–200ms.
List row hover: background fade-in, ~100ms — fast, since it's a frequent, low-stakes interaction across many rows.
15. Component Hierarchy
App Shell
├── Top App Bar
│   ├── Menu (hamburger) + Product logo + Product name
│   ├── Breadcrumb (Product name > Current entity, truncating)
│   └── Utility Cluster (apps grid icon, user avatar)
│
├── Left Sidebar
│   ├── Primary Nav List (Home, Calendar, Resources, Gemini•)
│   ├── Collapsible Group — "Teaching"
│   │   └── Entity List (colored avatar + 2-line label per class; selected = filled pill)
│   └── Collapsible Group — "Enrolled"
│
└── Main Content
    ├── Secondary Tab Bar (Stream / Classwork / People / Grades•) + Utility icons (calendar, AI, settings)
    ├── Primary Action — Button (+ Create)
    ├── Promo Banner Card (illustration + heading + body + link + dismiss)
    ├── Filter / Actions Row (Topic filter dropdown ⟷ Share class content / Collapse all links)
    └── Collapsible Section (e.g. "Labs")
        └── List Row × N (icon + label + status + overflow) …

    ── [Extension] Voting Module ──
    ├── Secondary Tab Bar reused for view-switching (e.g. Open / Closed / Results)
    ├── Primary Action — Button ("+ Create ballot" / "Cast Vote")
    ├── Collapsible Section per ballot/topic
    │   └── List Row per option (icon + option label + live tally as trailing meta, matches "Draft" status pattern)

    ── [Extension] MOS TTS Evaluation Tool ──
    ├── Secondary Tab Bar (Queue / Rated / Results)
    ├── Collapsible Section ("Samples to rate")
    │   └── List Row per audio sample
    │       ├── Leading icon → Play/Pause control (reuses list-row icon-badge slot)
    │       ├── Label → sample/file name
    │       └── Trailing meta → 1–5 rating control (replaces "Draft" status slot) or "Rated" once complete
    └── Primary Action — Button ("Submit ratings")
16. Extending the System — Voting & MOS TTS Notes
Both extensions map onto the list-of-items pattern this UI is already built for, rather than the single-task pattern of a login screen:

Voting module: A ballot or topic becomes a collapsible section (exactly like "Labs"); each candidate/option becomes a list row using the same icon-badge + label + trailing-meta + overflow layout, with the trailing-meta slot repurposed to show a live vote count or a "Voted" state instead of "Draft." The blue primary button remains the single call-to-action ("Cast Vote" / "+ Create ballot").
MOS TTS evaluation tool: Each audio sample becomes a list row; the leading icon-badge slot becomes a play/pause control instead of a static document icon, and the trailing-meta slot becomes a compact 1–5 rating control instead of a "Draft" label. The promo-banner pattern (Section 9A) is a good fit for onboarding copy ("Rate 10 samples to help us measure voice quality") with a dismiss option, exactly as used here for the learning-goals callout.
In both extensions, keep the one-blue-button rule: exactly one filled primary action per screen; every other control is a text link, icon button, or the trailing-meta control inside a row — never a second filled button competing for attention.
End of specification. This document defines reusable tokens and patterns; no implementation code included per request.