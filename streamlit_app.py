import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
from journal_qa import parse_journal_xml, validate_entries, generate_statusrapport

st.set_page_config(page_title="Journal QA - Kvalitetssikring", layout="wide")

st.title("Kvalitetssikring av offentlig journal")
st.write(
    "Last opp offentlig journal i XML-format for kvalitetskontroll. "
    "Kontrollerer sakstitler, skjerming, hjemmel, kontaktinfo, datoer og sprak "
    "i henhold til Copilot-instruks v3.1."
)

uploaded_file = st.file_uploader("Last opp journal-XML", type=["xml"])

if uploaded_file is not None:
    try:
        tree = ET.parse(uploaded_file)
        entries = parse_journal_xml(tree)
    except ET.ParseError as e:
        st.error(f"Kunne ikke lese XML-filen: {e}")
        st.stop()

    if not entries:
        st.warning("Fant ingen journalposter i XML-filen. Sjekk at formatet er korrekt.")
        st.stop()

    findings = validate_entries(entries)
    rapport = generate_statusrapport(entries, findings)

    # --- 1. Sammendrag ---
    st.header("1. Sammendrag")
    if rapport["kan_publiseres"]:
        st.success(rapport["sammendrag"])
    else:
        st.error(rapport["sammendrag"])

    # --- 2. Nokkeltall ---
    st.header("2. Nokkeltall")
    nk = rapport["nokkeltall"]
    cols = st.columns(6)
    cols[0].metric("Poster", nk["antall_poster"])
    cols[1].metric("Avvik totalt", nk["antall_avvik"])
    cols[2].metric("Kritiske", nk["kritiske"])
    cols[3].metric("Hoye", nk["hoye"])
    cols[4].metric("Moderate", nk["moderate"])
    cols[5].metric("Lave", nk["lave"])

    # --- 3. Kontroll per punkt ---
    st.header("3. Kontroll per kontrollpunkt")

    kategorier = {
        "3.1 Titler": "Tittel",
        "3.3 Skjerming": "Skjerming",
        "3.4 Kontaktinfo": "Kontaktinfo",
        "3.6 Dato og forsinkelse": "Dato",
        "3.7 Fremmedsprak": "Sprak",
    }

    for label, kat in kategorier.items():
        kat_funn = [f for f in findings if f["avvikskategori"] == kat]
        with st.expander(f"{label} ({len(kat_funn)} avvik)", expanded=len(kat_funn) > 0):
            if not kat_funn:
                st.success("Ingen avvik funnet.")
            else:
                for f in kat_funn:
                    prio = f["prioritet"]
                    icon = {"Kritisk": "error", "Hoy": "error", "Moderat": "warning", "Lav": "info"}.get(prio, "info")
                    getattr(st, icon)(
                        f"**{f['regel']}** (Dok: {f['dokumentnummer']}, Prioritet: {prio})\n\n"
                        f"{f['beskrivelse']}\n\n"
                        f"*Anbefalt handling:* {f['anbefalt_handling']}"
                    )

    # --- 4. Avvikstabell ---
    st.header("4. Avvikstabell")

    if findings:
        avvik_data = []
        for f in findings:
            status = "Krever manuell vurdering" if f.get("manuell_vurdering") else "Apen"
            avvik_data.append({
                "Dokumentnr.": f["dokumentnummer"],
                "Type": f["avvikskategori"],
                "Avvikskategori": f["regel"],
                "Beskrivelse": f["beskrivelse"],
                "Skal rettes til": f["anbefalt_handling"],
                "Prioritet": f["prioritet"],
                "Risiko": f["risiko"],
                "Status": status,
            })
        df_avvik = pd.DataFrame(avvik_data)

        # Filter
        col1, col2 = st.columns(2)
        with col1:
            prio_filter = st.multiselect(
                "Filtrer pa prioritet",
                ["Kritisk", "Hoy", "Moderat", "Lav"],
                default=["Kritisk", "Hoy", "Moderat", "Lav"],
            )
        with col2:
            kat_filter = st.multiselect(
                "Filtrer pa kategori",
                df_avvik["Type"].unique().tolist(),
                default=df_avvik["Type"].unique().tolist(),
            )

        filtered = df_avvik[
            df_avvik["Prioritet"].isin(prio_filter) & df_avvik["Type"].isin(kat_filter)
        ]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    else:
        st.success("Ingen avvik funnet.")

    # --- 5. Flagg for manuell vurdering ---
    st.header("5. Flagg for manuell vurdering")
    manuelle = rapport["flagg_manuell_vurdering"]
    if manuelle:
        for m in manuelle:
            st.warning(
                f"**Dok {m['dokumentnummer']}**: {m['regel']} - {m['beskrivelse']}"
            )
    else:
        st.info("Ingen poster krever manuell vurdering.")

    # --- 6. Konklusjon ---
    st.header("6. Konklusjon")
    if rapport["kan_publiseres"]:
        st.success(
            "Journalen kan publiseres. "
            "Forutsetning: " + rapport["forutsetninger"]
        )
    else:
        st.error(
            "Journalen kan IKKE publiseres for avvik er rettet. "
            + rapport["forutsetninger"]
        )

    # --- Alle journalposter ---
    with st.expander("Vis alle journalposter"):
        df = pd.DataFrame(entries)
        display_cols = [c for c in [
            "dokumentnummer", "gradering", "unntatt_offentligheten",
            "sak", "dokumenttittel", "til_fra", "saksansvarlig",
        ] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

else:
    st.info("Last opp en XML-fil for a starte kvalitetskontrollen.")

    with st.expander("Forventet XML-format"):
        st.code("""<?xml version="1.0" encoding="UTF-8"?>
<journal>
  <periode fra="2026-02-09" til="2026-02-15"/>
  <post>
    <dokumentnummer>25/04495-2</dokumentnummer>
    <dokumentdato>09.02.2026</dokumentdato>
    <journaldato>10.02.2026</journaldato>
    <gradering>UO</gradering>
    <unntatt_offentligheten>Offl § 13 jf sbl § 5-2</unntatt_offentligheten>
    <retning>U</retning>
    <til_fra>Avskjermet</til_fra>
    <sak>Deponering i gjeldsforhold - Avskjermet</sak>
    <dokumenttittel>Deponering i gjeldsforhold - Avskjermet</dokumenttittel>
    <saksansvarlig>FIN Financial Reporting</saksansvarlig>
    <saksbehandler>FIN Financial Reporting</saksbehandler>
  </post>
</journal>""", language="xml")

    st.subheader("Kontrollpunkter (v3.1)")
    st.markdown("""
| Punkt | Kontroll | Beskrivelse |
|-------|----------|-------------|
| 3.1 | Titler | Skal vaere pa norsk/engelsk, uten personopplysninger eller sensitiv info |
| 3.2 | Sakstilhorighet | Dokument i korrekt sak og arkivdel |
| 3.3 | Skjerming | Hjemmel pa norsk, korrekt graderingsniva |
| 3.4 | Kontaktinfo | Avsender/mottaker skjermet i UO/F-poster |
| 3.5 | Elektronisk fil | Lesbar fil tilknyttet (krever arkivsystemtilgang) |
| 3.6 | Dato/forsinkelse | Dokumentdato utfylt, forsinkelse under kontroll |
| 3.7 | Fremmedsprak | Journaltekst pa norsk/engelsk, hjemler pa norsk |
""")

    st.subheader("Risikosaker - skjerpet kontroll")
    st.markdown("""
| Sakstype | Typisk feil | Kontrollpunkt |
|----------|-------------|---------------|
| Deponeringssaker | Avsender/mottaker ikke avskjermet | 3.4 |
| Tildelingsbrev, anskaffelser | Leverandornavn synlig i mottakerfeltet | 3.4 |
| Rekrutteringsposter fra HR | Engelsk hjemmel (FoIA, CBA) | 3.3 |
| Vekslingssoknader | Forsinket journalforing | 3.6 |
| Nordisk samarbeid | Svensk/annet fremmedsprak i tittel | 3.7 |
""")
