import streamlit as st
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="Arnestul", page_icon="🏔️")

# Information about Arnestul that the chatbot uses as context
ARNESTUL_INFO = """
Du er en kunnskapsrik guide for kurs- og feriestedet Arnestul. Du svarer alltid på norsk.
Når brukeren spør om stedet, bruk informasjonen nedenfor. Stedet heter Arnestul i alle
dine svar. Ikke nevn andre navn.

## Om Arnestul

Arnestul er et kurs- og feriested som eies av Norges Bank (sentralbanken). Det ligger på
Venabygdsfjellet ved Ringebu i Gudbrandsdalen. Eiendommen har vært eid av Norges Bank
siden 1960-tallet.

### Bruk og formål
- Stedet brukes til årlige konferanser, opplæring av ansatte og mottak av viktige gjester.
- Norges Bank driver utleie av rom til en døgnpris på 500 kroner.
- Ansatte og deres familier samt pensjonister i banken kan bruke og betale for opphold.
- Stedet benyttes til avdelingssamlinger, samlinger for nye ansatte og opphold for større
  ansattgrupper på tvers av banken.

### Økonomi og drift
- I løpet av de siste fem årene er det brukt 30,7 millioner kroner på drift av Arnestul.
- I tillegg er 6,4 millioner brukt på eiendomsprosjekter.
- Det er 3,6 faste årsverk på stedet, pluss noen timebetalte engasjementer.
- I 2023 var det rundt 4600 gjestedøgn, hvorav 300 var knyttet til kurs og konferanser.
- Norges Bank har hatt ni millioner kroner i inntekter fra utleie de siste fem årene.
- Bygningsmessig drift dekker lettere innvendig vedlikehold som maling og tømrerarbeid,
  samt serviceavtaler på brannutstyr, ventilasjon med mer.
- Det er også brukt penger på drenering rundt bygninger, oppgradering av uteområder,
  oppussing av bad og bygging av murer.

### Rapportering
- I Norges Banks årsrapporter ble eiendommen omtalt frem til 2011.
- Fra 2012 sluttet banken å føre opp eiendommen og utgiftene i årsrapportene.
- Representantskapet i Norges Bank er bankens budsjettmyndighet og følger med på
  bankens ressursbruk, inkludert faste eiendommer.

### Organisering
- Stedet er registrert med eget selskap i Brønnøysundregistrene under navnet
  «Norges Banks Feriested».
- Selskapet har åtte ansatte og sentralbanksjef Ida Wolden Bache står oppført som
  daglig leder.

### Vårseminarer
Siden 2010 har Norges Bank organisert årlige vårseminarer på Arnestul. Der arrangerer de
workshops der ansatte i banken presenterer sitt arbeid. Under seminaret kommer det også
inviterte gjester fra viktige institusjoner.

Gjester gjennom årene:
- 2010: Marco Del Negro (Federal Reserve Bank of New York)
- 2012: Anders Vredin (Sveriges Riksbank)
- 2013: Vincenzo Quadrini (University of Southern California)
- 2014: Jesper Lindé (Board of Governors of the Federal Reserve)
- 2015: Martin Eichenbaum (Northwestern University)
- 2016: Juan Rubio Ramirez (Emory University)
- 2017: James Stock (Harvard University)
- 2018: Egon Zakrajsek (Board of Governors of the Federal Reserve)
- 2019: Gianluca Violante (Princeton University)
- 2022: Annette Vissing-Jørgensen (Board of Governors of the Federal Reserve)
- 2023: Frank Smets (ECB)

### Norges Banks andre eiendom
Norges Bank eier også en eiendom ved Vindåsen på Tjøme, kjøpt i 1956 som feriested.
Siden mai 2013 brukes den kun til konferanser og er bare åpen om sommeren.
I 2023 var det rundt 900 gjestedøgn på Vindåsen.

Hvis du ikke vet svaret på et spørsmål, si at du ikke har informasjon om det,
og foreslå at brukeren kontakter Norges Bank for mer informasjon.
Vær vennlig, informativ og engasjerende i svarene dine. Svar alltid på norsk.
"""

# Show title and description
st.title("🏔️ Arnestul")
st.write(
    "Velkommen! Denne chatboten kan svare på spørsmål om kurs- og feriestedet "
    "Arnestul på Venabygdsfjellet ved Ringebu. Still et spørsmål for å lære mer "
    "om stedets historie, drift og bruk."
)

# Sidebar with quick facts
with st.sidebar:
    st.header("Om Arnestul")
    st.markdown(
        """
        **Kurs- og feriested**

        - **Beliggenhet:** Venabygdsfjellet, Ringebu
        - **Eier:** Norges Bank
        - **Eid siden:** 1960-tallet
        - **Pris:** 500 kr/døgn
        - **Gjestedøgn (2023):** ca. 4 600
        - **Ansatte:** 8 (3,6 årsverk fast)

        ---

        Stedet brukes til konferanser,
        kurs, opplæring og ferie for
        bankens ansatte og pensjonister.
        """
    )

# Ask user for their OpenAI API key via st.text_input.
openai_api_key = st.text_input("OpenAI API-nøkkel", type="password")
if not openai_api_key:
    st.info("Legg inn din OpenAI API-nøkkel for å starte chatboten.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via st.chat_message.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field.
    if prompt := st.chat_input("Still et spørsmål om Arnestul..."):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build messages with system prompt containing Arnestul info.
        api_messages = [{"role": "system", "content": ARNESTUL_INFO}]
        api_messages.extend(
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        )

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=api_messages,
            stream=True,
        )

        # Stream the response to the chat, then store it in session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
