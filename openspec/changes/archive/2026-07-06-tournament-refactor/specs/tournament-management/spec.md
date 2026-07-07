## ADDED Requirements

### Requirement: Tournament Reference Table
The system SHALL maintain a global `Tournament` reference table storing unique tournament names.

#### Scenario: Tournament has a unique name
- **WHEN** a user attempts to create a tournament with a name that already exists
- **THEN** the existing tournament record is reused (no duplicate created)

### Requirement: Inline Tournament Creation from Match Form
The system SHALL allow users to associate a tournament with a match by selecting an existing name or typing a new one.

#### Scenario: Existing tournament shown in match form
- **WHEN** the user opens the match creation or match setup form
- **THEN** an autocomplete input (datalist) shows all existing tournament names

#### Scenario: Creating new tournament inline in match form
- **WHEN** the user types a new tournament name not present in the list and saves the match
- **THEN** the tournament is automatically created and linked to the match

#### Scenario: No tournament selected
- **WHEN** the user leaves the tournament field empty when creating or editing a match
- **THEN** the match is saved with no tournament association

### Requirement: Inline Tournament Creation from Squad Form
The system SHALL allow users to associate a tournament with a saved squad using the same inline creation behavior.

#### Scenario: Tournament autocomplete on squad form
- **WHEN** the user creates or edits a squad
- **THEN** an autocomplete input shows all existing tournament names

#### Scenario: New tournament from squad form
- **WHEN** the user types a new tournament name on the squad form and saves
- **THEN** the tournament is created and linked to the squad

### Requirement: Tournament Displayed in Match List and Squad List
The system SHALL display the tournament name wherever it was previously shown as a free-text string.

#### Scenario: Tournament name in match list
- **WHEN** the user views the matches list
- **THEN** the tournament column shows the linked tournament name, or "—" if not set

#### Scenario: Tournament name in squad list
- **WHEN** the user views the squads list
- **THEN** the tournament column shows the linked tournament name, or "—" if not set
