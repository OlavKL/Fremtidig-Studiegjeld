import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Studieøkonomi-kalkulator", layout="wide")

st.title("Studieøkonomi-kalkulator")
st.write(
    "Beregn fremtidig studielån basert på inntekt, bostatus, støttegrad og eventuelle skolepenger."
)

# -------------------------
# Hjelpefunksjoner
# -------------------------
def format_nok(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{abs(value):,.0f} kr".replace(",", " ")

def calculate_stipend_ratio(income: float, threshold: float, full_loan_income_limit: float) -> float:
    """
    Returnerer stipendandel av støtte:
    - 40 % stipend ved eller under threshold
    - lineært ned til 0 ved full_loan_income_limit
    """
    if income <= threshold:
        return 0.40
    if income >= full_loan_income_limit:
        return 0.0

    reduction_range = full_loan_income_limit - threshold
    if reduction_range <= 0:
        return 0.0

    remaining_share = 1 - ((income - threshold) / reduction_range)
    return max(0.0, 0.40 * remaining_share)


# -------------------------
# Sidebar: globale innstillinger
# -------------------------
st.sidebar.header("Globale innstillinger")

annual_basis_support = st.sidebar.number_input(
    "Årlig basisstøtte",
    min_value=0,
    value=166_859,
    step=1_000,
)

annual_income_threshold = st.sidebar.number_input(
    "Årlig inntektsgrense for full stipendandel",
    min_value=0,
    value=234_821,
    step=1_000,
)

annual_full_loan_limit = st.sidebar.number_input(
    "Årlig inntekt der alt blir lån",
    min_value=0,
    value=300_000,
    step=1_000,
)

years = st.sidebar.number_input(
    "Antall studieår",
    min_value=1,
    max_value=8,
    value=5,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.write("Modellen antar at du består og fullfører på normert tid.")

# Semesterverdier
semester_basis_support = annual_basis_support / 2
semester_income_threshold = annual_income_threshold / 2
semester_full_loan_limit = annual_full_loan_limit / 2

# -------------------------
# Input per år / semester
# -------------------------
st.markdown("## Legg inn data")

rows = []
year_summary_rows = []

total_loan = 0.0
total_stipend = 0.0
total_support = 0.0
total_school_fees = 0.0
cumulative_debt = 0.0

for year in range(1, years + 1):
    st.markdown(f"---")
    st.markdown(f"## Studieår {year}")

    school_fees = st.number_input(
        f"Skolepenger år {year}",
        min_value=0,
        value=0,
        step=5_000,
        key=f"school_fees_{year}",
        help="Skolepenger legges inn som 100 % lån i denne modellen.",
    )

    col1, col2 = st.columns(2)

    # Semester 1
    with col1:
        st.markdown(f"### År {year} – Semester 1")

        income_s1 = st.number_input(
            f"Inntekt semester 1 (år {year})",
            min_value=0,
            value=60_000,
            step=5_000,
            key=f"income_s1_{year}",
        )

        lives_away_s1 = st.selectbox(
            f"Bodd borte semester 1 (år {year})?",
            options=["Ja", "Nei"],
            index=0,
            key=f"away_s1_{year}",
        )

        support_share_s1 = st.slider(
            f"Andel støtte mottatt semester 1 (år {year})",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_s1_{year}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    # Semester 2
    with col2:
        st.markdown(f"### År {year} – Semester 2")

        income_s2 = st.number_input(
            f"Inntekt semester 2 (år {year})",
            min_value=0,
            value=60_000,
            step=5_000,
            key=f"income_s2_{year}",
        )

        lives_away_s2 = st.selectbox(
            f"Bodd borte semester 2 (år {year})?",
            options=["Ja", "Nei"],
            index=0,
            key=f"away_s2_{year}",
        )

        support_share_s2 = st.slider(
            f"Andel støtte mottatt semester 2 (år {year})",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_s2_{year}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    year_support = 0.0
    year_stipend = 0.0
    year_loan = 0.0

    semester_inputs = [
        ("Semester 1", income_s1, lives_away_s1, support_share_s1),
        ("Semester 2", income_s2, lives_away_s2, support_share_s2),
    ]

    for semester_name, income, lives_away, support_share in semester_inputs:
        actual_support = semester_basis_support * support_share

        if lives_away == "Ja":
            stipend_ratio = calculate_stipend_ratio(
                income=income,
                threshold=semester_income_threshold,
                full_loan_income_limit=semester_full_loan_limit,
            )
        else:
            stipend_ratio = 0.0

        stipend_amount = actual_support * stipend_ratio
        loan_amount = actual_support - stipend_amount

        year_support += actual_support
        year_stipend += stipend_amount
        year_loan += loan_amount

        total_support += actual_support
        total_stipend += stipend_amount
        total_loan += loan_amount

        rows.append(
            {
                "Studieår": year,
                "Semester": semester_name,
                "Inntekt": income,
                "Bodd borte": lives_away,
                "Støttegrad": support_share,
                "Mottatt støtte": actual_support,
                "Stipend": stipend_amount,
                "Lån fra basisstøtte": loan_amount,
                "Skolepenger": 0.0,
            }
        )

    # Legg til skolepenger som 100 % lån på årsnivå
    total_school_fees += school_fees
    total_loan += school_fees

    cumulative_debt = total_loan

    year_summary_rows.append(
        {
            "Studieår": year,
            "Støtte totalt": year_support,
            "Stipend": year_stipend,
            "Lån fra basisstøtte": year_loan,
            "Skolepenger (100 % lån)": school_fees,
            "Totalt lån dette året": year_loan + school_fees,
            "Kumulativ gjeld": cumulative_debt,
        }
    )

# -------------------------
# Resultater
# -------------------------
semester_df = pd.DataFrame(rows)
year_df = pd.DataFrame(year_summary_rows)

st.markdown("---")
st.markdown("## Oppsummering")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total studiegjeld", format_nok(total_loan))
k2.metric("Total stipend", format_nok(total_stipend))
k3.metric("Total mottatt støtte", format_nok(total_support))
k4.metric("Totale skolepenger", format_nok(total_school_fees))

st.markdown("## Årsoversikt")
st.dataframe(
    year_df.style.format(
        {
            "Støtte totalt": lambda x: format_nok(x),
            "Stipend": lambda x: format_nok(x),
            "Lån fra basisstøtte": lambda x: format_nok(x),
            "Skolepenger (100 % lån)": lambda x: format_nok(x),
            "Totalt lån dette året": lambda x: format_nok(x),
            "Kumulativ gjeld": lambda x: format_nok(x),
        }
    ),
    use_container_width=True,
)

st.markdown("## Semesteroversikt")
st.dataframe(
    semester_df.style.format(
        {
            "Inntekt": lambda x: format_nok(x),
            "Støttegrad": "{:.0%}",
            "Mottatt støtte": lambda x: format_nok(x),
            "Stipend": lambda x: format_nok(x),
            "Lån fra basisstøtte": lambda x: format_nok(x),
            "Skolepenger": lambda x: format_nok(x),
        }
    ),
    use_container_width=True,
)

# -------------------------
# Graf
# -------------------------
st.markdown("## Gjeldsutvikling")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(year_df["Studieår"], year_df["Kumulativ gjeld"], marker="o")
ax.set_xlabel("Studieår")
ax.set_ylabel("Kumulativ gjeld")
ax.set_title("Utvikling i studiegjeld")
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# -------------------------
# Forklaring
# -------------------------
st.markdown("## Forutsetninger")
st.write(
    """
- Modellen antar at du består og fullfører på normert tid.
- Hvert studieår er delt inn i to semestre.
- Bor du hjemme i et semester, settes stipendandelen til 0 for det semesteret.
- Bor du borte, kan opptil 40 % av støtten bli stipend.
- Over inntektsgrensen trappes stipendandelen lineært ned til 0.
- Skolepenger legges inn per år og behandles som 100 % lån i denne modellen.
- Dette er en planleggingsmodell og ikke en eksakt kopi av Lånekassens beregning.
"""
)
