import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Marginaleffekt", layout="wide")

st.title("Marginaleffekt for student")
st.write(
    "Undersøk hvor mye du mister i skatt og stipend ved høyere inntekt, "
    "og hvor mye du faktisk sitter igjen med av neste krone."
)

# -------------------------
# Hjelpefunksjoner
# -------------------------
def format_nok(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{abs(value):,.0f} kr".replace(",", " ")

def calculate_stipend_loss(
    income: float,
    income_threshold: float,
    stipend_loss_rate: float,
    max_stipend_loss: float
) -> float:
    """
    Beregner totalt stipendtap ved gitt årsinntekt.
    stipend_loss_rate = tap per krone over grensen, f.eks. 0.55
    max_stipend_loss = maksimalt stipend som kan tapes
    """
    if income <= income_threshold:
        return 0.0

    loss = (income - income_threshold) * stipend_loss_rate
    return min(loss, max_stipend_loss)

def marginal_tax_rate(income: float, salary_tax_rate: float, bracket_1_limit: float, bracket_1_rate: float) -> float:
    """
    Forenklet marginal skattesats:
    - trygdeavgift + alminnelig inntektsskatt
    - + trinn 1 over bracket_1_limit
    """
    rate = salary_tax_rate
    if income >= bracket_1_limit:
        rate += bracket_1_rate
    return rate

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("Forutsetninger")

annual_basis_support = st.sidebar.number_input(
    "Årlig basisstøtte",
    min_value=0,
    value=166_859,
    step=1_000,
)

stipend_share = st.sidebar.slider(
    "Stipendandel av basisstøtte",
    min_value=0.0,
    max_value=1.0,
    value=0.40,
    step=0.01,
)

income_threshold = st.sidebar.number_input(
    "Inntektsgrense for fullt stipend",
    min_value=0,
    value=234_821,
    step=1_000,
)

months_with_support = st.sidebar.number_input(
    "Antall måneder med støtte",
    min_value=1,
    max_value=12,
    value=11,
    step=1,
)

salary_tax_rate = st.sidebar.slider(
    "Skatt + trygdeavgift før trinnskatt",
    min_value=0.0,
    max_value=1.0,
    value=0.296,  # 22 % + 7.6 %
    step=0.001,
    help="Forenklet sats: alminnelig inntektsskatt + trygdeavgift",
)

bracket_1_limit = st.sidebar.number_input(
    "Grense for trinnskatt trinn 1",
    min_value=0,
    value=226_100,
    step=1_000,
)

bracket_1_rate = st.sidebar.slider(
    "Trinnskatt trinn 1",
    min_value=0.0,
    max_value=0.10,
    value=0.017,
    step=0.001,
)

income_min = st.sidebar.number_input(
    "Min inntekt i analyse",
    min_value=0,
    value=0,
    step=10_000,
)

income_max = st.sidebar.number_input(
    "Maks inntekt i analyse",
    min_value=0,
    value=400_000,
    step=10_000,
)

income_step = st.sidebar.number_input(
    "Intervall",
    min_value=100,
    value=1_000,
    step=100,
)

# -------------------------
# Avledede størrelser
# -------------------------
max_stipend = annual_basis_support * stipend_share
stipend_loss_rate = 0.05 * months_with_support  # f.eks. 0.55 ved 11 mnd

st.markdown("## Nøkkelantakelser")
c1, c2, c3 = st.columns(3)
c1.metric("Maks stipend", format_nok(max_stipend))
c2.metric("Tap i stipend per kr over grensen", f"{stipend_loss_rate:.0%}")
c3.metric(
    "Omtrentlig marginalskatt over trinn 1",
    f"{(salary_tax_rate + bracket_1_rate):.1%}"
)

# -------------------------
# Beregningstabell
# -------------------------
rows = []

for income in range(int(income_min), int(income_max) + 1, int(income_step)):
    stipend_loss = calculate_stipend_loss(
        income=income,
        income_threshold=income_threshold,
        stipend_loss_rate=stipend_loss_rate,
        max_stipend_loss=max_stipend,
    )

    tax_rate = marginal_tax_rate(
        income=income,
        salary_tax_rate=salary_tax_rate,
        bracket_1_limit=bracket_1_limit,
        bracket_1_rate=bracket_1_rate,
    )

    total_marginal_effect = tax_rate
    if stipend_loss < max_stipend:
        if income > income_threshold:
            total_marginal_effect += stipend_loss_rate

    net_of_next_krone = 1 - total_marginal_effect

    rows.append(
        {
            "Inntekt": income,
            "Totalt stipendtap": stipend_loss,
            "Marginal skatt": tax_rate,
            "Marginal stipendtap": stipend_loss_rate if (income > income_threshold and stipend_loss < max_stipend) else 0.0,
            "Samlet marginaleffekt": total_marginal_effect,
            "Netto av neste krone": net_of_next_krone,
        }
    )

df = pd.DataFrame(rows)

# -------------------------
# Finn "dummeste" område
# -------------------------
worst_row = df.loc[df["Samlet marginaleffekt"].idxmax()]
worst_income = int(worst_row["Inntekt"])
worst_effect = float(worst_row["Samlet marginaleffekt"])
worst_net = float(worst_row["Netto av neste krone"])

st.markdown("## Oppsummering")
k1, k2, k3 = st.columns(3)
k1.metric("Dummeste inntektsnivå i modellen", format_nok(worst_income))
k2.metric("Samlet marginaleffekt", f"{worst_effect:.1%}")
k3.metric("Du sitter igjen med", f"{worst_net:.1%} av neste krone")

st.info(
    "Tolkning: Hvis samlet marginaleffekt er 86 %, betyr det at du mister omtrent 86 øre "
    "i skatt og stipend for hver ekstra krone du tjener i dette området."
)

# -------------------------
# Tabell
# -------------------------
st.markdown("## Tabell")
st.dataframe(
    df.style.format(
        {
            "Inntekt": lambda x: format_nok(x),
            "Totalt stipendtap": lambda x: format_nok(x),
            "Marginal skatt": "{:.1%}",
            "Marginal stipendtap": "{:.1%}",
            "Samlet marginaleffekt": "{:.1%}",
            "Netto av neste krone": "{:.1%}",
        }
    ),
    use_container_width=True,
)

# -------------------------
# Grafer
# -------------------------
st.markdown("## Samlet marginaleffekt")

fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(df["Inntekt"], df["Samlet marginaleffekt"] * 100)
ax1.set_xlabel("Inntekt")
ax1.set_ylabel("Samlet marginaleffekt (%)")
ax1.set_title("Skatt + stipendtap per ekstra krone")
ax1.grid(True, alpha=0.3)
st.pyplot(fig1)

st.markdown("## Netto av neste krone")

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(df["Inntekt"], df["Netto av neste krone"] * 100)
ax2.set_xlabel("Inntekt")
ax2.set_ylabel("Netto igjen (%)")
ax2.set_title("Hvor mye du sitter igjen med av neste krone")
ax2.grid(True, alpha=0.3)
st.pyplot(fig2)

st.markdown("## Totalt stipendtap")

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.plot(df["Inntekt"], df["Totalt stipendtap"])
ax3.set_xlabel("Inntekt")
ax3.set_ylabel("Stipendtap (kr)")
ax3.set_title("Totalt stipendtap ved ulik inntekt")
ax3.grid(True, alpha=0.3)
st.pyplot(fig3)

# -------------------------
# Kort forklaring
# -------------------------
st.markdown("## Hvordan lese dette")
st.write(
    """
- **Marginal skatt** = hvor mye skatt/avgift neste krone utløser i modellen.
- **Marginal stipendtap** = hvor mye stipend du mister per ekstra krone over inntektsgrensen.
- **Samlet marginaleffekt** = skatt + stipendtap.
- **Netto av neste krone** = det du faktisk sitter igjen med.
"""
)
