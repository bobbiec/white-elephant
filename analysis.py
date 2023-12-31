import plotly.express as px
import pandas as pd

def rank(n, suffix=None):
    df = pd.read_csv(f'results-{n}{"-" + suffix if suffix else ""}.csv')

    num_trials = len(df)

    fig = px.histogram(
        df,
        x='rank',
    )
    total_options = df['total_options'][0]
    total_options_percent = total_options // 100
    fig.update_yaxes(range = [0, 7500])
    fig.update_xaxes(range = [total_options, 1])
    fig.update_traces(xbins_size=total_options_percent)
    fig.update_layout(
        title=f'Rank distribution for {n} players (over {num_trials} simulated games)',
        xaxis_title='worst <-- Rank percentile --> best',
        yaxis_title='Number of simulated games'
    )

    fontsize = 18

    if total_options_percent <= 1:
        top_bucket_count = len(df.loc[df['rank'] == 1])
    else:
        top_bucket_count = len(df.loc[df['rank'] < total_options_percent])
    top_bucket_percentage = f"{top_bucket_count/num_trials*100:2.0f}"
    fig.add_annotation(
        x=1,
        y=top_bucket_count,
        text=f"{top_bucket_percentage}% of simulated games produce a result<br>in the top 1% of possible outcomes.",
        showarrow=True,
        arrowhead=1,
        xanchor='right',
        font=dict(
            size=fontsize,
        ),
        axref="x",
        ayref="y",
        ax=total_options_percent * 5,
        ay=5000,
    )

    worst_rank = max(df['rank'])
    fig.add_annotation(
        x=worst_rank,
        y=1,
        text="The absolute worst simulated outcome is here.",
        showarrow=True,
        arrowhead=1,
        font=dict(
            size=fontsize,
        ),
        ax=-80,
        ay=-150,
    )

    p99 = df['rank'].quantile(q=0.99, interpolation='nearest')
    p99_percentage = f"{p99/total_options*100:2.0f}"
    fig.add_annotation(
        x=p99,
        y=1,
        text=f"99% of simulated games produce a result<br>in the top {p99_percentage}% of possible outcomes.",
        showarrow=True,
        arrowhead=1,
        font=dict(
            size=fontsize,
        ),
        ax=-80,
        ay=-150,
    )

    fig.write_html(f'rank-{n}{"-" + suffix if suffix else ""}.html', include_plotlyjs='cdn')
    # fig.show()

if __name__ == '__main__':
    for i in range(2, 10):
        rank(i)
        rank(i, suffix='laststeal')
