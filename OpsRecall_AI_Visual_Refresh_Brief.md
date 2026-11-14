# OpsRecall AI --- Visual Identity Refresh

## Design-only implementation brief (before Part 3)

**Goal:** Give OpsRecall AI a distinctive visual identity instead of the
familiar AI-builder dark dashboard template. Keep every existing
feature, data flow, API call, component behavior, and business rule
exactly as it is. Change presentation only.

Paste this document into Cursor, Antigravity, or your coding assistant
while the cloned OpsRecall AI repository is open.

------------------------------------------------------------------------

## 1. Design direction: SIGNAL / FIELD NOTES

Create the feeling of a precision incident-response instrument designed
for engineers: part operational control room, part technical field
notebook.

Avoid the generic AI SaaS look: - No default purple-blue gradient
backgrounds. - No glowing borders around every card. - No oversized
rounded cards everywhere. - No glassmorphism as the main visual
language. - No constant floating, pulsing, or bouncing elements. - No
generic dashboard template or wholesale redesign of the information
architecture.

The interface should feel intentional, technical, calm, and memorable.

### Core visual character

-   Warm, pale mineral background for the main workspace.
-   Deep ink/navy for navigation and high-importance surfaces.
-   Signal orange for urgent actions and critical states.
-   Electric chartreuse for verified/success states and selected
    indicators.
-   Muted blue for informational data.
-   Fine grid lines, compact labels, deliberate spacing, and crisp
    typography.
-   Use glow as a rare status signal, not as decoration.

------------------------------------------------------------------------

## 2. Color system

Create CSS custom properties and use them consistently. Do not scatter
raw color values throughout components.

### Light workspace palette

  ------------------------------------------------------------------------
  Token                                        Value Use
  --------------------- ---------------------------- ---------------------
  `--bg-app`                               `#F1F0EA` Main application
                                                     background

  `--bg-panel`                             `#FBFAF6` Cards, drawers,
                                                     content panels

  `--bg-panel-muted`                       `#E8E7DF` Secondary surfaces,
                                                     filter backgrounds

  `--bg-sidebar`                           `#17212B` Sidebar and primary
                                                     navigation

  `--bg-elevated`                          `#FFFFFF` Menus, popovers,
                                                     modal surfaces

  `--text-primary`                         `#17212B` Main text

  `--text-secondary`                       `#66717A` Supporting text

  `--text-inverse`                         `#F8F7F1` Text on dark surfaces

  `--border-color`                         `#D8D8CE` Dividers and borders

  `--primary`                              `#E66A3D` Primary actions and
                                                     active emphasis

  `--primary-hover`                        `#C9542C` Primary hover state

  `--accent-verified`                      `#B5D83D` Verified state and
                                                     confirmation

  `--accent-info`                          `#5276B8` Informational state

  `--status-critical`                      `#D94C3D` Critical incidents

  `--status-high`                          `#E58A36` High severity

  `--status-medium`                        `#B89A3C` Medium severity

  `--status-low`                           `#648A79` Low severity
  ------------------------------------------------------------------------

### Dark surfaces

Use dark surfaces selectively for the sidebar, top-level command strip,
selected detail areas, and code/log panels. Do not turn every page into
a dark card grid.

Suggested dark tokens: - `--ink-950: #111820` - `--ink-900: #17212B` -
`--ink-800: #24313D` - `--ink-700: #344553` - `--ink-text: #F5F4ED` -
`--ink-muted: #A9B2B8`

### Theme compatibility

OpsRecall currently has theme options (`obsidian`, `emerald`, `synth`).
Inspect how these are implemented before changing them.

-   Preserve the theme switcher and all existing theme-selection
    behavior.
-   Apply the new design language consistently across all themes.
-   If keeping all three themes, make them coherent variants of the new
    design system rather than three unrelated palettes.
-   Do not remove a theme or silently change persisted user preferences.
-   Keep severity colors semantically consistent across themes.

------------------------------------------------------------------------

## 3. Typography and layout

### Typography

Use fonts already available in the project if they fit. Do not add a
font dependency without a clear reason.

-   Page title: strong, compact, editorial.
-   Section labels: small uppercase with modest letter spacing.
-   Metric values: large, tabular numerals.
-   Body copy: comfortable and highly readable.
-   IDs, timestamps, service names, and log output: monospace.

Avoid uppercase for long paragraphs. Keep labels short and meaningful.

### Shape and spacing

-   Use mostly 6--12px corner radii; reserve larger radii for major
    drawers or dialogs.
-   Prefer fine borders and subtle surface contrast over heavy shadows.
-   Use consistent spacing increments.
-   Keep dashboard data dense enough for engineers, but never cramped.
-   Preserve responsive behavior at existing breakpoints.

### Distinctive details

-   Add small numbered section markers or compact technical eyebrow
    labels where useful.
-   Use thin divider rules and restrained grid motifs.
-   Use a small orange "signal" marker for active/critical attention.
-   Keep incident IDs and timestamps visually scannable.

------------------------------------------------------------------------

## 4. Glow and animation language

Animations must communicate state or guide attention. They must not make
the application feel like a gaming UI.

### Allowed effects

1.  Active navigation: a short 150--220ms color transition and a thin
    orange indicator.
2.  Critical incident indicator: a very subtle, slow halo around the
    small status dot only. Do not pulse the entire card.
3.  Verified memory: a brief chartreuse confirmation shimmer when the
    verified state first appears; no continuous glow.
4.  Primary action: subtle hover lift (maximum 1--2px) and a restrained
    shadow transition.
5.  Charts: animate bars or line paths once on initial render, around
    350--550ms, with no looping.
6.  Memory drawer: smooth 180--240ms slide-in with a dimmed backdrop.
7.  Loading: use a restrained skeleton shimmer or small spinner. Avoid
    large animated loaders.

### Glow rules

-   Use soft, low-opacity glows only for active/critical/verified status
    indicators.
-   Keep glows localized and small.
-   Avoid neon outlines around every panel.
-   Do not use full-screen animated gradients.
-   Do not animate background color continuously.
-   Do not add particle effects, stars, or decorative noise that reduces
    readability.

### Accessibility

Include `@media (prefers-reduced-motion: reduce)` and disable
nonessential transitions, shimmer, and chart entrance animation for
users who request reduced motion.

------------------------------------------------------------------------

## 5. Apply the design across existing screens

Keep all existing screen structures and functionality. Restyle these
areas consistently:

### Main dashboard

-   Overview cards should look like compact instrument readouts, not
    generic floating tiles.
-   Use clear numeric hierarchy and restrained severity accents.
-   Charts should have clean axes, legible labels, and minimal grid
    lines.
-   Operational insight sections should feel like concise engineering
    notes.
-   Memory status should be prominent but not oversized.

### Incident list and incident details

-   Preserve current list behavior, filters, navigation, and actions.
-   Improve scanability of service, severity, status, and incident ID.
-   Use orange only for important attention states.
-   Keep long titles and log text readable.

### Incident Memory Explorer

-   Make the catalog feel like a searchable technical archive.
-   Use compact memory cards with a clear verified marker.
-   Make storage provider and bank ID visually distinct concepts.
-   Style the inspection drawer as a focused evidence panel.
-   Keep sanitized logs in a dark monospace surface.
-   Preserve pagination, filters, trust gate, citation counts, and the
    Recall & Reflect Lab.

### Forms and controls

-   Restyle buttons, inputs, selects, tabs, filter pills, badges, and
    toggles.
-   Provide clear hover, focus, active, disabled, and error states.
-   Ensure keyboard focus is visible.
-   Keep controls consistent across the application.

------------------------------------------------------------------------

## 6. Strict implementation constraints

**This is a visual-only change.**

Do not: - Change Python backend files. - Change API routes,
request/response schemas, database models, or SQL. - Change Retain,
Recall, or Reflect logic. - Change memory verification or citation
counting. - Change incident creation, resolution, or filtering
behavior. - Rename API functions or data fields. - Replace existing
pages or components. - Remove existing theme functionality. - Add mock
data. - Add a new UI framework, charting library, animation library, or
other dependency. - Modify deployment configuration. - Change
authentication, environment variables, or secrets handling.

You may: - Modify existing CSS files and theme token definitions. - Make
minimal JSX changes only when required to add presentational class names
or decorative, noninteractive wrappers. - Reuse existing icons and
components. - Add CSS keyframes and transitions that do not affect
application logic.

If a proposed visual change requires changing application behavior or
data flow, do not implement it. Report the limitation instead.

------------------------------------------------------------------------

## 7. Required workflow

### Before editing

1.  Inspect the current frontend structure, stylesheets, theme
    definitions, and existing components.
2.  Identify the current design tokens and all theme-switching logic.
3.  Identify any CSS that is shared with functional states.
4.  Provide a short file-by-file visual change plan.
5.  Confirm that no backend or business-logic changes are required.

### During implementation

1.  Introduce the new design tokens centrally.
2.  Restyle shared components first.
3.  Apply the design to the dashboard and Memory Explorer.
4.  Restyle remaining existing screens consistently.
5.  Add only restrained, purposeful animation.
6.  Test all three themes and responsive breakpoints.
7.  Verify focus visibility and reduced-motion behavior.

### After implementation

Run: - `npm --prefix frontend run build` - Existing backend tests, to
confirm no accidental backend changes. - A manual smoke test of
dashboard navigation, incident filters, memory catalog, memory detail
drawer, pagination, Recall, and Reflect.

### Final report

Return: - Files modified. - Screens/components visually updated. - Exact
palette and animation changes. - Confirmation that backend files and
business logic were untouched. - Frontend build result. - Backend test
result. - Any visual issues remaining.

**Stop after the visual refresh. Do not begin Part 3 until the user
reviews and approves the new design.**

------------------------------------------------------------------------

## 8. Design acceptance checklist

-   [ ] OpsRecall no longer looks like a generic purple/blue AI
    dashboard template.
-   [ ] Warm mineral workspace + deep ink navigation + signal
    orange/chartreuse accents are applied consistently.
-   [ ] Existing `obsidian`, `emerald`, and `synth` theme options still
    work.
-   [ ] No feature, route, API, data model, or business logic was
    changed.
-   [ ] Glow is localized and meaningful, not applied to every card.
-   [ ] Animations are restrained and respect reduced-motion
    preferences.
-   [ ] Dashboard and Memory Explorer remain responsive.
-   [ ] Text, charts, badges, and controls remain readable.
-   [ ] Frontend production build passes.
-   [ ] User has reviewed the visual refresh before Part 3 begins.

**Priority:** A distinctive, polished, readable engineering product ---
not visual effects for their own sake.
