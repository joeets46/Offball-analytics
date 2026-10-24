export type View =
  | 'home'
  | 'dashboard'
  | 'player'
  | 'team'
  | 'match'
  | 'recruitment'
  | 'ai'

export const players = [
  { name: 'Maya Okafor', role: 'data.interior', team: 'Northbridge FC', rating: 92, space: 88, press: 94, minutes: 1284, status: 'data.shortlist', color: '#ef7f5c' },
  { name: 'Elena Varga', role: 'data.leftEight', team: 'Riverside United', rating: 87, space: 91, press: 78, minutes: 1098, status: 'data.monitor', color: '#7868d8' },
  { name: 'Sofia Marin', role: 'data.creator', team: 'Crown Athletic', rating: 84, space: 86, press: 73, minutes: 964, status: 'data.shortlist', color: '#4b9d8a' },
  { name: 'Amara Diallo', role: 'data.wideEight', team: 'Eastport City', rating: 81, space: 79, press: 89, minutes: 1162, status: 'data.watch', color: '#d8a23f' },
]

export type Player = (typeof players)[number]

export const weeklyTrend = [58, 63, 61, 72, 69, 78, 75, 84, 82, 89, 86, 93]
export const spaceByPhase = [
  { label: 'data.buildUp', value: 78, color: '#ef7f5c' },
  { label: 'data.progression', value: 68, color: '#d8a23f' },
  { label: 'data.finalThird', value: 84, color: '#4b9d8a' },
  { label: 'data.transition', value: 61, color: '#7868d8' },
]

export const matchMoments = [
  { time: '08:42', title: 'match.pressingSequence', detail: 'match.pressingDetail', type: 'press' },
  { time: '17:19', title: 'match.spaceCreated', detail: 'match.spaceDetail', type: 'space' },
  { time: '31:06', title: 'match.possessionShift', detail: 'match.possessionDetail', type: 'possession' },
  { time: '64:44', title: 'match.opportunityMissed', detail: 'match.opportunityDetail', type: 'alert' },
]

export const kpis = [
  { label: 'kpi.teamRating', value: '84.6', delta: '+6.8%', note: 'kpi.previousPeriod', tone: 'orange' },
  { label: 'kpi.spaceConversion', value: '68.4%', delta: '+4.2%', note: 'kpi.observedOpportunities', tone: 'green' },
  { label: 'kpi.pressRecovery', value: '41.8%', delta: '+8.1%', note: 'kpi.pressingOpportunities', tone: 'purple' },
  { label: 'kpi.dataCoverage', value: '91.2%', delta: 'common.good', note: 'kpi.trackingEvidence', tone: 'blue' },
]
