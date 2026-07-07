import {
  countSportTemplates,
  createAction,
  createCategory,
  addMatchLineupRow,
  deleteMatchLineupForTeam,
  getSportTemplateByName,
  createSportTemplate,
  getSquad,
  listSquadPlayers,
  updateMatchSquadRefs,
} from './repository';

type SeedAction = {
  name: string;
  hasOutcome?: boolean;
  colorClass: string;
};

type SeedCategory = {
  name: string;
  actions: SeedAction[];
};

const RUGBY_CATEGORIES: SeedCategory[] = [
  {
    name: 'Handling',
    actions: [
      { name: 'Pass (success)', colorClass: 'handling' },
      { name: 'Pass (missed)', colorClass: 'handling' },
      { name: 'Catch (success)', colorClass: 'handling' },
      { name: 'Catch (failure)', colorClass: 'handling' },
      { name: 'Knock-on', colorClass: 'handling' },
      { name: 'Forward pass', colorClass: 'handling' },
    ],
  },
  {
    name: 'Offence',
    actions: [
      { name: 'Carry', colorClass: 'offence' },
      { name: 'Linebreak', colorClass: 'offence' },
      { name: 'try', colorClass: 'offence' },
    ],
  },
  {
    name: 'Tackle',
    actions: [
      { name: 'Tackle (success)', colorClass: 'tackle' },
      { name: 'Missed tackle', colorClass: 'tackle' },
    ],
  },
  {
    name: 'Kicking',
    actions: [
      { name: 'Kick (tactical)', colorClass: 'kicking' },
      { name: 'Kick (attacking)', colorClass: 'kicking' },
      { name: 'conversion', colorClass: 'kicking' },
      { name: 'Conversion (opp)', colorClass: 'kicking' },
    ],
  },
  {
    name: 'Set-piece',
    actions: [
      { name: 'Ruck', colorClass: 'setpiece' },
      { name: 'Lineout (own)', colorClass: 'setpiece' },
      { name: 'Lineout (opp)', colorClass: 'setpiece' },
      { name: 'Scrum (own)', colorClass: 'setpiece' },
      { name: 'Scrum (opp)', colorClass: 'setpiece' },
    ],
  },
  {
    name: 'Defence',
    actions: [
      { name: 'Turnover', colorClass: 'defence' },
      { name: 'Try conceded', colorClass: 'defence' },
    ],
  },
  {
    name: 'Discipline',
    actions: [
      { name: 'penalty (offside)', colorClass: 'discipline' },
      { name: 'penalty (high tackle)', colorClass: 'discipline' },
      { name: 'penalty (ruck)', colorClass: 'discipline' },
      { name: 'penalty (other)', colorClass: 'discipline' },
      { name: 'Penalty (opponent)', colorClass: 'discipline' },
      { name: 'yellow card', colorClass: 'discipline' },
      { name: 'red card', colorClass: 'discipline' },
    ],
  },
  {
    name: 'Substitute',
    actions: [
      { name: 'On', colorClass: 'substitute', hasOutcome: false },
      { name: 'Off', colorClass: 'substitute', hasOutcome: false },
    ],
  },
];

export async function seedRugbyTemplate(): Promise<number> {
  const existing = await getSportTemplateByName('Регби-7');
  if (existing?.id) return existing.id;

  const templateId = await createSportTemplate('Регби-7');

  let categoryOrder = 0;
  for (const cat of RUGBY_CATEGORIES) {
    const categoryId = await createCategory(templateId, cat.name, categoryOrder++);

    let actionOrder = 0;
    for (const act of cat.actions) {
      await createAction(
        categoryId,
        act.name,
        act.hasOutcome ?? true,
        actionOrder++,
        act.colorClass,
      );
    }
  }

  return templateId;
}

export async function ensureSeeded(): Promise<void> {
  const count = await countSportTemplates();
  if (count === 0) {
    await seedRugbyTemplate();
  }
}

export async function copySquadToMatchLineup(
  matchId: number,
  squadId: number,
  side: 'home' | 'away',
): Promise<void> {
  const squad = await getSquad(squadId);
  if (!squad?.id) return;

  await deleteMatchLineupForTeam(matchId, squad.teamId);
  const squadPlayers = await listSquadPlayers(squadId);

  for (const sp of squadPlayers) {
    await addMatchLineupRow({
      matchId,
      teamId: squad.teamId,
      playerId: sp.playerId,
      position: sp.position,
      lineupRole: sp.lineupRole,
      sortOrder: sp.sortOrder,
    });
  }

  await updateMatchSquadRefs(matchId, {
    [side === 'home' ? 'homeSquadId' : 'awaySquadId']: squadId,
  });
}
