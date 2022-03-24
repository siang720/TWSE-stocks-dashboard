import pandas as pd
import random
import requests

import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Group

percentage_format = FormatTemplate.percentage(2)
group_format = Format().group(True)

base_urls = [
    'https://justdata.moneydj.com/', # MoneyDJ
    'http://jdata.yuanta.com.tw/',  # 元大
    'https://fubon-ebrokerdj.fbs.com.tw/', # 富邦
    'http://moneydj.emega.com.tw/', # 兆豐
    'http://newjust.masterlink.com.tw/' # 元富
]

def get_stock_list():
    
    tse_url = 'https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv'
    otc_url = 'http://mopsfin.twse.com.tw/opendata/t187ap03_O.csv'
    
    tse_df = pd.read_csv(tse_url, usecols=['公司代號', '英文簡稱'])
    otc_df = pd.read_csv(otc_url, usecols=['公司代號', '英文簡稱'])
    
    options = []

    for index, row in tse_df.iterrows():
        options.append({
                'label': f"{row['公司代號']} - {row['英文簡稱']}",
                'value': f"{row['公司代號']}.TW"
        })
        
    for index, row in otc_df.iterrows():
        options.append({
                'label': f"{row['公司代號']} - {row['英文簡稱']}",
                'value': f"{row['公司代號']}.TWO"
        })
        
    return options


def get_column_dict(column, dtype):
    
    if 'Change' in column or 'Percentage' in column or 'Profit' in column or 'Margin' in column:
        return {"name": column, "id": column, "type": 'numeric', "format": percentage_format}
    
    elif pd.api.types.is_numeric_dtype(dtype):
        return {"name": column, "id": column, "type": 'numeric', "format": group_format}
    
    else:
        return {"name": column, "id": column}
    
def get_shareholder_structure(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcj/zcj_{symbol}.djhtm'
    dfs = pd.read_html(url)
    df = dfs[3]
    
    df = df.iloc[2:-1, [0, 1, 3]]
    df.columns = ['Shareholders', 'Shares Owned', 'Percentage']

    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df['Percentage'] = df['Percentage'] / 100
    others_percentage = round(1 - df['Percentage'].sum(), 4)
    others = int(df['Shares Owned'].sum() / df['Percentage'].sum() * others_percentage)
    
    new_row = pd.DataFrame([['Others', others, others_percentage]], columns=['Shareholders', 'Shares Owned', 'Percentage'])

    df = pd.concat([df, new_row], ignore_index=True)
    
    # transfer shareholders type to English
    for index, rows in df.iterrows():
        if rows[0] == '董監持股':
            df.iloc[index, 0] = 'Directors'
        elif rows[0] == '外資持股':
            df.iloc[index, 0] = 'Foreign Investors'
        elif rows[0] == '投信持股':
            df.iloc[index, 0] = 'Investment Trusts'
        elif rows[0] == '自營商持股':
            df.iloc[index, 0] = 'Dealers'
        elif rows[0] == '融資餘額':
            df.iloc[index, 0] = 'Margin Debt'
        elif rows[0] == '融券餘額':
            df.iloc[index, 0] = 'Short Balance'
    
    fig = px.pie(
            df, 
            values=df.columns[1], 
            names=df.columns[0], 
            title=f'{symbol} Shareholder Structure',
            color_discrete_sequence=px.colors.sequential.Tealgrn
          )
    fig.update_traces(textinfo='label+percent')
    fig.update_layout(
        title_x=0.4,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
    )
    
    return df, fig


def get_dividends(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcc/zcc_{symbol}.djhtm'
    
    html = requests.get(url).text   
    html = html.replace('<td class="t3n0">', '<tr><td class="t3n0">')
    
    dfs = pd.read_html(html)
    df = dfs[2]
    
    df = df.iloc[4:, [0, 3, 4, 5, 7]]
    df.columns = ['Year', 'Cash Dividend' , 'Stock Dividend from Retained Earnings', 'Stock Dividend from Capital Reserve', 'Total']
    df = df[~df['Year'].str.contains('Q')]
    
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df.Year = df.Year.astype('str')
    df = df.round(4)
    
    fig_df = df.iloc[:12][::-1]
    fig = px.bar(fig_df, x=df.columns[0], y=df.columns[4], text=df.columns[4])
    fig.update_layout(
        title=f'{symbol} Dividends (Yearly)',
        title_x=0,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
        xaxis_title='Year',
        yaxis_title='Dollars',
        template='plotly_white'
    )

    return df, fig


def get_inst_investors(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcl/zcl.djhtm?a={symbol}&b=3'
    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[7:-1, :5]
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df.columns = ['Date', 'Foreign Investors', 'Investment Trusts', 'Dealers', 'Total']
    df['Date'] = df['Date'].transform(lambda x: str(int(x[0:3]) + 1911) + x[3:])

    fig_df = df.iloc[::-1]
    
    fig = px.bar(fig_df, x=fig_df.columns[0], y=[fig_df.columns[1], fig_df.columns[2], fig_df.columns[3]])
    
    fig.update_layout(
        title=f'{symbol} Institutional Investors',
        title_x=0,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
        xaxis_title='Date',
        yaxis_title='Shares(thousands)',
        template='plotly_white',
        hovermode='x unified'
    )
    
    return df, fig


def get_cashflow(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zc3/zc3_{symbol}.djhtm'
    
    r = requests.get(url)
    html = r.text.replace('div class="table-caption', 'tr class="table-caption')
    html = html.replace('div class="table-row', 'tr class="table-row')
    html = html.replace('span class="table-cell', 'td class="table-cell')

    dfs = pd.read_html(html)
    df = dfs[1]
    
    df.set_index(0, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    
    data = {
        'Quarter': df.loc['期別'],
        'Net CF': df.loc['本期產生現金流量'].apply(pd.to_numeric),
        'Operating CF': df.loc['來自營運之現金流量'].apply(pd.to_numeric),
        'Investing CF': df.loc['投資活動之現金流量'].apply(pd.to_numeric),
        'Financing CF': df.loc['籌資活動之現金流量'].apply(pd.to_numeric)
    }
    
    df = pd.DataFrame(data)
    
    fig_df = df.iloc[::-1]
    
    fig = px.scatter(
            fig_df, 
            x=fig_df.columns[0], 
            y=[
                fig_df.columns[1],
                fig_df.columns[2], 
                fig_df.columns[3], 
                fig_df.columns[4]
            ]
          )
    fig.update_traces(mode='markers+lines')

    fig.update_layout(
        title=f'{symbol} Cash Flow',
        title_x=0,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
        xaxis_title='Quarter',
        yaxis_title='Million Dollars',
        template='plotly_white'
    )
    return df, fig


def get_monthly_revenue(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zch/zch_{symbol}.djhtm'
    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[6:, :3]
    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    
    df = df.apply(pd.to_numeric, errors='ignore')
    df[2] = df[2] / 100
    
    df.columns = ['Month', 'Revenue', 'MoM Change']
    df['Month'] = df['Month'].transform(lambda x: str(int(x[0:3]) + 1911) + x[3:])
    
    fig_df = df.iloc[:12][::-1]
    
    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(x=fig_df['Month'], y=fig_df['Revenue'], name='Revenue'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=fig_df['Month'], y=fig_df['MoM Change'], name='MoM Change'),
        secondary_y=True
    )

    fig.update_layout(
        title_text=f'{symbol} Monthly Revenue',
        title_x=0,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
        xaxis_title='Month',
        template='plotly_white',
        hovermode='x unified',
        yaxis1_title='Revenue',
        yaxis2_title='MoM Change',
        yaxis2_tickformat='p',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return df, fig


def get_profitability(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zce/zce_{symbol}.djhtm'

    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[3:, [0, 1, 4, 6, 8, 9, 10]]
    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df[8] = (df[8] / df[1]).round(4)
    df[9] = (df[9] / df[1]).round(4)
    del df[1]
    
    df[4] = df[4] / 100
    df[6] = df[6] / 100
    
    df.columns = ['Quarter', 'Gross Profit' , 'Operating Margin', 'Pre-Tax Income Margin' ,'Net Margin', 'EPS(dollars)']
    df['Quarter'] = df['Quarter'].transform(lambda x: str(int(x[0:-3]) + 1911) + x[-3:])
    
    fig_df = df.iloc[:12][::-1]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=fig_df['Quarter'], y=fig_df[fig_df.columns[5]], name=fig_df.columns[5]),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=fig_df['Quarter'], y=fig_df[fig_df.columns[1]], name=fig_df.columns[1]),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(x=fig_df['Quarter'], y=fig_df[fig_df.columns[2]], name=fig_df.columns[2]),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(x=fig_df['Quarter'], y=fig_df[fig_df.columns[3]], name=fig_df.columns[3]),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(x=fig_df['Quarter'], y=fig_df[fig_df.columns[4]], name=fig_df.columns[4]),
        secondary_y=True
    )

    fig.update_layout(
        title_text=f'{symbol} Profitablity',
        title_x=0,
        title_xanchor="left",
        title_y=0.9,
        title_yanchor="top",
        xaxis_title='Quarter',
        template='plotly_white',
        hovermode='x unified',
        yaxis1_title='EPS(dollars)',
        yaxis2_title='Margin',
        yaxis2_tickformat='p',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return df, fig