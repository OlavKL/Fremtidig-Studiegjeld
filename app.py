import streamlit as st
import pandas as pd

st.set_page_config(page_title="Studielånskalkulator", layout="wide")

st.title("Studielånskalkulator")
st.write(
    "Beregn forventet studiegjeld år for år basert på inntekt, bostatus og støttegrad."
)

# -----------------------------
# Hjelpefunksjoner
# -----------------------------
def format_nok(x):
    return f"{x:,.0f} kr".replace(",", " ")

def calculate_stipend_ratio(income, threshold, full_loan_income_limit):
    """
    Returnerer stipendandel av basisstøtten:
    - 0.40 under/lik threshold
    - lineært ned til 0 ved full_loan_income_limit
    """
    if income <= threshold:
        return 0.40
    if income >= full_loan_income_limit:
        return 0.0
    reduction_range = full_loan_income_limit - threshold
    remaining_share = 1 - ((income - threshold) / reduction_range)
    return max(0.0, 0.40 * remaining_share)

# -----------------------------
# Sidebar: globale innstillinger
# -----------------------------
st.sidebar.header("Globale innstillinger")

default_basis_support = st.sidebar.number_input(
    "Årlig basisstøtte",
    min_value=0,
    value=166_859,
    step=1_000,
)

income_threshold = st.sidebar.number_input(
    "Inntektsgrense for full stipendandel",
    min_value=0,
    value=234_821,
    step=1_000,
)

full_loan_income_limit = st.sidebar.number_input(
    "Inntekt der alt blir lån",
    min_value=0,
    value=300_000,
    step=1_000,
)

default_passed = st.sidebar.checkbox("Bestått studiet som standard", value=True)

st.sidebar.markdown("---")
years = st.sidebar.number_input(
    "Antall studieår",
    min_value=1,
    max_value=8,
    value=5,
    step=1,
)

st.markdown("## Legg inn data per år")

rows = []
total_loan = 0
total_stipend = 0

for year in range(1, years + 1):
    st.markdown(f"### År {year}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        income = st.number_input(
            f"Inntekt år {year}",
            min_value=0,
            value=120_000,
            step=5_000,
            key=f"income_{year}",
        )

    with col2:
        lives_away = st.selectbox(
            f"Bodd borte år {year}?",
            options=["Ja", "Nei"],
            index=0,
            key=f"away_{year}",
        )

    with col3:
        support_share = st.slider(
            f"Andel støtte mottatt år {year}",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_{year}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    with col4:
        passed = st.selectbox(
            f"Bestått år {year}?",
            options=["Ja", "Nei"],
            index=0 if default_passed else 1,
            key=f"passed_{year}",
        )

    actual_support = default_basis_support * support_share

    # Standard: alt utbetales som lån først
    stipend_ratio = 0.0

    if lives_away == "Ja" and passed == "Ja":
        stipend_ratio = calculate_stipend_ratio(
            income=income,
            threshold=income_threshold,
            full_loan_income_limit=full_loan_income_limit,
        )

    stipend_amount = actual_support * stipend_ratio
    loan_amount = actual_support - stipend_amount

    total_loan += loan_amount
    total_stipend += stipend_amount

    rows.append(
        {
            "År": year,
            "Inntekt": income,
            "Bodd borte": lives_away,
            "Støttegrad": support_share,
            "Bestått": passed,
            "Mottatt støtte": actual_support,
            "Stipend": stipend_amount,
            "Lån": loan_amount,
            "Kumulativ gjeld": total_loan,
        }
    )

# -----------------------------
# Resultater
# -----------------------------
df = pd.DataFrame(rows)

st.markdown("## Oppsummering")

k1, k2, k3 = st.columns(3)
k1.metric("Total studiegjeld", format_nok(total_loan))
k2.metric("Total stipend", format_nok(total_stipend))
k3.metric("Total mottatt støtte", format_nok(total_loan + total_stipend))

st.dataframe(
    df.style.format(
        {
            "Inntekt": lambda x: format_nok(x),
            "Mottatt støtte": lambda x: format_nok(x),
            "Stipend": lambda x: format_nok(x),
            "Lån": lambda x: format_nok(x),
            "Kumulativ gjeld": lambda x: format_nok(x),
            "Støttegrad": "{:.0%}",
        }
    ),
    use_container_width=True,
)

# -----------------------------
# Ekstra visning
# -----------------------------
st.markdown("## Gjeldsutvikling")
chart_df = df[["År", "Kumulativ gjeld"]].copy()
chart_df = chart_df.set_index("År")
st.line_chart(chart_df)

st.markdown("## Viktige forutsetninger")
st.write(
    """
- Kalkulatoren antar at støtte først gis som lån, og at en andel senere kan bli omgjort til stipend.
- Bor du hjemme, settes stipendandelen til 0 i denne modellen.
- Har du ikke bestått, settes stipendandelen også til 0.
- Over inntektsgrensen trappes stipendandelen lineært ned til 0 ved nivået du selv velger i sidebaren.
- Dette er en forenklet planleggingsmodell, ikke en eksakt kopi av Lånekassens interne beregning.
"""
)
