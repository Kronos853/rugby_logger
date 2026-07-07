import type { MatchScore } from '../lib/match-score';

export function MatchScoreDisplay({
  homeName,
  awayName,
  score,
  compact = false,
}: {
  homeName: string;
  awayName: string;
  score: MatchScore;
  compact?: boolean;
}) {
  return (
    <div className={`match-score${compact ? ' match-score--compact' : ''}`}>
      <span className="match-score__team">{homeName}</span>
      <span className="match-score__values">
        {score.home} : {score.away}
      </span>
      <span className="match-score__team">{awayName}</span>
    </div>
  );
}
