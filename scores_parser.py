import json
import pandas as pd
import argparse


def extract_match_data(item):
    start_date = item.get('startDate', '')
    tournament = item.get('uqTournament', {}).get('nameZh', '')
    home_team = item.get('hometeamName', '') or item.get('hometeamNameZh', '')
    away_team = item.get('awayteamName', '') or item.get('awayteamNameZh', '')

    # 即时比分优先取 current，若无则取 ft（完场）
    score_obj = item.get('score', {})
    score_str = score_obj.get('current', '') or score_obj.get('ft', '')

    total_goals = None
    goal_diff = None
    if score_str and ':' in score_str:
        parts = score_str.split(':')
        if len(parts) == 2:
            try:
                h = int(parts[0])
                a = int(parts[1])
                total_goals = h + a
                goal_diff = h - a
            except ValueError:
                pass

    return {
        'startDate': start_date,
        'tournament': tournament,
        'homeTeam': home_team,
        'awayTeam': away_team,
        'score': score_str,
        'totalGoals': total_goals,
        'goalDiff': goal_diff
    }


def deduplicate_and_sort(df):
    """单次提取内可能重复（极少），按组合键去重并排序"""
    if df.empty:
        return df
    df['_dup_key'] = df['startDate'] + '|' + df['tournament'] + '|' + df['homeTeam'] + '|' + df['awayTeam']
    df.drop_duplicates(subset=['_dup_key'], keep='last', inplace=True)
    df.drop(columns=['_dup_key'], inplace=True)

    df['startDate'] = df['startDate'].fillna('')
    df.sort_values('startDate', inplace=True)
    return df


def main():
    parser = argparse.ArgumentParser(description='解析即时比分 scores.json，覆盖保存')
    parser.add_argument('--input', required=True, help='scores.json 文件路径')
    parser.add_argument('--output', default='scores_now.csv', help='输出 CSV 路径（默认 scores_now.csv）')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('data', {}).get('list', [])
    records = [extract_match_data(item) for item in items if item.get('startDate')]
    df = pd.DataFrame(records)

    df_result = deduplicate_and_sort(df)

    df_result.to_csv(args.output, index=False, encoding='utf-8-sig')
    print(f"✅ 已保存 {len(df_result)} 条记录至 {args.output}")


if __name__ == '__main__':
    main()