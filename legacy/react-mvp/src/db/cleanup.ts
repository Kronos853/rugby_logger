import { countMatchesByTeam, countMatchesByTemplate } from './repository';
import { run, withWriteVoid } from './sqlite';

export async function deleteCommentTemplate(commentId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM CommentTemplate WHERE Id = ?', [commentId]);
  });
}

export async function deleteAction(actionId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM Action WHERE Id = ?', [actionId]);
  });
}

export async function deleteCategory(categoryId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM Category WHERE Id = ?', [categoryId]);
  });
}

export async function deleteSportTemplate(templateId: number): Promise<void> {
  const matchCount = await countMatchesByTemplate(templateId);
  if (matchCount > 0) {
    throw new Error(`Шаблон используется в ${matchCount} матч(ах). Сначала удалите матчи.`);
  }
  return withWriteVoid(() => {
    run('DELETE FROM SportTemplate WHERE Id = ?', [templateId]);
  });
}

export async function deleteSquad(squadId: number): Promise<void> {
  return withWriteVoid(() => {
    run('UPDATE Match SET HomeSquadId = NULL WHERE HomeSquadId = ?', [squadId]);
    run('UPDATE Match SET AwaySquadId = NULL WHERE AwaySquadId = ?', [squadId]);
    run('DELETE FROM Squad WHERE Id = ?', [squadId]);
  });
}

export async function deleteMatch(matchId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM Match WHERE Id = ?', [matchId]);
  });
}

export async function deletePlayer(playerId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM Player WHERE Id = ?', [playerId]);
  });
}

export async function deleteTeam(teamId: number): Promise<void> {
  const matchCount = await countMatchesByTeam(teamId);
  if (matchCount > 0) {
    throw new Error(`Команда используется в ${matchCount} матч(ах). Сначала удалите матчи.`);
  }
  return withWriteVoid(() => {
    run('DELETE FROM Team WHERE Id = ?', [teamId]);
  });
}
