import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Studieøkonomi-kalkulator", layout="wide")

st.title("Studieøkonomi-kalkulator")
st.write(
    "Beregn fremtidig studielån basert på årsinntekt, bostatus per semester, støttegrad og eventuelle skolepenger."
)

# -------------------------
# Hjelpefunksjoner
# -------------------------
def format_nok(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{abs(value):,.0f} kr".replace(",", " ")

def calculate_stipend_ratio(
    annual_income: float,
    annual_threshold: float,
    annual_full_loan_limit: float
) -> float:
    """
    Returnerer stipendandel av støtte basert på årsinntekt:
    - 40 % stipend ved eller under threshold
    - lineært ned til 0 ved full_loan_income_limit
    """
    if annual_income <= annual_threshold:
        return 0.40
    if annual_income >= annual_full_loan_limit:
        return 0.0

    reduction_range = annual_full_loan_limit - annual_threshold
    if reduction_range <= 0:
        return 0.0

    remaining_share = 1 - ((annual_income - annual_threshold) / reduction_range)
    return max(0.0, 0.40 * remaining_share)

def get_income_year_for_semester(semester_number: int) -> int:
    """
    Mapping:
    Semester 1 -> Årsinntekt år 1
    Semester 2 -> Årsinntekt år 2
    Semester 3 -> Årsinntekt år 2
    Semester 4 -> Årsinntekt år 3
    Semester 5 -> Årsinntekt år 3
    Semester 6 -> Årsinntekt år 4
    osv.
    """
    if semester_number == 1:
        return 1
    return (semester_number // 2) + 1

def get_term_label(semester_number: int) -> str:
    season = "Høst" if semester_number % 2 == 1 else "Vår"
    return f"{season} ({semester_number}. semester)"


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

semester_basis_support = annual_basis_support / 2
num_semesters = years * 2

# Hvor mange inntektsår som trengs for å dekke alle semestre
income_year_count = years + 1
# -------------------------
# Input: årsinntekt
# -------------------------
st.markdown("## Årsinntekt")
st.write(
    "Legg inn årsinntekt per kalenderår. Hver årsinntekt brukes på de semestrene den faktisk påvirker."
)

annual_incomes = {}
income_usage_rows = []

income_cols = st.columns(min(income_year_count, 3))

for i in range(1, income_year_count + 1):
    col = income_cols[(i - 1) % len(income_cols)]
    with col:
        annual_incomes[i] = st.number_input(
            f"Årsinntekt år {i}",
            min_value=0,
            value=120_000,
            step=5_000,
            key=f"annual_income_{i}",
        )

for semester_number in range(1, num_semesters + 1):
    income_year = get_income_year_for_semester(semester_number)
    income_usage_rows.append(
        {
            "Semester": get_term_label(semester_number),
            "Bruker årsinntekt": f"År {income_year}",
            "Årsinntekt": annual_incomes[income_year],
        }
    )

usage_df = pd.DataFrame(income_usage_rows)
st.dataframe(
    usage_df.style.format({"Årsinntekt": lambda x: format_nok(x)}),
    use_container_width=True,
)

# -------------------------
# Input per studieår / semester
# -------------------------
st.markdown("## Data per studieår")

semester_rows = []
year_summary_rows = []

total_loan = 0.0
total_stipend = 0.0
total_support = 0.0
total_school_fees = 0.0
cumulative_debt = 0.0

semester_number = 1

for year in range(1, years + 1):
    st.markdown("---")
    st.markdown(f"## Studieår {year}")

    school_fees = st.number_input(
        f"Skolepenger studieår {year}",
        min_value=0,
        value=0,
        step=5_000,
        key=f"school_fees_{year}",
        help="Skolepenger behandles som 100 % lån i denne modellen.",
    )

    col1, col2 = st.columns(2)

    # Høstsemester
    with col1:
        current_semester = semester_number
        current_label = get_term_label(current_semester)
        income_year_current = get_income_year_for_semester(current_semester)

        st.markdown(f"### {current_label}")
        st.caption(f"Bruker årsinntekt år {income_year_current}: {format_nok(annual_incomes[income_year_current])}")

        lives_away_fall = st.selectbox(
            f"Bodd borte i {current_label}?",
            options=["Ja", "Nei"],
            index=0,
            key=f"away_sem_{current_semester}",
        )

        support_share_fall = st.slider(
            f"Andel støtte i {current_label}",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_sem_{current_semester}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    semester_number += 1

    # Vårsemester
    with col2:
        current_semester = semester_number
        current_label = get_term_label(current_semester)
        income_year_current = get_income_year_for_semester(current_semester)

        st.markdown(f"### {current_label}")
        st.caption(f"Bruker årsinntekt år {income_year_current}: {format_nok(annual_incomes[income_year_current])}")

        lives_away_spring = st.selectbox(
            f"Bodd borte i {current_label}?",
            options=["Ja", "Nei"],
            index=0,
            key=f"away_sem_{current_semester}",
        )

        support_share_spring = st.slider(
            f"Andel støtte i {current_label}",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_sem_{current_semester}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    year_support = 0.0
    year_stipend = 0.0
    year_loan = 0.0

    fall_semester_number = (year * 2) - 1
    spring_semester_number = year * 2

    semester_inputs = [
        (fall_semester_number, lives_away_fall, support_share_fall),
        (spring_semester_number, lives_away_spring, support_share_spring),
    ]

    for sem_num, lives_away, support_share in semester_inputs:
        annual_income_year = get_income_year_for_semester(sem_num)
        annual_income_used = annual_incomes[annual_income_year]
        semester_label = get_term_label(sem_num)

        actual_support = semester_basis_support * support_share

        if lives_away == "Ja":
            stipend_ratio = calculate_stipend_ratio(
                annual_income=annual_income_used,
                annual_threshold=annual_income_threshold,
                annual_full_loan_limit=annual_full_loan_limit,
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

        semester_rows.append(
            {
                "Studieår": year,
                "Semester": semester_label,
                "Bruker årsinntekt": f"År {annual_income_year}",
                "Årsinntekt brukt": annual_income_used,
                "Bodd borte": lives_away,
                "Støttegrad": support_share,
                "Mottatt støtte": actual_support,
                "Stipend": stipend_amount,
                "Lån fra basisstøtte": loan_amount,
            }
        )

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

    semester_number += 1

# -------------------------
# Resultater
# -------------------------
semester_df = pd.DataFrame(semester_rows)
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
            "Årsinntekt brukt": lambda x: format_nok(x),
            "Støttegrad": "{:.0%}",
            "Mottatt støtte": lambda x: format_nok(x),
            "Stipend": lambda x: format_nok(x),
            "Lån fra basisstøtte": lambda x: format_nok(x),
        }
    ),
    use_container_width=True,
)
   

        support_share_spring = st.slider(
            f"Andel støtte i {current_label}",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            key=f"support_sem_{current_semester}",
            help="1.0 = full støtte, 0.5 = halv støtte, 0 = ingen støtte",
        )

    year_support = 0.0
    year_stipend = 0.0
    year_loan = 0.0

    fall_semester_number = (year * 2) - 1
    spring_semester_number = year * 2

    semester_inputs = [
        (fall_semester_number, lives_away_fall, support_share_fall),
        (spring_semester_number, lives_away_spring, support_share_spring),
    ]

    for sem_num, lives_away, support_share in semester_inputs:
        annual_income_year = get_income_year_for_semester(sem_num)
        annual_income_used = annual_incomes[annual_income_year]
        semester_label = get_term_label(sem_num)

        actual_support = semester_basis_support * support_share

        if lives_away == "Ja":
            stipend_ratio = calculate_stipend_ratio(
                annual_income=annual_income_used,
                annual_threshold=annual_income_threshold,
                annual_full_loan_limit=annual_full_loan_limit,
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

        semester_rows.append(
            {
                "Studieår": year,
                "Semester": semester_label,
                "Bruker årsinntekt": f"År {annual_income_year}",
                "Årsinntekt brukt": annual_income_used,
                "Bodd borte": lives_away,
                "Støttegrad": support_share,
                "Mottatt støtte": actual_support,
                "Stipend": stipend_amount,
                "Lån fra basisstøtte": loan_amount,
            }
        )

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

    semester_number += 1

# -------------------------
# Resultater
# -------------------------
semester_df = pd.DataFrame(semester_rows)
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
            "Årsinntekt brukt": lambda x: format_nok(x),
            "Støttegrad": "{:.0%}",
            "Mottatt støtte": lambda x: format_nok(x),
            "Stipend": lambda x: format_nok(x),
            "Lån fra basisstøtte": lambda x: format_nok(x),
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
# Forutsetninger
# -------------------------
st.markdown("## Forutsetninger")
st.write(
    """
- Modellen antar at du består og fullfører på normert tid.
- Hvert studieår har et høstsemester og et vårsemester.
- Årsinntekt år 1 brukes kun på høstsemesteret i første studieår.
- Deretter brukes hver årsinntekt på vårsemesteret og høstsemesteret rundt samme kalenderår.
- Bor du hjemme i et semester, settes stipendandelen til 0 for det semesteret.
- Bor du borte, kan opptil 40 % av støtten bli stipend.
- Over inntektsgrensen trappes stipendandelen lineært ned til 0.
- Skolepenger legges inn per studieår og behandles som 100 % lån i denne modellen.
- Dette er en planleggingsmodell og ikke en eksakt kopi av Lånekassens beregning.
"""
)
