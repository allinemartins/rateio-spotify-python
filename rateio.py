import pandas as pd
import streamlit as st
import base64
from datetime import datetime
from io import StringIO


# Meses pt -> en
meses_pt_en = {
    "Janeiro": "January", "Fevereiro": "February", "Março": "March",
    "Abril": "April", "Maio": "May", "Junho": "June",
    "Julho": "July", "Agosto": "August", "Setembro": "September",
    "Outubro": "October", "Novembro": "November", "Dezembro": "December"
}

def converter_mes(mes_ano):
    for mes_pt, mes_en in meses_pt_en.items():
        if mes_pt in mes_ano:
            return mes_ano.replace(mes_pt, mes_en)
    return mes_ano

def img_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# Dados CSV hospedado no Gist
csv_url = st.secrets["CSV_GIST_URL"]

# Carregar dados diretamente da URL
df = pd.read_csv(csv_url, sep=",", decimal=",")
df.columns = df.columns.str.strip().str.replace('"', '').str.replace('\ufeff','')  # remover BOM e aspas

# Corrigir coluna Valor e datas
df["Valor"] = pd.to_numeric(df["Valor"].astype(str).str.replace(",", "."), errors="coerce")
df["DataPagamento"] = pd.to_datetime(df["DataPagamento"], errors="coerce", dayfirst=True)
df["Pago"] = df["Pago"].astype(str).str.strip().str.capitalize()

# Converter meses e criar datetime
df["Mes_en"] = df["Mes"].apply(converter_mes)
df["Mes_dt"] = pd.to_datetime(df["Mes_en"], format="%B, %Y")

# Setup Streamlit
st.set_page_config(page_title="Controle Rateio Spotify", page_icon="🎵", layout="wide")
st.title("🎵 Controle de Rateio Spotify")

# Hoje
hoje = datetime.today()
mes_atual_str_pt = hoje.strftime("%B, %Y")
mes_atual_str_en = converter_mes(mes_atual_str_pt)

# --- Selectbox apenas para mês (Status Visual) ---
meses_ordenados = df.sort_values("Mes_dt")["Mes"].unique()
meses_en_list = df.sort_values("Mes_dt")["Mes_en"].tolist()
idx_mes_atual = meses_en_list.index(mes_atual_str_en) if mes_atual_str_en in meses_en_list else 0
mes_selecionado = st.sidebar.selectbox("Selecionar Mês", options=meses_ordenados, index=idx_mes_atual)

# Métricas gerais
pagos_total = df[df["Pago"]=="Sim"]["Valor"].sum()
pendentes_mes = df[(df["Mes"]==mes_selecionado) & (df["Pago"]=="Nao")]
pagos_mes = df[df["Pago"]=="Sim"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Valor total investido", f"R$ {pagos_total:.2f}")
col2.metric("👥 Total membros", len(df["Pessoa"].unique()))
col3.metric("✅ Total meses pagos", pagos_mes.shape[0])
col4.metric("❌ Pendentes mês atual", pendentes_mes.shape[0])

st.markdown("---")

# Status Visual
st.subheader("👤 Status Visual")
dados_mes = df[df["Mes"]==mes_selecionado]
if not dados_mes.empty:
    for _, row in dados_mes.iterrows():
        img_path = f"imagens/{row.Pessoa.lower()}.png"
        img_b64 = img_to_base64(img_path)
        if img_b64:
            img_tag = f'<img src="data:image/png;base64,{img_b64}" width="100" style="border-radius:50%; margin-right:25px;">'
        else:
            img_tag = '<img src="https://via.placeholder.com/100" width="100" style="border-radius:50%; margin-right:25px;">'
        
        # Cores e estilo diferentes para pago / pendente
        if row["Pago"] == "Sim":
            destaque = "background-color:#ecf0f1; color:#2c3e50;"
        else:
            destaque = "background-color:#ffeaea; color:#c0392b;"  # vermelho suave

        status_color = "#27ae60" if row["Pago"]=="Sim" else "#c0392b"
        pago_text = "✅ Pago" if row["Pago"]=="Sim" else "❌ Pendente"
        
        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; margin:25px 0;">
                <div style="{destaque} width:90%; max-width:800px; border-radius:20px; padding:25px; 
                            box-shadow: 0 4px 12px rgba(0,0,0,0.25); display:flex; align-items:center; 
                            text-align:left; font-family: Arial, sans-serif;">
                    {img_tag}
                    <div>
                        <b style="font-size:22px;">{row.Pessoa}</b><br>
                        <span style="font-size:18px;">💰 R$ {row.Valor:.2f}</span><br>
                        <span style="color:{status_color}; font-weight:bold; font-size:20px;">{pago_text}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.write("Nenhum dado para mostrar no status visual.")

st.markdown("---")

# --- Próximo a pagar (sempre no mês seguinte) ---
mes_selecionado_dt = df.loc[df["Mes"]==mes_selecionado, "Mes_dt"].iloc[0]  # datetime do mês selecionado
prox_mes_dt = df["Mes_dt"][df["Mes_dt"] > mes_selecionado_dt].min()

if pd.isna(prox_mes_dt):
    st.markdown(f"<div style='padding:10px; background-color:#f0f0f0; border-radius:10px; text-align:center;'>"
                f"<b>⏭ Próximo a pagar:</b> Nenhum pendente nos próximos meses"
                f"</div>", unsafe_allow_html=True)
else:
    pendentes_prox = df[(df["Mes_dt"] == prox_mes_dt) & (df["Pago"]=="Nao")]
    if not pendentes_prox.empty:
        pessoa_prox = pendentes_prox.iloc[0]["Pessoa"]
        mes_prox = pendentes_prox.iloc[0]["Mes"]
        st.markdown(
            f"<div style='padding:15px; background-color:#ffeaa7; border-radius:12px; text-align:center; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);'>"
            f"<b>⏭ Próximo a pagar:</b><br><span style='font-size:18px; color:#d63031;'>{pessoa_prox}</span><br>"
            f"<i>{mes_prox}</i>"
            f"</div>", unsafe_allow_html=True
        )
    else:
        mes_prox = prox_mes_dt.strftime("%B, %Y")
        st.markdown(
            f"<div style='padding:15px; background-color:#dfe6e9; border-radius:12px; text-align:center;'>"
            f"<b>⏭ Próximo a pagar:</b><br>Nenhum pendente no próximo mês<br><i>{mes_prox}</i>"
            f"</div>", unsafe_allow_html=True
        )

st.markdown("---")

# Histórico detalhado (com filtros de pessoa e status)
st.subheader("📊 Histórico detalhado")
pessoas_selecionadas = st.multiselect("Filtrar por Pessoa", options=sorted(df["Pessoa"].unique()), default=sorted(df["Pessoa"].unique()))
status_opcoes = ["Todos", "Sim", "Nao"]
status_selecionado = st.selectbox("Filtrar por Status de Pagamento", status_opcoes, index=0)

historico = df[df["Pessoa"].isin(pessoas_selecionadas)].copy()
historico = historico.sort_values(["Mes_dt"])

if status_selecionado != "Todos":
    historico = historico[historico["Pago"] == status_selecionado]

historico["Status"] = historico["Pago"].apply(lambda x: "✅ Pago" if str(x).strip().capitalize() == "Sim" else "❌ Pendente")

def highlight_status(row):
    return ["background-color: #f9e79f" if str(row["Pago"]).strip().capitalize() == "Nao" else "" for _ in row]

st.dataframe(
    historico[["Mes","Pessoa","Valor","Pago"]]
        .style
        .format({"Valor": "R$ {:.2f}"}).apply(highlight_status, axis=1),
    use_container_width=True
)

# Total pago por pessoa
st.subheader("💰 Total pago por pessoa")
total_pago_pessoa = df[df["Pago"]=="Sim"].groupby("Pessoa")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
st.dataframe(total_pago_pessoa.style.format({"Valor": "R$ {:.2f}"}), use_container_width=True)

