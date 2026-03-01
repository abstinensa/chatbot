import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Norges Bank – Deponering i gjeldsforhold",
    page_icon="🏦",
    layout="centered",
)

# --- Session state defaults ---
if "steg" not in st.session_state:
    st.session_state.steg = "hjem"
if "skjema" not in st.session_state:
    st.session_state.skjema = {}


def gaa_til(side: str):
    st.session_state.steg = side


# --- Sidebar navigation ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Norges_Bank.svg/200px-Norges_Bank.svg.png", width=160)
    st.markdown("### Navigasjon")
    if st.button("Hjem", use_container_width=True):
        gaa_til("hjem")
    if st.button("Søk om deponering", use_container_width=True):
        gaa_til("deponering")
    if st.button("Søk om utbetaling", use_container_width=True):
        gaa_til("utbetaling_valg")
    st.divider()
    st.caption("Norges Bank – Deponering i gjeldsforhold")
    st.caption("Postboks 1179 Sentrum, 0107 Oslo")
    st.caption("E-post: post@norges-bank.no")


# ============================================================
# HOME PAGE
# ============================================================
if st.session_state.steg == "hjem":
    st.title("🏦 Deponering i gjeldsforhold")
    st.markdown(
        """
        Deponering i gjeldsforhold er en ordning der en skyldner som ikke får
        gjennomført betaling av gjelden sin, kan fri seg fra gjelden ved å
        overføre penger eller verdipapirer til Norges Bank.

        ---

        **Hva ønsker du å gjøre?**
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Deponere midler")
        st.markdown("Overfør penger eller verdipapirer til Norges Bank for å fri deg fra gjeld.")
        if st.button("Søk om deponering →", use_container_width=True, type="primary"):
            gaa_til("deponering")
            st.rerun()

    with col2:
        st.markdown("#### Utbetaling av midler")
        st.markdown("Søk om å få utbetalt midler som er deponert i Norges Bank.")
        if st.button("Søk om utbetaling →", use_container_width=True, type="primary"):
            gaa_til("utbetaling_valg")
            st.rerun()

    st.divider()
    with st.expander("Hva betyr deponering i gjeldsforhold?"):
        st.markdown(
            """
            Når en skyldner ikke får betalt gjelden sin – for eksempel fordi
            kreditor nekter å ta imot betaling, eller det er uklart hvem som
            er rett kreditor – kan skyldneren deponere beløpet i Norges Bank.
            Deponeringen har da samme virkning som betaling.
            """
        )
    with st.expander("Hva skjer med midlene som er deponert?"):
        st.markdown(
            """
            Midlene oppbevares av Norges Bank inntil rett mottaker søker om
            utbetaling. Norges Bank utbetaler midlene til den som kan
            dokumentere at de har krav på dem.
            """
        )


# ============================================================
# DEPOSIT APPLICATION (Søk om deponering)
# ============================================================
elif st.session_state.steg == "deponering":
    st.title("📋 Søk om deponering")
    st.markdown("Fyll ut skjemaet nedenfor for å søke om deponering av midler i Norges Bank.")

    dep_type = st.radio(
        "Hvilken type deponering gjelder det?",
        ["Eiendomsmidler", "Andre midler (penger, verdipapirer, m.m.)"],
    )

    st.divider()

    with st.form("deponering_skjema"):
        st.subheader("1. Om søker")
        soker_type = st.selectbox("Søker som", ["Privatperson", "Virksomhet"])

        col1, col2 = st.columns(2)
        with col1:
            navn = st.text_input("Fullt navn *")
            telefon = st.text_input("Telefonnummer *")
        with col2:
            adresse = st.text_input("Postadresse *")
            epost = st.text_input("E-postadresse")

        if soker_type == "Virksomhet":
            col1, col2 = st.columns(2)
            with col1:
                org_nr = st.text_input("Organisasjonsnummer *")
            with col2:
                kontaktperson = st.text_input("Kontaktperson *")

        st.divider()
        st.subheader("2. Om deponeringen")

        if dep_type == "Eiendomsmidler":
            eiendomsmegler = st.text_input("Eiendomsmegler / meglerforetak *")

        belop = st.text_input("Beløp som skal deponeres (NOK) *")
        bakgrunn = st.text_area(
            "Bakgrunn og begrunnelse for deponeringen *",
            height=120,
            placeholder="Beskriv hvorfor du ønsker å deponere midlene...",
        )

        st.divider()
        st.subheader("3. Om kreditor (mottaker)")
        kreditor_navn = st.text_input("Kreditors navn (om kjent)")
        kreditor_adresse = st.text_input("Kreditors adresse (om kjent)")

        st.divider()
        st.subheader("4. Vedlegg")
        legitimasjon = st.file_uploader(
            "Last opp kopi av gyldig legitimasjon *",
            type=["pdf", "jpg", "png"],
        )
        dokumentasjon = st.file_uploader(
            "Last opp annen relevant dokumentasjon",
            type=["pdf", "jpg", "png"],
            accept_multiple_files=True,
        )

        st.divider()
        bekreft = st.checkbox("Jeg bekrefter at opplysningene er korrekte")
        submitted = st.form_submit_button("Send inn søknad", type="primary", use_container_width=True)

        if submitted:
            feil = []
            if not navn:
                feil.append("Fullt navn")
            if not telefon:
                feil.append("Telefonnummer")
            if not adresse:
                feil.append("Postadresse")
            if not belop:
                feil.append("Beløp")
            if not bakgrunn:
                feil.append("Bakgrunn og begrunnelse")
            if not legitimasjon:
                feil.append("Legitimasjon")
            if not bekreft:
                feil.append("Bekreftelse")

            if feil:
                st.error(f"Vennligst fyll ut følgende obligatoriske felt: {', '.join(feil)}")
            else:
                st.session_state.skjema = {
                    "type": "deponering",
                    "dep_type": dep_type,
                    "navn": navn,
                    "telefon": telefon,
                    "adresse": adresse,
                    "epost": epost,
                    "belop": belop,
                    "bakgrunn": bakgrunn,
                    "dato": str(date.today()),
                }
                st.session_state.steg = "kvittering"
                st.rerun()


# ============================================================
# PAYOUT TYPE SELECTION (Velg type utbetaling)
# ============================================================
elif st.session_state.steg == "utbetaling_valg":
    st.title("💰 Søk om utbetaling")
    st.markdown("Velg hvilken type deponerte midler du ønsker utbetalt:")

    typer = {
        "eiendom": {
            "tittel": "Eiendomsmidler",
            "ikon": "🏠",
            "beskrivelse": "Midler deponert i forbindelse med eiendomstransaksjon.",
        },
        "bank": {
            "tittel": "Bankinnskudd",
            "ikon": "🏧",
            "beskrivelse": "Bankinnskudd som er overført til Norges Bank.",
        },
        "fond": {
            "tittel": "Fondsandeler",
            "ikon": "📈",
            "beskrivelse": "Fondsandeler deponert i Norges Bank.",
        },
        "vps": {
            "tittel": "Verdipapirer i VPS",
            "ikon": "📊",
            "beskrivelse": "Verdipapirer registrert i Verdipapirsentralen.",
        },
        "annet": {
            "tittel": "Andre deponeringer",
            "ikon": "📁",
            "beskrivelse": "Alle andre typer deponerte midler.",
        },
    }

    for key, info in typer.items():
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{info['ikon']} {info['tittel']}**")
                st.caption(info["beskrivelse"])
            with col2:
                if st.button("Velg", key=f"velg_{key}", use_container_width=True):
                    st.session_state.skjema["utbetaling_type"] = key
                    gaa_til("utbetaling_skjema")
                    st.rerun()


# ============================================================
# PAYOUT APPLICATION FORM (Utbetalingsskjema)
# ============================================================
elif st.session_state.steg == "utbetaling_skjema":
    utype = st.session_state.skjema.get("utbetaling_type", "annet")

    titler = {
        "eiendom": "Utbetaling av deponerte eiendomsmidler",
        "bank": "Utbetaling av deponerte bankinnskudd",
        "fond": "Utbetaling av deponerte fondsandeler",
        "vps": "Overføring av deponerte verdipapirer i VPS",
        "annet": "Utbetaling av andre deponeringer",
    }

    st.title(f"📝 {titler[utype]}")

    if st.button("← Tilbake til valg av type"):
        gaa_til("utbetaling_valg")
        st.rerun()

    st.divider()

    with st.form("utbetaling_skjema"):
        st.subheader("1. Om søker")
        soker_type = st.selectbox("Søker som", ["Privatperson", "Virksomhet"])

        col1, col2 = st.columns(2)
        with col1:
            navn = st.text_input("Fullt navn *")
            telefon = st.text_input("Telefonnummer *")
        with col2:
            adresse = st.text_input("Postadresse *")
            epost = st.text_input("E-postadresse")

        if soker_type == "Privatperson":
            personnr = st.text_input("Personnummer (11 siffer) *")
        else:
            col1, col2 = st.columns(2)
            with col1:
                org_nr = st.text_input("Organisasjonsnummer *")
            with col2:
                kontaktperson = st.text_input("Kontaktperson *")

        st.divider()
        st.subheader("2. Om deponeringen")

        deponerings_ref = st.text_input(
            "Deponeringskontonummer eller saksreferanse (om kjent)",
            placeholder="Fyll inn om du har denne informasjonen",
        )

        # Type-specific fields
        if utype == "eiendom":
            eiendomsmegler = st.text_input("Hvilken eiendomsmegler deponerte midlene? *")
        elif utype == "bank":
            bank_navn = st.text_input("Hvilken bank hadde du innskudd hos? *")
        elif utype == "fond":
            fond_inst = st.text_input("Hvilken finansinstitusjon hadde du fondsandeler hos? *")
        elif utype == "vps":
            vps_deponent = st.text_input("Hvem har deponert verdipapirene? *")
            vps_konto = st.text_input("VPS-kontonummer *")
        else:
            deponent = st.text_input("Hvem har deponert midlene? *")

        st.divider()
        st.subheader("3. Utbetalingsinformasjon")

        kontonummer = st.text_input(
            "Kontonummer for utbetaling *",
            placeholder="11 siffer",
        )

        if utype in ("eiendom", "annet"):
            bakgrunn = st.text_area(
                "Bakgrunn og begrunnelse for søknad om utbetaling *",
                height=100,
            )

        st.divider()
        st.subheader("4. Vedlegg")

        legitimasjon = st.file_uploader(
            "Kopi av gyldig legitimasjon *",
            type=["pdf", "jpg", "png"],
        )

        if utype == "eiendom":
            st.markdown("**Last opp ett av følgende:**")
            avtale = st.file_uploader(
                "Avtale mellom partene eller rettsgyldig dom",
                type=["pdf", "jpg", "png"],
            )
        elif utype == "annet":
            st.markdown("**Relevant dokumentasjon (om aktuelt):**")
            doc_type = st.multiselect(
                "Type dokumentasjon",
                ["Skifteattest / uskifteattest", "Avtale mellom partene", "Rettsgyldig dom", "Annet"],
            )
            ekstra_docs = st.file_uploader(
                "Last opp dokumentasjon",
                type=["pdf", "jpg", "png"],
                accept_multiple_files=True,
            )

        st.divider()
        bekreft = st.checkbox("Jeg bekrefter at opplysningene er korrekte")
        submitted = st.form_submit_button("Send inn søknad", type="primary", use_container_width=True)

        if submitted:
            feil = []
            if not navn:
                feil.append("Fullt navn")
            if not telefon:
                feil.append("Telefonnummer")
            if not adresse:
                feil.append("Postadresse")
            if not kontonummer:
                feil.append("Kontonummer for utbetaling")
            if not legitimasjon:
                feil.append("Legitimasjon")
            if not bekreft:
                feil.append("Bekreftelse")
            if soker_type == "Privatperson" and not personnr:
                feil.append("Personnummer")

            if feil:
                st.error(f"Vennligst fyll ut følgende obligatoriske felt: {', '.join(feil)}")
            else:
                st.session_state.skjema.update({
                    "type": "utbetaling",
                    "utbetaling_type": utype,
                    "navn": navn,
                    "telefon": telefon,
                    "adresse": adresse,
                    "kontonummer": kontonummer,
                    "dato": str(date.today()),
                })
                st.session_state.steg = "kvittering"
                st.rerun()


# ============================================================
# CONFIRMATION / RECEIPT (Kvittering)
# ============================================================
elif st.session_state.steg == "kvittering":
    skjema = st.session_state.skjema
    er_deponering = skjema.get("type") == "deponering"

    st.balloons()
    st.title("✅ Søknad mottatt")
    st.success("Takk! Din søknad er registrert og vil bli behandlet av Norges Bank.")

    st.divider()
    st.subheader("Oppsummering")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Søknadstype:** {'Deponering' if er_deponering else 'Utbetaling'}")
        st.markdown(f"**Navn:** {skjema.get('navn', '-')}")
        st.markdown(f"**Telefon:** {skjema.get('telefon', '-')}")
    with col2:
        st.markdown(f"**Dato:** {skjema.get('dato', '-')}")
        st.markdown(f"**Adresse:** {skjema.get('adresse', '-')}")
        if skjema.get("kontonummer"):
            st.markdown(f"**Utbetalingskonto:** {skjema.get('kontonummer')}")

    st.divider()
    st.info(
        "**Hva skjer videre?**\n\n"
        "1. Du vil motta en bekreftelse på e-post eller brev.\n"
        "2. Norges Bank behandler søknaden din.\n"
        "3. Du blir kontaktet dersom vi trenger mer informasjon.\n\n"
        "Merk: Saksbehandlingstiden kan være lang på grunn av stor pågang av saker.",
        icon="ℹ️",
    )

    if st.button("← Tilbake til forsiden", type="primary"):
        st.session_state.steg = "hjem"
        st.session_state.skjema = {}
        st.rerun()
