## ADDED Requirements

### Requirement: Manage Teams
The system SHALL allow users to create and manage teams in a global directory.

#### Scenario: Creating a team
- **WHEN** the user creates a team with a name
- **THEN** the team is saved in the directory and can be used in matches

### Requirement: Manage Players
The system SHALL allow users to add players to a team, optionally specifying their position.

#### Scenario: Adding a player to a team
- **WHEN** the user adds a player with a name and position to a team
- **THEN** the player is associated with that team

### Requirement: Create Matches
The system SHALL allow users to create a match by specifying metadata (date, tournament, score, periods) and selecting two teams from the directory.

#### Scenario: Setting up a match
- **WHEN** the user creates a match and selects a Home Team and an Away Team
- **THEN** the match is initialized with those teams

### Requirement: Manage Saved Squads
The system SHALL allow users to create and save named squads (lineups) for a team, consisting of players and their positions, optionally linked to a tournament.

#### Scenario: Creating a squad for a tournament
- **WHEN** the user creates a squad for a team and adds players with positions
- **THEN** the squad is saved and can be reused for multiple matches

#### Scenario: Marking starters and substitutes in a squad
- **WHEN** the user adds a player to a saved squad
- **THEN** they can mark the player as a starter or a substitute

### Requirement: Assign Squad to Match
The system SHALL allow users to assign a saved squad to a match for each team side, copying the squad into a match lineup snapshot.

#### Scenario: Selecting a squad for a match
- **WHEN** the user sets up a match and selects a saved squad for the home team
- **THEN** the system copies all squad players and positions into the match lineup
- **AND** only those players are available for event logging during that match

#### Scenario: Adjusting lineup roles for a specific match
- **WHEN** the user edits the match lineup after copying from a squad
- **THEN** they can change a player's starter/substitute flag for that match only
- **AND** the saved squad remains unchanged

#### Scenario: Squad changes do not affect past matches
- **WHEN** the user edits a saved squad after a match was logged
- **THEN** the match lineup snapshot for that past match remains unchanged

### Requirement: Edit Saved Squad Metadata
The system SHALL allow users to change a saved squad's name and tournament when editing the squad.

#### Scenario: Renaming a squad
- **WHEN** the user edits the squad name or tournament and saves
- **THEN** the updated metadata is persisted and shown in the squads list
