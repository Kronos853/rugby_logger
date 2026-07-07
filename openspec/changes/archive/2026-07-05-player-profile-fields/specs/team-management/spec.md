## MODIFIED Requirements

### Requirement: Manage Players
The system SHALL allow users to add players to a team, optionally specifying their position.

The Player entity SHALL include:
- **Name** — short display name used in tagging UI
- **FullName** — optional full legal name
- **BirthDay** — optional date of birth
- **DefaultPosition** — optional default position in team roster

#### Scenario: Adding a player to a team
- **WHEN** the user adds a player with a name and position to a team
- **THEN** the player is associated with that team

## ADDED Requirements

### Requirement: Edit Player Profile
The system SHALL provide a dedicated page to edit a player's profile fields (Name, FullName, BirthDay, DefaultPosition).

#### Scenario: Updating player profile
- **WHEN** the user opens the player edit page and saves changes
- **THEN** the updated profile is persisted and shown in the team roster
