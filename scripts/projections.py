import code

from datetime import date, timedelta

import pandas

# Fresno County population
population = 1042157

today = date.today()
reopen = date(2021, 6, 15)

days_to_reopen = (reopen - today).days

# Fetch states data
def fetch_data():
    url = 'https://data.chhs.ca.gov/dataset/e283ee5a-cf18-4f20-a92c-ee94a2866ccd/resource/130d7ba2-b6eb-438d-a412-741bde207e1c/download/covid19vaccinesbycounty.csv'
    df = pandas.read_csv(url)
    df = df[df['county'] == 'Fresno']
    return df

def get_seven_day_average_increase(df):
    absolute_average = df.iloc[len(df) - 7:]['cumulative_fully_vaccinated'].diff().mean()
    percent_average = (100. / population) * absolute_average
    return {
        'absolute': absolute_average,
        'percent': percent_average,
    }

def get_current_percentage(df):
    vaccinated = int(df.iloc[-1]['cumulative_fully_vaccinated'])
    return (100. / population) * vaccinated

def estimated_percentage(goal, current, average):
    return today + timedelta(days=round((goal - current) / average))

df = fetch_data()
increase = get_seven_day_average_increase(df)
current_percentage = get_current_percentage(df)
projected_percentage = current_percentage + (days_to_reopen * increase['percent'])

print('')
print(f'Current percentage: {current_percentage:.1f}%')
print(f'7-day average increase: {int(increase["absolute"])} ({increase["percent"]:.1f}%)')
print(f'Days until June 15th: {days_to_reopen}')
print(f'Estimated percentage on June 15th: {projected_percentage:.1f}%')
print(f'Projected dates by percentage:')

for x in (25, 50, 65, 80):
    if x < current_percentage:
        continue
    projection_date = estimated_percentage(x, current_percentage, increase["percent"])
    days_away = (projection_date - today).days
    print(f'\t{x}%: {projection_date} ({days_away} days)')

# code.interact(local=locals())
