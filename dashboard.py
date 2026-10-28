from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

PASTA = Path(__file__).resolve().parent
HISTORICO = PASTA / 'historico_cartola.csv'
TIMES = PASTA / 'times_cartola.csv'
CSS = PASTA / 'style.css'
CORES = ['#20C761', '#FF5A1F', '#FFD92F', '#2878D0', '#9B59B6', '#E8436D']

st.set_page_config(page_title='Cartola 2026 | Liga Galera TI', page_icon='⚽', layout='wide')

@st.cache_data
def carregar_dados():
    hist = pd.read_csv(HISTORICO, encoding='utf-8-sig')
    times = pd.read_csv(TIMES, encoding='utf-8-sig')
    hist.columns = hist.columns.str.strip()
    times.columns = times.columns.str.strip()
    for c in ['rodada', 'pontos_rodada', 'patrimonio']:
        hist[c] = pd.to_numeric(hist[c], errors='coerce')
    hist['time_id'] = hist['time_id'].astype(str)
    times['time_id'] = times['time_id'].astype(str)
    return hist, times

if not HISTORICO.exists() or not TIMES.exists():
    st.error('Coloque historico_cartola.csv e times_cartola.csv na mesma pasta do dashboard.py.')
    st.stop()
try:
    df_original, times_df = carregar_dados()
except Exception as e:
    st.error(f'Erro ao ler os CSVs: {e}')
    st.stop()

obrigatorias = {'rodada', 'time_id', 'nome_time', 'cartoleiro', 'pontos_rodada', 'patrimonio'}
if not obrigatorias.issubset(df_original.columns):
    st.error('O historico_cartola.csv não contém todas as colunas esperadas.')
    st.stop()

st.sidebar.markdown('''<div class="sidebar-brand"><div class="sidebar-brand-icon">⚽</div><div><div class="sidebar-brand-title">CARTOLA 2026</div><div class="sidebar-brand-subtitle">LIGA GALERA TI</div></div></div>''', unsafe_allow_html=True)

TEMAS = {
    "Cartola Original": {
        "page": "#17191D", "panel": "#22252A", "sidebar": "#202328",
        "text": "#FFFFFF", "muted": "#C4C8CC", "border": "#3A3F45",
        "green": "#20C761", "orange": "#FF5A1F", "gold": "#FFE000",
        "hero": "#292D32", "metric": "#292D32", "metric_text": "#20C761",
    },
    "Campo Verde": {
        "page": "#142019", "panel": "#1D2B22", "sidebar": "#19271E",
        "text": "#F7FFF8", "muted": "#C0D2C4", "border": "#385442",
        "green": "#39E875", "orange": "#FF9F43", "gold": "#FFD166",
        "hero": "#203528", "metric": "#223329", "metric_text": "#39E875",
    },
}


tema_nome = st.sidebar.selectbox(
    "🎨 Tema visual",
    options=list(TEMAS.keys()),
    index=0,
    key="tema_visual",
)

tema = TEMAS[tema_nome]

# 1. Carrega primeiro o CSS base
if CSS.exists():
    css_text = CSS.read_text(encoding="utf-8")
    st.markdown(
        f"<style>\n{css_text}\n</style>",
        unsafe_allow_html=True,
    )

# 2. Aplica o tema selecionado depois do CSS base
st.markdown(
    f"""
    <style>
    :root {{
        --page-bg: {tema['page']};
        --panel-bg: {tema['panel']};
        --sidebar-bg: {tema['sidebar']};
        --green: {tema['green']};
        --orange: {tema['orange']};
        --gold: {tema['gold']};
        --text: {tema['text']};
        --muted: {tema['muted']};
        --border: {tema['border']};
        --hero-bg: {tema['hero']};
        --metric-bg: {tema['metric']};
        --metric-text: {tema['metric_text']};
        --input-bg: {tema['hero']};
        --table-bg: {tema['page']};
    }}

    .stApp {{
        background: var(--page-bg) !important;
        color: var(--text) !important;
    }}

    [data-testid="stHeader"] {{
        background: var(--page-bg) !important;
    }}

    [data-testid="stSidebar"] {{
        background: var(--sidebar-bg) !important;
        border-right-color: var(--border) !important;
    }}

    .hero {{
        background: var(--hero-bg) !important;
        border-color: var(--border) !important;
        border-left-color: var(--orange) !important;
    }}

    .hero-title,
    h1, h2, h3 {{
        color: var(--text) !important;
    }}

    .hero-eyebrow,
    .section-kicker {{
        color: var(--orange) !important;
    }}

    .hero-league,
    .team-points {{
        color: var(--green) !important;
    }}

    .hero-subtitle,
    .team-manager,
    .team-extra {{
        color: var(--muted) !important;
    }}

    .team-card,
    .team-card-large,
    [data-testid="stMetric"],
    [data-testid="stExpander"] {{
        background: var(--panel-bg) !important;
        border-color: var(--border) !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--metric-bg) !important;
    }}

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: var(--metric-text) !important;
    }}

    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--orange) !important;
        border-bottom-color: var(--orange) !important;
    }}

    div.stButton > button,
    div.stDownloadButton > button {{
        background: var(--green) !important;
        border-color: var(--green) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.caption(f"Tema ativo: {tema_nome}")

st.sidebar.markdown('### Filtros da competição')
turnos = {'1º turno · Rodadas 19–24': (19, 24), '2º turno · Rodadas 25–38': (25, 38)}
turno = st.sidebar.selectbox('Turno', list(turnos), index=1)
inicio_turno, fim_turno = turnos[turno]
df_turno = df_original[df_original['rodada'].between(inicio_turno, fim_turno)].copy()
if df_turno.empty:
    st.warning(f'Não há dados coletados para {turno}.')
    st.stop()

df_turno = df_turno.sort_values(['time_id', 'rodada']).copy()
df_turno['pontos_acumulados_liga'] = df_turno.groupby('time_id')['pontos_rodada'].cumsum()
df_turno['posicao_liga'] = df_turno.groupby('rodada')['pontos_acumulados_liga'].rank(method='min', ascending=False)
df_turno['posicao_rodada'] = df_turno.groupby('rodada')['pontos_rodada'].rank(method='min', ascending=False)
rodadas = sorted(df_turno['rodada'].dropna().astype(int).unique().tolist())
times_disponiveis = sorted(df_turno['nome_time'].dropna().unique().tolist())
selecionados = st.sidebar.multiselect('Times nos gráficos', times_disponiveis, default=times_disponiveis)

if len(rodadas) > 1:
    intervalo = st.sidebar.slider('Intervalo de rodadas', min_value=rodadas[0], max_value=rodadas[-1], value=(rodadas[0], rodadas[-1]))
else:
    intervalo = (rodadas[0], rodadas[0])
ini, fim = intervalo
filtrado = df_turno[df_turno['nome_time'].isin(selecionados) & df_turno['rodada'].between(ini, fim)].copy()
if filtrado.empty:
    st.warning('Nenhum dado encontrado para os filtros selecionados.')
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("### Legenda dos times")

CORES_TIMES = {
    "cBenefs": "#20C761",
    "Pácábá Sporte Club": "#FF5A1F",
    "FEBRE DO RATO DE ESGOTO": "#FFD92F",
    "divadafiel": "#2878D0",
    "kopo d'água": "#9B59B6",
    "AIMS Acaba": "#E8436D",
}

for nome in times_disponiveis:
    if nome in selecionados:
        cor = CORES_TIMES.get(nome, "#FFFFFF")

        st.sidebar.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                margin:12px 0;
                font-size:16px;
                color:#F1F5F2;
                overflow-wrap:anywhere;
            ">
                <span style="
                    width:16px;
                    height:16px;
                    min-width:16px;
                    border-radius:4px;
                    background:{cor};
                    display:inline-block;
                "></span>
                <span>{nome}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


rodada_atual = int(filtrado['rodada'].max())
classificacao = filtrado[filtrado['rodada'] == rodada_atual].sort_values('pontos_acumulados_liga', ascending=False).reset_index(drop=True)
classificacao['posicao'] = range(1, len(classificacao) + 1)
lider = classificacao.iloc[0]
segundo = classificacao.iloc[1] if len(classificacao) > 1 else None
vantagem = float(lider['pontos_acumulados_liga'] - segundo['pontos_acumulados_liga']) if segundo is not None else 0
escudos = times_df.drop_duplicates('time_id').set_index('time_id').to_dict('index')

# Cabeçalho e resumo do turno lado a lado
col_hero, col_resumo = st.columns([1.6, 1], gap="medium")

with col_hero:
    st.markdown(
        '''
        <section class="hero">
            <div class="hero-eyebrow">TEMPORADA 2026 · FUTEBOL FANTASY</div>
            <div class="hero-title">⚽ CARTOLA 2026</div>
            <div class="hero-league">LIGA GALERA TI</div>
            <div class="hero-subtitle">
                Estatísticas · Classificação · Desempenho dos cartoleiros
            </div>
        </section>
        ''',
        unsafe_allow_html=True
    )

with col_resumo:
    st.markdown(
        '<div class="section-kicker">RESUMO DO TURNO</div>',
        unsafe_allow_html=True
    )
    resumo_col1, resumo_col2 = st.columns(2, gap="small")

    with resumo_col1:
        st.metric(
            'Turno selecionado',
            '1º turno' if inicio_turno == 19 else '2º turno'
        )
        st.metric('Última rodada no filtro', str(rodada_atual))

    with resumo_col2:
        st.metric('Líder do período', str(lider['nome_time']))
        st.metric(
            'Vantagem para o 2º',
            f'{vantagem:.2f} pts'.replace('.', ',')
        )

    st.caption(
        f'Rodadas {ini}–{fim} · Histórico disponível neste turno '
        f'até a rodada {max(rodadas)}.'
    )

aba_visao, aba_pontos, aba_posicoes, aba_patrimonio, aba_times = st.tabs(['🏆 Visão geral', '📈 Pontuação', '🔄 Posições', '💰 Patrimônio', '🛡️ Times'])
       
with aba_visao:
    st.markdown(
        '<div class="section-kicker">CLASSIFICAÇÃO DO TURNO</div>',
        unsafe_allow_html=True
    )
    st.subheader(f'Classificação · Rodada {rodada_atual}')

    tabela = classificacao[
        [
            'posicao', 'nome_time', 'cartoleiro',
            'pontos_rodada', 'pontos_acumulados_liga', 'patrimonio'
        ]
    ].rename(columns={
        'posicao': 'Posição',
        'nome_time': 'Time',
        'cartoleiro': 'Cartoleiro(a)',
        'pontos_rodada': 'Pontos na rodada',
        'pontos_acumulados_liga': 'Pontos no turno',
        'patrimonio': 'Patrimônio'
    })

    
    st.table(
        tabela.style
        .format({
            'Pontos na rodada': '{:.2f}',
            'Pontos no turno': '{:.2f}',
            'Patrimônio': '{:.2f}'
        })
        .set_properties(**{
            'background-color': tema['panel'],
            'color': tema['text'],
            'border': f"1px solid {tema['border']}",
            'padding': '10px'
        })
        .set_table_styles([
            {
                'selector': 'th',
                'props': [
                    ('background-color', tema['sidebar']),
                    ('color', tema['text']),
                    ('border', f"1px solid {tema['border']}"),
                    ('font-weight', '700'),
                    ('padding', '10px')
                ]
            },
            {
                'selector': 'td',
                'props': [
                    ('background-color', tema['panel']),
                    ('color', tema['text']),
                    ('border', f"1px solid {tema['border']}"),
                    ('padding', '10px')
                ]
            },
            {
                'selector': 'table',
                'props': [
                    ('border-collapse', 'collapse'),
                    ('width', '100%'),
                    ('border', f"1px solid {tema['border']}")
                ]
            }
        ])
    )

    st.markdown(
        '<div class="section-kicker">DESTAQUES DOS PARTICIPANTES</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)

    for i, (_, r) in enumerate(classificacao.iterrows()):
        info = escudos.get(str(r['time_id']), {})
        url = str(info.get('escudo', '') or '').strip()

        with cols[i % 3]:
            with st.container(border=True):
                if url.startswith(('http://', 'https://')):
                    try:
                        st.image(url, width=100)
                    except Exception:
                        st.markdown('## ⚽')
                else:
                    st.markdown('## ⚽')

                st.markdown(
                    f"**{int(r['posicao'])}º LUGAR NO TURNO**"
                )
                st.markdown(f"### {r['nome_time']}")
                st.write(r['cartoleiro'])

                st.markdown(
                    f"**{float(r['pontos_acumulados_liga']):.2f} pts**"
                )
                st.caption(
                    f"Patrimônio: {float(r['patrimonio']):.2f}"
                )

with aba_pontos:
    st.markdown('<div class="section-kicker">DESEMPENHO RODADA A RODADA</div>', unsafe_allow_html=True)
    st.subheader('Pontos conquistados em cada rodada')
    fig = px.line(filtrado.sort_values('rodada'), x='rodada', y='pontos_rodada', color='nome_time', markers=True, color_discrete_sequence=CORES, hover_data=['cartoleiro'], labels={'rodada':'Rodada','pontos_rodada':'Pontos na rodada','nome_time':'Time','cartoleiro':'Cartoleiro(a)'})
    fig.update_traces(line=dict(width=3), marker=dict(size=8)); fig.update_layout(
    hovermode='x unified',
    showlegend=False,
    font=dict(size=16, color=tema["text"]),
    paper_bgcolor=tema["panel"], plot_bgcolor=tema["panel"],
    margin=dict(l=65, r=20, t=30, b=55)
)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Evolução da pontuação acumulada no turno')
    fig = px.line(filtrado.sort_values('rodada'), x='rodada', y='pontos_acumulados_liga', color='nome_time', markers=True, color_discrete_sequence=CORES, hover_data=['cartoleiro','pontos_rodada'], labels={'rodada':'Rodada','pontos_acumulados_liga':'Pontos acumulados no turno','nome_time':'Time','cartoleiro':'Cartoleiro(a)','pontos_rodada':'Pontos na rodada'})
    fig.update_traces(line=dict(width=3), marker=dict(size=7)); fig.update_layout(
    hovermode='x unified',
    showlegend=False,
    font=dict(size=16, color=tema["text"]),
    paper_bgcolor=tema["panel"], plot_bgcolor=tema["panel"],
    margin=dict(l=65, r=20, t=30, b=55)
)
    st.plotly_chart(fig, use_container_width=True)

with aba_posicoes:
    st.markdown('<div class="section-kicker">DISPUTA ENTRE OS TIMES</div>', unsafe_allow_html=True)
    st.subheader('Posição em cada rodada · baseada nos pontos da rodada')
    fig = px.line(filtrado.sort_values('rodada'), x='rodada', y='posicao_rodada', color='nome_time', markers=True, line_shape='linear', color_discrete_sequence=CORES, hover_data=['cartoleiro','pontos_rodada'], labels={'rodada':'Rodada','posicao_rodada':'Posição na rodada','nome_time':'Time','cartoleiro':'Cartoleiro(a)','pontos_rodada':'Pontos na rodada'})
    fig.update_traces(line=dict(width=3), marker=dict(size=8)); fig.update_yaxes(autorange='reversed', tickmode='linear', tick0=1, dtick=1, range=[6.2, 0.8]); fig.update_layout(
    hovermode='x unified',
    showlegend=False,
    font=dict(size=16, color=tema["text"]),
    paper_bgcolor=tema["panel"], plot_bgcolor=tema["panel"],
    margin=dict(l=65, r=20, t=30, b=55)
)
    st.plotly_chart(fig, use_container_width=True)

with aba_patrimonio:
    st.markdown('<div class="section-kicker">CARTOLETAS</div>', unsafe_allow_html=True)
    st.subheader('Evolução do patrimônio')
    fig = px.line(filtrado.sort_values('rodada'), x='rodada', y='patrimonio', color='nome_time', markers=True, color_discrete_sequence=CORES, hover_data=['cartoleiro'], labels={'rodada':'Rodada','patrimonio':'Patrimônio (cartoletas)','nome_time':'Time','cartoleiro':'Cartoleiro(a)'})
    fig.update_traces(line=dict(width=3), marker=dict(size=7)); fig.update_layout(
    hovermode='x unified',
    showlegend=False,
    font=dict(size=16, color=tema["text"]),
    paper_bgcolor=tema["panel"], plot_bgcolor=tema["panel"],
    margin=dict(l=65, r=20, t=30, b=55)
)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander('Consultar e exportar dados filtrados'):
        cols = [c for c in ['rodada','posicao_rodada','posicao_liga','time_id','nome_time','cartoleiro','pontos_rodada','pontos_acumulados_liga','patrimonio','status'] if c in filtrado.columns]
        st.dataframe(filtrado.sort_values(['rodada','posicao_rodada'])[cols], use_container_width=True, hide_index=True)
        csv = filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button('⬇ Baixar dados filtrados em CSV', data=csv, file_name='galera_ti_historico.csv', mime='text/csv')


with aba_times:
    st.markdown(
        '<div class="section-kicker">ELENCO DA LIGA</div>',
        unsafe_allow_html=True
    )
    st.subheader('Times e cartoleiros')

    times_unicos = times_df.drop_duplicates('time_id').reset_index(drop=True)

    for inicio in range(0, len(times_unicos), 3):
        bloco = times_unicos.iloc[inicio:inicio + 3]
        cols = st.columns(3)

        for col, (_, t) in zip(cols, bloco.iterrows()):
            tid = str(t['time_id'])
            nome = str(t.get('nome_time', 'Time sem nome'))
            cartoleiro = str(t.get('cartoleiro', 'Cartoleiro não informado'))
            url = str(t.get('escudo', '') or '').strip()

            htime = df_turno[
                df_turno['time_id'] == tid
            ].sort_values('rodada')

            with col:
                with st.container(border=True):
                    st.markdown(
                        f'<div class="team-name">{nome}</div>',
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f'<div class="team-manager">{cartoleiro}</div>',
                        unsafe_allow_html=True
                    )

                    if url.startswith(('http://', 'https://')):
                        try:
                            st.image(url, width=100)
                        except Exception:
                            st.markdown(
                                '<div class="crest-fallback">⚽</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div class="crest-fallback">⚽</div>',
                            unsafe_allow_html=True
                        )

                    if not htime.empty:
                        ultima = htime.iloc[-1]
                        pontos = (
                            f'{float(ultima["pontos_acumulados_liga"]):,.2f}'
                            .replace(',', 'X')
                            .replace('.', ',')
                            .replace('X', '.')
                        )

                        st.metric('Pontos no turno', pontos)
                        st.caption(
                            f'Última rodada coletada: '
                            f'{int(ultima["rodada"])}'
                        )
                    else:
                        st.caption('Sem dados para o turno selecionado.')


st.markdown(
    """
    <div class="footer">
      <div>Desenvolvido por <strong>Ricardo Spicka</strong> © 2026</div>
      <div class="footer-links">
        <a href="https://github.com/RicardoSpicka" target="_blank" rel="noopener noreferrer">GitHub</a>
        <span>·</span>
        <a href="https://www.linkedin.com/in/ricardo-spicka-b79049160" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <span>·</span>
        <span>Cartola 2026 · Liga Galera TI</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
