# UDKAST - Overordnede use cases / business cases for metadataordbogen (FDA)

## Fælles forudsætninger

Følgende gælder på tværs af alle use cases og gentages ikke under de enkelte:

- Ordbogen indeholder kuraterede RDF-elementer med stabile URI'er, danske betegnelser, definitioner og anvendelsesvejledning i en dansk myndighedskontekst.
- Ordbogen indeholder forretningsbegreber leveret af dataejere og repræsenteret med SKOS.
- Relationer mellem elementer er eksplicitte, herunder ækvivalens, snævrere og bredere begreber samt relationer til internationale og europæiske vokabularer.
- Indholdet vedligeholdes løbende af en redaktionsgruppe efter fastlagte kriterier for optagelse, ændring og afvisning.
- Ordbogen er tilgængelig både for mennesker og maskinelt.

Derudover gælder det for alle use cases, at værdien stiger efterhånden som ordbogen vokser og indeholder flere begreber og dataelementer, samt efterhånden som flere datakilder bliver mappet til den. Især UC6 om fødereret søgning kræver at mange datakilder er mappet til ordbogen.

---

## UC1: Anvende begreber ensartet på tværs af domæner

**Primær aktør:** Lovskriver, forretningsudvikler eller standardiseringsansvarlig

**Øvrige interessenter:** Modellører og systemudviklere, der senere skal implementere det, aktøren beskriver

**Situation i dag:** Samme ord bruges om forskellige begreber, og samme begreb kaldes forskellige ting i forskellige domæner, reguleringeren og organisationer. Det er en kilde til misforståelser og forvirring i sig selv, og det gør systemunderstøttelsen sværere, fordi det ikke uden videre kan afgøres, om to datasæt handler om det samme. 

**Mål:** At genbruge etablerede begreber og termer, således at der over tid kommer ensartet brug i forskellig og at når det ikke er muligt, så forskellene velforståde og dokumenterede.

**Forløb:**

1. Aktøren skal beskrive eller regulere noget, der involverer et fagbegreb.
2. Aktøren slår begrebet op i ordbogen og ser den autoritative definition samt hvilke andre domæner der anvender det.
3. Aktøren ser, om der findes homonymer eller synonymer, altså om ordet allerede bruges om noget andet, eller om samme betydning allerede har en anden betegnelse.
4. Aktøren anvender et etableret begreb, når det er muligt eller dokumenterer forskellen.

**Forudsætninger:**

- Definitioner, der kan læses og vurderes af ikke-teknikere.
- Synlighed af homonymer og synonymer, ikke kun af det enkelte opslag.
- Oplysning om, hvilke domæner og myndigheder der anvender begrebet.

**Værdi:** Færre begrebsmæssige misforståelser mellem forretning, jura og it, og en tidligere afklaring af, om data fra forskellige kilder kan bruges sammen. Ensartet begrebsbrug tidligt i lovgivnings- og udviklingsarbejdet er billigere end kortlægning og oversættelse senere.

**Opfyldt når:** En ikke-teknisk medarbejder kan slå et fagbegreb op og på den baggrund afgøre, om det bruges med samme betydning i et andet domæne.

---

## UC2: Etablere dataintegrationer hurtigere og mere sikkert

**Primær aktør:** Integrationsansvarlig eller udvikler, der skal koble to datakilder

**Øvrige interessenter:** Dataejere for begge kilder, den forretning der skal bruge det sammenstillede data

**Situation i dag:** Semantisk interoperabilitet etableres i dag typisk med manuelle og ressourcekrævende processer. Vurderingen af, om to felter i to systemer betyder det samme, laves fra sag til sag, ofte på baggrund af feltnavne og fritekstdokumentation. Arbejdet dokumenteres sjældent på en måde, der kan genbruges ved næste integration, og fejlfortolkninger opdages først i drift.

**Mål:** Hurtigt og med dokumenteret sikkerhed at afgøre, om data fra to kilder kan sammenstilles eller udveksles, og hvor der skal tages forbehold.

**Forløb:**

1. Integrationsansvarlig undersøger to datakilder, der skal kobles.
2. Er begge mappet til ordbogen, sammenholdes deres mapninger, og det fremgår, hvilke elementer der er ækvivalente, hvilke der er beslægtede, og hvor der er reelle betydningsforskelle.
3. Er kun den ene kilde mappet, mapper den integrationsansvarlige den anden. Det giver både den aktuelle sammenligning og en dokumentation, der kan genbruges næste gang den kilde skal integreres med noget andet.
4. Integrationen bygges på et dokumenteret grundlag, og forbehold fremgår eksplicit i stedet for at være underforståede.

**Forudsætninger:**

- Mulighed for at registrere og fremsøge mapninger mellem datakilders elementer og ordbogens elementer.
- Relationstyper, der kan udtrykke andet end fuld ækvivalens, så delvise sammenfald kan dokumenteres frem for at blive rundet op eller ned.
- Relationer fra ordbogens elementer til internationale og europæiske vokabularer, så en dansk mapning også kan bruges i grænseoverskridende sammenhænge.

**Værdi:** Mapningsarbejdet bliver en investering i stedet for en engangsomkostning, fordi hver mapning gør de næste billigere. Risikoen for at sammenstille data, der kun tilsyneladende handler om det samme, reduceres. Opfyldelse af krav til grænseoverskridende interoperabilitet lettes for data der gennem mapning til ordbogen er koblet til vokabularer anvendt i EU-sammenhæng.

**Opfyldt når:** To mappede datakilder kan sammenholdes gennem ordbogen, og den integrationsansvarlige kan på det grundlag pege på både de elementer der kan sammenstilles direkte, og de elementer der kræver forbehold.

---

## UC3: Give AI-løsninger og automatisering et autoritativt begrebsgrundlag

**Primær aktør:** Udvikler eller forretningsejer af en AI-assistent eller en automatiseret databehandling

**Øvrige interessenter:** Myndighedens ledelse, revision og tilsyn, borgere og virksomheder der berøres af automatiserede afgørelser

**Situation i dag:** AI-assistenter og automatiserede løsninger, der arbejder på tværs af datakilder, må udlede betydning af feltnavne, fritekst og statistiske sammenhænge. Det gør løsningerne dyrere at udvikle, sværere at vedligeholde og mere usikre i drift, og det gør det vanskeligt at redegøre for, hvorfor en løsning har fortolket data som den har.

**Mål:** At basere en AI- eller automatiseringsløsning på et stabilt, autoritativt begrebsgrundlag i stedet for på løsningens egne fortolkninger.

**Forløb:**

1. Løsningen skal anvende data fra en eller flere kilder.
2. Løsningen slår op i ordbogen og henter definitioner, relationer og mapninger maskinelt.
3. Datafortolkningen sker på grundlag af det publicerede begrebsgrundlag, med stabile URI'er, der kan refereres.
4. Ændringer i begreber kan følges, så løsningen ikke stille og roligt kommer til at bygge på en forældet fortolkning.

**Forudsætninger:**

- Maskinel adgang til ordbogens indhold.
- Stabile, versionerede URI'er og synlig ændringshistorik.
- Kvalitet og dækning, der er høj nok til, at en automatiseret løsning kan bygge på indholdet uden manuel kontrol i hvert tilfælde.

**Værdi:** Billigere udvikling og vedligehold af AI-løsninger, mere forudsigelig drift og bedre mulighed for at redegøre for, hvordan data er fortolket. Det er også den use case, der ældes bedst: efterspørgslen efter autoritative, maskinlæsbare metadata stiger, i takt med at flere løsninger automatiseres.

**Opfyldt når:** En automatiseret løsning kan hente definitioner og mapninger direkte fra ordbogen og henvise til det anvendte begreb med en stabil reference.

---

## UC4: Finde og genbruge begreber og dataelementer i modelarbejde

**Primær aktør:** Begrebs-, informations- eller datamodellør

**Øvrige interessenter:** Projektejer, arkitekter, kommende anvendere af modellen

**Situation i dag:** Modellører skal finde egnede elementer at genbruge på tværs af mange eksisterende vokabularer og modeller. Modelkataloget giver adgang til modeller, men ikke søgning på begrebs- eller elementniveau. Man skal derfor på forhånd vide, hvilken model det ønskede element findes i. Resultatet er, at elementer nyudvikles frem for at blive genbrugt, og at ellers beslægtede modeller ender med hver sin repræsentation af det samme.

**Mål:** At bygge en ny model på allerede anbefalede og velbeskrevne elementer i stedet for at opfinde dem forfra.

**Forløb:**

1. Modelløren skal repræsentere et begreb eller dataelement i en ny model.
2. Modelløren søger i ordbogen på begrebet, ikke på modellen.
3. Ordbogen viser kandidater med definition, dansk anvendelsestolkning, relationer til beslægtede elementer og oplysning om, hvor elementet allerede anvendes.
4. Modelløren vurderer kandidaterne og genbruger det egnede element, eller konstaterer begrundet, at intet passer.
5. Findes intet egnet element, kan behovet meldes ind til kuratering, så næste modellør ikke står i samme situation.

**Forudsætninger:**

- Søgning på enkeltelementer på tværs af modeller og vokabularer, ikke kun på modelniveau.
- Oplysning om, hvilke modeller og datakilder der allerede anvender elementet.
- Beskrivelser, der er fyldestgørende nok til, at egnethed kan vurderes uden at åbne kildevokabularet.

**Værdi:** Kortere modelleringstid, færre parallelle repræsentationer af samme begreb og modeller, der hænger sammen på tværs af myndigheder, fordi de trækker på samme elementer. Værdien høstes af den enkelte myndigheds udviklingsprojekter og af fællesskabet i form af mere ensartede modeller.

**Opfyldt når:** En modellør kan tage udgangspunkt i et begrebsnavn alene og på den baggrund finde frem til relevante genbrugelige elementer, uden forudgående viden om, hvilken model eller hvilket vokabular de findes i.

---

## UC5: Begrebsbaseret søgning i Datavejviser og andre datakataloger

**Primær aktør:** Datasøgende bruger i Datavejviser eller andet datakatalog, menneske eller digital agent

**Øvrige interessenter:** Datakatalogets ejere og redaktion, dataejere der gerne vil have deres data anvendt

**Situation i dag:** Brugere ved typisk, hvilket begreb de vil have data om, men ikke hvilke datasæt der indeholder relevante data. Søgningen foregår i dag med nøgleord og fritekstbeskrivelser. Dette afhænger af manuel vedligeholdelse af nøgleord, og relevante datasæt bliver ikke fundet, hvis de beskriver det samme med andre ord.

**Mål:** At finde de datasæt, der indeholder data om et bestemt begreb, uafhængigt af hvilke ord datasættets beskrivelse bruger.

**Forløb:**

1. Brugeren søger på et begreb i datakataloget.
2. Kataloget slår begrebet op i ordbogen og finder også synonymer, snævrere og bredere begreber.
3. Brugeren får de datasæt, hvis indhold er mappet til det pågældende begreb eller til beslægtede begreber.
4. Brugeren kan se, på hvilket grundlag et datasæt er fundet relevant.

**Forudsætninger:**

- Ordbogen kan anvendes af andre systemer, ikke kun via egen brugergrænseflade.
- Datasæt kan knyttes til ordbogens begreber på et niveau, der er finere end datasættet som helhed.
- Begrebshierarkier og synonymer, så en søgning kan udvides kontrolleret.

**Værdi:** Datavejviseren får en søgning, der bygger på betydning frem for på ordvalg, og som ikke skal vedligeholdes manuelt pr. datasæt. Dataejere får deres data fundet af flere brugere.

**Opfyldt når:** En søgning på et begreb i et katalog returnerer relevante datasæt, uden at det er afhængigt af manuelt vedligeholdte nøgleord

---

## UC6: Søge på tværs af flere datakilder uden dedikerede integrationer

**Primær aktør:** Analytiker, forretningsudvikler, explorativ datasøger

**Øvrige interessenter:** Dataejere, der ellers ville skulle bygge og vedligeholde punkt-til-punkt-integrationer

**Situation i dag:** Skal man have svar fra flere datakilder, skal man kende kilderne på forhånd og etablere en integration til hver. Det udelukker i praksis en explorativ tilgang til data og sammenhænge mellem data, samt hurtige test inden man evt. bygger dedikerede integrationer. Tværgående analyse og vidensøgning er ofte dyr og besværlig. 

**Mål:** At stille ét spørgsmål formuleret i begreber og få svar fra de datakilder, der har relevant data, uden at kende dem på forhånd og uden at bygge en integration pr. kilde.

**Forløb:**

1. Aktøren formulerer et spørgsmål ud fra begreber, ikke ud fra kildesystemernes feltnavne.
2. Spørgsmålet oversættes via ordbogens mapninger til de mappede datakilders egne repræsentationer.
3. De relevante kilder forespørges, og resultaterne stilles sammen på grundlag af den fælles begrebsforståelse.
4. Aktøren kan se, hvilke kilder der har bidraget, og hvor der er taget forbehold.

**Forudsætninger:**

- Mapninger, der er maskinlæsbare og præcise nok til at kunne oversætte en forespørgsel.
- Datakilder, der eksponerer data maskinelt, så en føderet forespørgsel kan gennemføres. Ordbogen løser den semantiske del, ikke adgangen til data.
- Gennemsigtighed om dækning, så et svar ikke fremstår udtømmende, hvis kun en del af de relevante kilder er mappet.

**Værdi:** Nye spørgsmål kan besvares uden nye integrationsprojekter, og værdien af hver enkelt mapning vokser med antallet af mappede kilder. Dette er den use case, der har den stærkeste netværkseffekt, og samtidig den, der stiller de største krav til udbredelse, før den bærer.

**Opfyldt når:** Et spørgsmål formuleret i ordbogens begreber kan besvares med data fra mere end én mappet kilde, uden at der er bygget en integration mellem de pågældende kilder.

---
