"""
Kvalitetssikring av offentlig journal - Norges Bank.
Copilot-instruks versjon 3.1.

Kontrollpunkter:
3.1 Titler
3.2 Sakstilhorighet
3.3 Skjerming
3.4 Kontaktinformasjon - avsender og mottaker
3.5 Elektronisk fil (kan ikke sjekkes via XML alene)
3.6 Dokumentdato og forsinkelse
3.7 Fremmedsprak
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# --- Hjemler ---

VALID_HJEMLER_NORSK = {
    "Offl § 13": "Teieplikt",
    "Offl § 14": "Organinterne dokument",
    "Offl § 15": "Dokument innhenta utenfra for intern saksforebuing",
    "Offl § 20": "Utenrikspolitiske omsyn",
    "Offl § 21": "Nasjonale forsvars- og tryggingsomsyn",
    "Offl § 22": "Budsjettsaker",
    "Offl § 23": "Omsyn til det offentlege sin forhandlingsposisjon m.m.",
    "Offl § 24": "Kontroll- og reguleringstiltak m.m.",
    "Offl § 25": "Tilsetjingssaker m.m.",
    "Offl § 26": "Eksamen, statlege prover m.m.",
    "sbl § 5-1": "Teieplikt - sentralbankloven",
    "Sbl § 5-1": "Teieplikt - sentralbankloven",
    "sbl § 5-2": "Teieplikt - sentralbankloven",
    "Sbl § 5-2": "Teieplikt - sentralbankloven",
    "Beskyttelsesinstruksen § 4": "Beskyttelsesgraderte dokument",
}

ENGELSKE_HJEMLER = {
    "FoIA": "Freedom of Information Act (skal vaere Offl)",
    "CBA": "Central Bank Act (skal vaere sbl)",
}

VALID_GRADERINGER = {"U", "UO", "F", "SH", "S", "H", "TH"}

RISIKOSAKER = {
    "deponering": "Deponeringssaker - sjekk at avsender/mottaker er avskjermet",
    "veksling": "Vekslingssaker - sjekk journalforingsforsinkelse",
    "tildeling": "Tildelingssaker - sjekk at leverandornavn er skjermet",
    "rekruttering": "Rekrutteringsposter - sjekk for engelsk hjemmel",
}


def parse_journal_xml(tree):
    """Parse journal XML and return list of entry dicts."""
    root = tree.getroot()
    entries = []
    for post in root.findall(".//post"):
        entry = {}
        for field in [
            "dokumentnummer", "dokumentdato", "journaldato",
            "gradering", "unntatt_offentligheten", "retning",
            "til_fra", "sak", "dokumenttittel",
            "saksansvarlig", "saksbehandler",
        ]:
            elem = post.find(field)
            entry[field] = elem.text.strip() if elem is not None and elem.text else ""
        entries.append(entry)
    return entries


def validate_entries(entries):
    """Run all validation rules. Returns list of findings."""
    findings = []
    for entry in entries:
        findings.extend(_check_titler(entry))
        findings.extend(_check_skjerming(entry))
        findings.extend(_check_kontaktinfo(entry))
        findings.extend(_check_dato_forsinkelse(entry))
        findings.extend(_check_fremmedsprak(entry))
    return findings


def generate_statusrapport(entries, findings):
    """Generate the status report as per v3.1 spec."""
    kritisk = [f for f in findings if f["prioritet"] == "Kritisk"]
    hoy = [f for f in findings if f["prioritet"] == "Hoy"]
    moderat = [f for f in findings if f["prioritet"] == "Moderat"]
    lav = [f for f in findings if f["prioritet"] == "Lav"]

    kan_publiseres = len(kritisk) == 0 and len(hoy) == 0

    rapport = {
        "sammendrag": _sammendrag(entries, findings, kan_publiseres),
        "nokkeltall": {
            "antall_poster": len(entries),
            "antall_avvik": len(findings),
            "kritiske": len(kritisk),
            "hoye": len(hoy),
            "moderate": len(moderat),
            "lave": len(lav),
        },
        "kan_publiseres": kan_publiseres,
        "forutsetninger": (
            "Ingen kritiske eller hoye avvik gjenstaar."
            if kan_publiseres
            else "Kritiske/hoye avvik ma handteres for publisering."
        ),
        "flagg_manuell_vurdering": [
            f for f in findings if f.get("manuell_vurdering", False)
        ],
    }
    return rapport


def _sammendrag(entries, findings, kan_publiseres):
    if not findings:
        return f"Kontrollert {len(entries)} journalposter. Ingen avvik funnet. Journalen kan publiseres."
    status = "kan publiseres" if kan_publiseres else "kan IKKE publiseres for avvik er rettet"
    return (
        f"Kontrollert {len(entries)} journalposter. "
        f"Funnet {len(findings)} avvik. Journalen {status}."
    )


# --- 3.1 Titler ---

_SENSITIVE_PATTERNS = [
    (r"\b\d{11}\b", "Mulig fodselsnummer i tittel"),
    (r"\b\d{6}\s?\d{5}\b", "Mulig fodselsnummer i tittel"),
    (r"\bNOK\s*[\d,.]+\s*(mill|mrd|tusen)?", "Mulig belopsinformasjon i tittel"),
    (r"\b\d+[\s,.]?\d*\s*(kroner|kr|NOK|USD|EUR|GBP)\b", "Mulig belopsinformasjon i tittel"),
    (r"\b[A-Z]{2}\d{5}\b", "Mulig registreringsnummer/ID i tittel"),
]

_COMMON_TYPOS = {
    "offenltigheten": "offentligheten",
    "offenligheten": "offentligheten",
    "departemetet": "departementet",
    "gjeldsfohold": "gjeldsforhold",
    "deponerign": "deponering",
    "vekslign": "veksling",
    "sentralabnkloven": "sentralbankloven",
}


def _check_titler(entry):
    findings = []
    dok = entry.get("dokumentnummer", "?")
    sak = entry.get("sak", "")
    tittel = entry.get("dokumenttittel", "")
    gradering = entry.get("gradering", "")
    unntak = entry.get("unntatt_offentligheten", "")

    # Tom sakstittel
    if not sak:
        findings.append(_avvik(
            dok, "Tittel", "Manglende sakstittel",
            "Journalposten mangler sakstittel.",
            "Personvern / Arkivintegritet",
            "Legg til beskrivende sakstittel.",
            "Hoy", sak,
        ))

    # Tom dokumenttittel
    if not tittel:
        findings.append(_avvik(
            dok, "Tittel", "Manglende dokumenttittel",
            "Journalposten mangler dokumenttittel.",
            "Arkivintegritet",
            "Legg til beskrivende dokumenttittel.",
            "Hoy", sak,
        ))

    # Tittel som bare er "Avskjermet" uten sakstype
    if sak.strip().lower() == "avskjermet":
        findings.append(_avvik(
            dok, "Tittel", "Sakstittel kun 'Avskjermet'",
            "Sakstittelen er kun 'Avskjermet' uten beskrivende tekst. "
            "Selv skjermede saker bor ha en generell beskrivelse av sakstypen.",
            "Offentlighet",
            "Legg til generell saksbeskrivelse for 'Avskjermet', f.eks. 'Deponering i gjeldsforhold - Avskjermet'.",
            "Moderat", sak,
        ))

    # Sensitiv informasjon i titler
    for text, label in [(sak, "sakstittel"), (tittel, "dokumenttittel")]:
        for pattern, desc in _SENSITIVE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                findings.append(_avvik(
                    dok, "Tittel", f"Sensitiv informasjon i {label}",
                    f"{desc}: '{match.group()}' funnet i {label}. "
                    "Skjermingsverdig informasjon skal ikke fremga av tittel.",
                    "Personvern",
                    f"Fjern sensitiv informasjon fra {label} og erstatt med 'Avskjermet'.",
                    "Kritisk", sak,
                    manuell=True,
                ))

    # Skrivefeil
    for text, label in [(sak, "sakstittel"), (tittel, "dokumenttittel")]:
        for typo, correct in _COMMON_TYPOS.items():
            if typo.lower() in text.lower():
                findings.append(_avvik(
                    dok, "Tittel", f"Skrivefeil i {label}",
                    f"Mulig skrivefeil i {label}: '{typo}' bor vaere '{correct}'.",
                    "Arkivintegritet",
                    f"Rett '{typo}' til '{correct}' i {label}.",
                    "Lav", sak,
                ))

    # Skjermingsverdig info i tittel pa UO-dokument
    if gradering in ("UO", "F") and unntak:
        is_taushetsplikt = ("§ 13" in unntak or "§ 5-2" in unntak or "CBA" in unntak)
        if is_taushetsplikt:
            # Sjekk om tittel avslorer innhold som burde vaere skjermet
            if "- Avskjermet" not in tittel and "avskjermet" not in tittel.lower():
                # Titler uten "Avskjermet"-markering pa taushetsbelagte dokumenter
                findings.append(_avvik(
                    dok, "Tittel", "Tittel pa taushetsbelagt dokument ikke markert",
                    f"Dokumenttittel '{tittel}' er ikke markert med 'Avskjermet' "
                    "til tross for teieplikthjemmel. Sjekk om tittelen avslorer skjermingsverdig info.",
                    "Personvern / Offentlighet",
                    "Vurder om tittelen avslorer taushetsbelagt informasjon. Legg evt. til '- Avskjermet'.",
                    "Moderat", sak,
                    manuell=True,
                ))

    return findings


# --- 3.3 Skjerming ---

def _check_skjerming(entry):
    findings = []
    dok = entry.get("dokumentnummer", "?")
    sak = entry.get("sak", "")
    gradering = entry.get("gradering", "")
    unntak = entry.get("unntatt_offentligheten", "")

    # Ugyldig gradering
    if gradering and gradering not in VALID_GRADERINGER:
        findings.append(_avvik(
            dok, "Skjerming", "Ugyldig gradering",
            f"Graderingen '{gradering}' er ikke en kjent graderingsverdi. "
            f"Gyldige verdier: {', '.join(sorted(VALID_GRADERINGER))}.",
            "Arkivintegritet",
            "Korriger graderingsverdien.",
            "Kritisk", sak,
        ))

    # Manglende gradering
    if not gradering:
        findings.append(_avvik(
            dok, "Skjerming", "Manglende gradering",
            "Journalposten mangler graderingsverdi.",
            "Arkivintegritet",
            "Legg til graderingsverdi (U, UO, F, etc.).",
            "Kritisk", sak,
        ))

    # UO/F uten hjemmel
    if gradering in ("UO", "F", "SH", "S", "H", "TH") and not unntak:
        findings.append(_avvik(
            dok, "Skjerming", "Manglende hjemmel ved gradering",
            f"Dokumentet har gradering '{gradering}' men mangler hjemmel for unntak fra offentligheten.",
            "Offentlighet",
            "Legg til korrekt hjemmel for unntak.",
            "Kritisk", sak,
        ))

    # Hjemmel pa apent dokument
    if unntak and gradering == "U":
        findings.append(_avvik(
            dok, "Skjerming", "Hjemmel pa ugradert dokument",
            f"Dokumentet er gradert 'U' (ugradert) men har unntakshjemmel: '{unntak}'.",
            "Offentlighet",
            "Fjern unntakshjemmel eller endre gradering til UO/F.",
            "Kritisk", sak,
        ))

    # Engelsk hjemmel (3.3 - skyldes ofte feil i HR-systemintegrasjon)
    if unntak:
        for eng_ref, desc in ENGELSKE_HJEMLER.items():
            if eng_ref in unntak:
                norsk = unntak
                norsk = norsk.replace("FoIA", "Offl").replace("CBA", "sbl")
                findings.append(_avvik(
                    dok, "Skjerming", "Engelsk hjemmel",
                    f"Hjemmel er oppgitt pa engelsk: '{unntak}'. {desc}. "
                    "Skjermingshjemler skal alltid vaere pa norsk.",
                    "Arkivintegritet",
                    f"Endre til norsk hjemmel: '{norsk}'.",
                    "Hoy", sak,
                ))
                break

    # Valider hjemmelreferanse
    if unntak and gradering != "U":
        has_valid = False
        for key in VALID_HJEMLER_NORSK:
            if key.lower() in unntak.lower():
                has_valid = True
                break
        for key in ENGELSKE_HJEMLER:
            if key in unntak:
                has_valid = True
                break
        if "beskyttelsesinstruksen" in unntak.lower():
            has_valid = True
        if not has_valid:
            findings.append(_avvik(
                dok, "Skjerming", "Ukjent hjemmelreferanse",
                f"Hjemmelen '{unntak}' inneholder ingen kjent lovhenvisning.",
                "Offentlighet",
                "Sjekk og korriger hjemmelhenvisningen.",
                "Kritisk", sak,
                manuell=True,
            ))

    return findings


# --- 3.4 Kontaktinformasjon ---

def _check_kontaktinfo(entry):
    findings = []
    dok = entry.get("dokumentnummer", "?")
    sak = entry.get("sak", "")
    gradering = entry.get("gradering", "")
    unntak = entry.get("unntatt_offentligheten", "")
    til_fra = entry.get("til_fra", "")
    retning = entry.get("retning", "")

    if gradering not in ("UO", "F", "SH", "S", "H", "TH"):
        return findings

    if not til_fra:
        return findings

    er_avskjermet = "avskjermet" in til_fra.lower()

    if er_avskjermet:
        return findings

    # Deponeringssaker
    is_deponering = "deponering" in sak.lower()
    if is_deponering:
        findings.append(_avvik(
            dok, "Kontaktinfo", "Avsender/mottaker ikke avskjermet i deponeringssak",
            f"Deponeringssak har synlig avsender/mottaker: '{til_fra}'. "
            "I deponeringssaker skal avsender/mottaker alltid vaere avskjermet.",
            "Personvern",
            "Skjerm avsender/mottaker-feltet.",
            "Kritisk", sak,
        ))
        return findings

    # Anskaffelsessaker / tildelingsbrev (offl § 23)
    is_anskaffelse = "§ 23" in unntak
    if is_anskaffelse:
        findings.append(_avvik(
            dok, "Kontaktinfo", "Leverandornavn synlig i anskaffelsessak",
            f"Anskaffelsessak (Offl § 23) har synlig mottaker: '{til_fra}'. "
            "Leverandornavn skal ikke vaere synlig i mottakerfeltet for tildelingsbrev.",
            "Offentlighet",
            "Skjerm mottakerfeltet.",
            "Kritisk", sak,
        ))
        return findings

    # Vekslingssaker, personalsaker og andre UO-saker med teieplikt
    is_taushetsplikt = ("§ 13" in unntak or "§ 5-2" in unntak or "CBA" in unntak)
    if is_taushetsplikt:
        findings.append(_avvik(
            dok, "Kontaktinfo", "Avsender/mottaker ikke avskjermet ved teieplikt",
            f"Dokumentet er unntatt med teieplikthjemmel ({unntak}), "
            f"men avsender/mottaker '{til_fra}' er ikke avskjermet.",
            "Personvern",
            "Skjerm avsender/mottaker-feltet.",
            "Hoy", sak,
        ))

    return findings


# --- 3.6 Dokumentdato og forsinkelse ---

def _check_dato_forsinkelse(entry):
    findings = []
    dok = entry.get("dokumentnummer", "?")
    sak = entry.get("sak", "")
    dok_dato_str = entry.get("dokumentdato", "")
    journal_dato_str = entry.get("journaldato", "")

    # Manglende dokumentdato
    if not dok_dato_str:
        findings.append(_avvik(
            dok, "Dato", "Manglende dokumentdato",
            "Dokumentdatofeltet er ikke utfylt.",
            "Arkivintegritet",
            "Legg til dokumentdato.",
            "Hoy", sak,
        ))

    # Manglende journaldato
    if not journal_dato_str:
        findings.append(_avvik(
            dok, "Dato", "Manglende journaldato",
            "Journalposten mangler journaldato.",
            "Arkivintegritet",
            "Legg til journaldato.",
            "Kritisk", sak,
        ))

    if not dok_dato_str or not journal_dato_str:
        return findings

    try:
        d_dato = datetime.strptime(dok_dato_str, "%d.%m.%Y")
        j_dato = datetime.strptime(journal_dato_str, "%d.%m.%Y")
    except ValueError:
        findings.append(_avvik(
            dok, "Dato", "Ugyldig datoformat",
            f"Kunne ikke tolke dato. Dokumentdato: '{dok_dato_str}', "
            f"Journaldato: '{journal_dato_str}'. Forventet: DD.MM.YYYY.",
            "Arkivintegritet",
            "Korriger datoformat til DD.MM.YYYY.",
            "Hoy", sak,
        ))
        return findings

    # Journaldato for dokumentdato
    if j_dato < d_dato:
        findings.append(_avvik(
            dok, "Dato", "Journaldato for dokumentdato",
            f"Journaldato ({journal_dato_str}) er for dokumentdato ({dok_dato_str}). "
            "Journalforing skal normalt skje etter at dokumentet er mottatt/sendt.",
            "Arkivintegritet",
            "Sjekk om dokumentdato eller journaldato er feil.",
            "Moderat", sak,
        ))

    # Forsinkelse
    diff_days = (j_dato - d_dato).days
    if diff_days > 56:  # Over 8 uker
        findings.append(_avvik(
            dok, "Dato", "Kritisk forsinket journalforing",
            f"Det er {diff_days} dager ({diff_days // 7} uker) mellom dokumentdato "
            f"({dok_dato_str}) og journaldato ({journal_dato_str}). "
            "Over 8 ukers forsinkelse er kritisk.",
            "Arkivintegritet",
            "Undersok arsaken til forsinket journalforing.",
            "Kritisk", sak,
        ))
    elif diff_days > 28:  # Over 4 uker
        findings.append(_avvik(
            dok, "Dato", "Forsinket journalforing",
            f"Det er {diff_days} dager ({diff_days // 7} uker) mellom dokumentdato "
            f"({dok_dato_str}) og journaldato ({journal_dato_str}). "
            "Over 4 ukers forsinkelse er moderat avvik.",
            "Arkivintegritet",
            "Undersok arsaken til forsinket journalforing.",
            "Moderat", sak,
        ))

    # Feil arstall (f.eks. 2025 i en serie ellers datert 2026)
    dok_year = d_dato.year
    journal_year = j_dato.year
    if journal_year - dok_year > 1:
        findings.append(_avvik(
            dok, "Dato", "Mulig feil arstall",
            f"Dokumentdato ({dok_dato_str}) er over ett ar for journaldato ({journal_dato_str}). "
            "Sjekk om arstallet er korrekt.",
            "Arkivintegritet",
            "Verifiser at dokumentdato er korrekt.",
            "Moderat", sak,
            manuell=True,
        ))

    return findings


# --- 3.7 Fremmedsprak ---

_SVENSKE_ORD = [
    "och", "eller", "ang", "angaende", "forslag", "beslut",
    "styrelsen", "rapportering", "myndigheten",
]

_TYSKE_ORD = ["und", "oder", "bitte", "danke", "bezuglich"]


def _check_fremmedsprak(entry):
    findings = []
    dok = entry.get("dokumentnummer", "?")
    sak = entry.get("sak", "")
    tittel = entry.get("dokumenttittel", "")
    unntak = entry.get("unntatt_offentligheten", "")

    # Sjekk hjemmel for engelsk (allerede dekket i _check_skjerming,
    # men vi flagger ogsa her under sprakregler)
    # Ikke dupliser - dekkes av _check_skjerming

    # Sjekk titler for fremmedsprak (utover norsk/engelsk)
    for text, label in [(sak, "sakstittel"), (tittel, "dokumenttittel")]:
        text_lower = text.lower()
        words = text_lower.split()
        # Enkel sjekk for svensk
        swedish_matches = [w for w in _SVENSKE_ORD if w in words]
        if len(swedish_matches) >= 2:
            findings.append(_avvik(
                dok, "Sprak", f"Mulig svensk tekst i {label}",
                f"{label} inneholder mulige svenske ord: {', '.join(swedish_matches)}. "
                "Internt generert journaltekst skal vaere pa norsk eller engelsk.",
                "Arkivintegritet",
                f"Oversett {label} til norsk eller engelsk, med mindre det er egennavn.",
                "Moderat", sak,
                manuell=True,
            ))

    return findings


# --- Avviksformat ---

def _avvik(dok, kategori, beskrivelse_kort, beskrivelse, risiko, anbefalt_handling,
           prioritet, sak, manuell=False):
    return {
        "dokumentnummer": dok,
        "avvikskategori": kategori,
        "regel": beskrivelse_kort,
        "beskrivelse": beskrivelse,
        "risiko": risiko,
        "anbefalt_handling": anbefalt_handling,
        "prioritet": prioritet,
        "sak": sak,
        "manuell_vurdering": manuell,
        # For bakoverkompatibilitet
        "alvorlighet": _prioritet_til_alvorlighet(prioritet),
    }


def _prioritet_til_alvorlighet(prioritet):
    return {
        "Kritisk": "Feil",
        "Hoy": "Feil",
        "Moderat": "Advarsel",
        "Lav": "Info",
    }.get(prioritet, "Info")
