import yfinance as yf
import pandas as pd
from datetime import datetime
import json

# ==========================================
# LOAD TICKERS
# ==========================================

with open("tickers.json", "r", encoding="utf-8") as file:
    ticker_data = json.load(file)

TICKERS = (
    ticker_data["fiis"]
    + ticker_data["acoes"]
    + ticker_data["etfs"]
)

# ==========================================
# HELPERS
# ==========================================

def format_number(value):
    if value is None:
        return 0

    try:
        return round(float(value), 2)
    except:
        return 0


def format_financial(value):
    """
    Formata números financeiros:
    1.2K
    1.5M
    2.4B
    """

    try:
        value = float(value)

        abs_value = abs(value)

        if abs_value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}T"

        if abs_value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"

        if abs_value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"

        if abs_value >= 1_000:
            return f"{value / 1_000:.2f}K"

        return f"{value:.2f}"

    except:
        return "0"


def format_currency(value):
    """
    Formata moeda brasileira.
    """

    try:
        value = float(value)

        if abs(value) >= 1_000:
            return f"R$ {format_financial(value)}"

        return f"R$ {value:.2f}"

    except:
        return "R$ 0.00"


def detect_category(info, ticker):
    quote_type = str(info.get("quoteType", "")).lower()
    long_name = str(info.get("longName", "")).lower()

    if "fii" in long_name:
        return "FII"

    if ticker.endswith("11.SA"):
        return "FII/UNIT"

    if quote_type == "etf":
        return "ETF"

    return "AÇÃO"


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def get_asset_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info

        # ==================================
        # DADOS BÁSICOS
        # ==================================

        nome = info.get("longName", ticker_symbol)

        preco_atual = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or 0
        )

        # ==================================
        # DIVIDENDOS
        # ==================================

        dividends = ticker.dividends

        hoje = pd.Timestamp.now(tz="America/Sao_Paulo")
        um_ano_atras = hoje - pd.Timedelta(days=365)

        dividends_12m = dividends[dividends.index >= um_ano_atras]

        total_dividendos = dividends_12m.sum()

        dy = 0

        if preco_atual > 0:
            dy = (total_dividendos / preco_atual) * 100

        # ==================================
        # CATEGORIA
        # ==================================

        categoria = detect_category(info, ticker_symbol)

        # ==================================
        # SETOR
        # ==================================

        setor = (
            info.get("sector")
            or info.get("category")
            or "N/D"
        )

        # ==================================
        # P/VP
        # ==================================

        pvp = (
            info.get("priceToBook")
            or 0
        )

        # ==================================
        # LIQUIDEZ
        # ==================================

        liquidez = (
            info.get("averageVolume")
            or info.get("volume")
            or 0
        )

        # ==================================
        # PATRIMÔNIO / MARKET CAP
        # ==================================

        patrimonio = (
            info.get("marketCap")
            or info.get("enterpriseValue")
            or 0
        )

        # ==================================
        # RESULTADO
        # ==================================

        return {
            "Ticker": ticker_symbol.replace(".SA", ""),
            "Nome": nome,
            "Categoria": categoria,
            "Setor": setor,
            "Preço Atual": format_currency(preco_atual),
            "Dividendos 12M": format_currency(total_dividendos),
            "DY (%)": f"{format_number(dy)}%",
            "P/VP": format_number(pvp),
            "Liquidez": format_financial(liquidez),
            "Patrimônio": format_currency(patrimonio),
            "Atualizado Em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {
            "Ticker": ticker_symbol.replace(".SA", ""),
            "Erro": str(e)
        }


# ==========================================
# EXECUÇÃO
# ==========================================

resultados = []

for ticker in TICKERS:
    print(f"Buscando {ticker}...")

    resultado = get_asset_data(ticker)

    resultados.append(resultado)

# ==========================================
# DATAFRAME
# ==========================================

df = pd.DataFrame(resultados)

print("\n")
print(df)

# ==========================================
# EXPORT CSV
# ==========================================

df.to_csv(
    "ativos.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# EXPORT JSON
# ==========================================

df.to_json(
    "ativos.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("\nCSV gerado com sucesso!")
print("JSON gerado com sucesso!")
