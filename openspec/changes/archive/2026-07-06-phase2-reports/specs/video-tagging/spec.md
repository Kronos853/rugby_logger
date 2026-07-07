## ADDED Requirements

### Requirement: Main Navigation on Tagging Control Panel
The system SHALL display the main navigation bar on the tagging control panel page, consistent with all other pages.

#### Scenario: Navigation bar visible on tagging page
- **WHEN** the user opens the tagging control panel (`/tagging/<match_id>/control`)
- **THEN** the main navigation bar is visible at the top of the page, providing links to other sections (Home, Directories, Matches, Reports, Admin)

#### Scenario: Layout not broken by navigation bar
- **WHEN** the navigation bar is added to the tagging control panel
- **THEN** the fixed-height viewport layout remains intact — the tagging toolbar and split-pane content area still fill the remaining screen height without causing page-level scroll

#### Scenario: Navigation accessible without leaving match
- **WHEN** the user clicks a navigation link on the tagging control panel
- **THEN** they are taken to the corresponding page (standard browser navigation)
