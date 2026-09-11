# Risveglio, secondo volume — checklist di copertura

Il secondo libro-infografica, consegnato l'11-9-2026
(`pdf-sorgenti/da tradurre e creare una mappa come si deve2.pdf`, 214 pagine di PDF =
2 d'indice + 211 di libro + coda). Continua il primo ma **non ne è il seguito numerato**:
ha un indice proprio che riparte da pagina 1. In coda dichiara finalmente **l'autore:
Harry B. Joseph** (il primo volume restava firmato solo «revival wisdom»), e chiude con
un *Message to humanity*.

**Corrispondenza pagine: pagina del PDF = pagina del libro + 3.**

**Differenza tecnica dal primo volume, da sapere prima di toccarlo.** Il primo PDF aveva
uno strato di testo estraibile; questo **non ne ha nessuno** — zero caratteri su tutte e
214 le pagine. Il testo è stato ricostruito con OCR (`pdftoppm -r 300 -gray -png` +
`tesseract -l eng --psm 3`, la strada già battuta col vol. III di Zeland, qui in inglese)
e sta in `testi/da-tradurre-e-creare-una-mappa-come-si-deve2.txt`. L'OCR è pulito ma resta
un appoggio per cercare: **ciò che si scrive nella mappa si scrive guardando la pagina**,
perché qui il diagramma *è* l'argomento. Alcune tavole anatomiche non si lasciano nemmeno
aprire dagli strumenti di lettura immagini: per quelle si lavora sul testo OCR e sul
riporto dell'immagine, che va comunque estratta e mostrata.

**L'indice del libro dichiara 77 voci. Le pagine con un titolo proprio sono 211.** Cioè
l'indice ne tace più di metà — blocchi interi (tutta l'anatomia simbolica dell'arte
rinascimentale ed egizia, i templi, le sei pagine di tecniche di proiezione astrale, la
Terra Santa, la sex magic, l'architettura occulta di Washington) non compaiono. **Questa
tabella è quindi costruita sulle pagine vere, non sull'indice**: è la sola lista di
controllo che non lascia fuori niente.

**Come si usa.** Una riga per pagina del libro. Si spunta `[x]` quando quella pagina è
stata letta *e* il suo contenuto è finito in una sezione, annotando `→ #sezione`. Una
pagina assorbita dentro una sezione più ampia si annota comunque: non si cancella.
`rinforzo` = argomento che la mappa già tratta (si allarga la sezione esistente e si
aggiorna la sua `<p class="src">`, non si duplica); `nuovo` = materiale che la mappa non
ha; `da vedere` = deciso dopo la lettura.

## La proposta di struttura

Il conto dice che **la maggior parte del volume rinforza** le dodici parti esistenti.
Resta però un blocco che non ha casa, ed è il più corposo del libro — quattro parti nuove:

- **XIII · Il corpo come tempio** (~70 pagine, di gran lunga il nucleo): l'anatomia
  simbolica letta nell'arte (Michelangelo, Blake, Mengs, Da Vinci) e nell'Egitto (djed,
  cranio, Horus e il tronco encefalico, Osiride e il cervello rettiliano, Thoth e
  l'ippocampo, Ganesh), i templi come corpo (Salomone, Luxor, Giza), **il cuore** (11
  pagine di fila), i dodici nervi cranici come i dodici discepoli, i meridiani, trauma e
  sistema nervoso.
- **XIV · La pratica** (~25 pagine): meditazione (6 pagine), respiro, controllo mentale
  sul campo energetico, preparazione e tecniche di proiezione astrale, affermazioni,
  canalizzazione, sincronizzazione emisferica. **Sarebbe la prima parte operativa di
  Risveglio**, che oggi espone soltanto dottrina.
- **XV · La parola** (~10 pagine): il potere delle parole, gli incantesimi nascosti nel
  linguaggio, le vocali, la preghiera, la benedizione sul cibo, i compleanni.
- **XVI · L'io e il male** (~12 pagine): il peccato, la decima, l'ego e il diavolo, gli
  strati del sé, paradiso e inferno, l'«io» dentro, bene e male, il bafometto.

Le ultime due sono le più discutibili: *la parola* potrebbe stare dentro *la pratica*, e
*l'io e il male* potrebbe distribuirsi fra VI Saturno (il diavolo) e III Corpo sottile
(gli strati del sé). Le altre due no: reggono da sole.

Fuori dalle parti nuove, gli innesti più grossi: **VII Astrologia** prende i sette pianeti
(5 pagine), la luna, i quattro segni fissi e i vangeli, e i metalli planetari;
**XI Mente e massoneria** prende undici pagine di simbolismo massonico voce per voce,
l'architettura occulta di Washington, i telefoni e la «mente-alveare»; **III Corpo
sottile** i piani di coscienza e il piano astrale; **VIII Cabala** nove pagine di albero
della vita e la *vesica piscis* — che è anche il primo punto in cui questa mappa tocca
per nome il perno della biblioteca, *Rapporto Vesica*.

## Le 211 pagine

| ok | pag. | Titolo (come sta nel libro) | Dove va | Che cosa è |
|---|---|---|---|---|
| [ ] | 0 | INTRODUCTION | I Il libro | cornice |
| [ ] | 1 | THE KABALISTIC TREE OF LIFE | VIII Cabala | rinforzo |
| [ ] | 2 | THE TREE OF LIFE AND THE HUMAN BODY | VIII Cabala | rinforzo |
| [ ] | 3 | PRACTICAL KABALAH | VIII Cabala | rinforzo |
| [ ] | 4 | THE TREE OF LIFE ANDITS INFLUENCE | VIII Cabala | rinforzo |
| [ ] | 5 | *(pagina senza titolo: tavola di figure)* | VIII Cabala | rinforzo |
| [ ] | 6 | CHRISTIANITY AND THE KABALAH | VIII Cabala | rinforzo |
| [ ] | 7 | THE TREE OF LIFE AND HUMAN NATURE | VIII Cabala | rinforzo |
| [ ] | 8 | CHRISTIANITY AND THE KABALAH TREE | VIII Cabala | rinforzo |
| [ ] | 9 | CHRISTIANITY AND THE KABALAH | VIII Cabala | rinforzo |
| [ ] | 10 | THE 5 SENSES AND THE NER VOUS SYSTEM | XIII Il corpo come tempio | nuovo |
| [ ] | 11 | THE 5 SENSES AND THE MIND | XIII Il corpo come tempio | nuovo |
| [ ] | 12 | PERCEIVING THE PHYSICAL WORLD | XIII Il corpo come tempio | nuovo |
| [ ] | 13 | THE TREE OF LIFE @ TREE OF KNOWLEDGE | VIII Cabala | rinforzo |
| [ ] | 14 | SPIRIT AND MATTER | III Corpo sottile | da vedere |
| [ ] | 15 | SPIRITUAL | III Corpo sottile | da vedere |
| [ ] | 16 | THE WORLD WITHIN | III Corpo sottile | rinforzo |
| [ ] | 17 | THE WORLD WITHIN | III Corpo sottile | rinforzo |
| [ ] | 18 | *(pagina senza titolo: tavola di figure)* | III Corpo sottile | rinforzo |
| [ ] | 19 | THE WORLD WITHIN | III Corpo sottile | rinforzo |
| [ ] | 20 | EGYPTIAN ART OF A UNITED UNIVERSE | X Culto solare | rinforzo |
| [ ] | 21 | SIN SEPERATES YOU FROM GOD | XVI L'io e il male | nuovo |
| [ ] | 22 | THE 7 DEADLY SINS | XVI L'io e il male | nuovo |
| [ ] | 23 | WHATIS CONSCIOUSNESS? | III Corpo sottile | rinforzo |
| [ ] | 24 | THE UNIVERSAL MIND | XI Mente | rinforzo |
| [ ] | 25 | ETYMOLOGY OF MIND | XI Mente | rinforzo |
| [ ] | 26 | I2 DISCIPLES AND THE 12 CRANIAL NERVES | XIII Il corpo come tempio | nuovo |
| [ ] | 27 | SPIRIT AND MATTER SYMBOLISM | XIII / IV | da vedere |
| [ ] | 28 | PERCEPTION: DA VINCI'S SYMBOLISM OF THE EYES | XIII / IV | da vedere |
| [ ] | 29 | CUBED CONSICOUSNESS | XIII / IV | da vedere |
| [ ] | 30 | HUMANS AND THE AWAKENING | XIII Il corpo come tempio | nuovo |
| [ ] | 31 | THE HUMAN CREATIVE ABILLITIES | XIII Il corpo come tempio | nuovo |
| [ ] | 32 | THE HUMAN DESIGN | XIII Il corpo come tempio | nuovo |
| [ ] | 33 | THE MAGNITUDE OF GOD'S INFINITE KNOWLEDGE | VIII Cabala | da vedere |
| [ ] | 34 | THE UNMATCHED DESIGN OF THE HUMAN EYE | II Luce e pineale | rinforzo |
| [ ] | 35 | *(pagina senza titolo: tavola di figure)* | II Luce e pineale | rinforzo |
| [ ] | 36 | THE MEANING OF LIFE | I Il libro | da vedere |
| [ ] | 37 | AS ABOVE SO BELOW | V Terra piatta / VIII | rinforzo |
| [ ] | 38 | THE FIBONACCI SEQUENCE | V Terra piatta / VIII | rinforzo |
| [ ] | 39 | MICHELANGELO SYMBOLIC ARTWORK | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 40 | MICHELANGELO SYMBOLIC ARTWORK | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 41 | MICHELANGELO SYMBOLIC ARTWORK | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 42 | ANTON RAPHAEL MENGS: THE ASCENSION | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 43 | WILLIAM BLAKE: THE FOUR AND TWENTY ELDERS | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 44 | GEREARD DA VID SYMBOLIC ARTWORK | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 45 | EGYPTIAN SYMBOLISM OF THE TOUNGE | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 46 | EGYPTIAN DJED PILLER | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 47 | EGYPTIAN CASKET SYMBOLISM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 48 | EGYPTIAN CASKET SYMBOLISM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 49 | EGYPTIAN SYMBOLISM OF THE SKULL | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 50 | EGYPTIAN SYMBOLISM OF THE SKULL | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 51 | FALCON OF HORUS @ THE BRAIN STEM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 52 | OSIRIS THE REPTILLIAN BRAIN | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 53 | GANESH THE HINDU DIETY @ ANATOMY | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 54 | HORUS SYMBOLISM AND ANATOMY | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 55 | SYMBOLISM OF THE HIPPOCAMPUS | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 56 | SYMBOLISM OF THE HIPPOCAMPUS | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 57 | THOTH THE GOD OF WISDOM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 58 | THOTH THE GOD OF WISDOM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 59 | EGYPTIAN ANKH SYMBOLISM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 60 | THE SYMBOLIC LANGUAGE OF NATURE | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 61 | FREEMASONIC ART @ ANATOMY | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 62 | THE ARCH OF THE COVENANT | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 63 | SPINAL COLUMN SYMBOLISM | XIII Il corpo come tempio | NUOVO - anatomia simbolica |
| [ ] | 64 | JACOBS LADDER | XIII / I | da vedere |
| [ ] | 65 | WHY USE SYMBOLISM? | XIII / I | da vedere |
| [ ] | 66 | THE BODY IS A TEMPLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 67 | THE BODY IS A TEMPLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 68 | SOLOMONS TEMPLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 69 | THE LUXOR TEMPLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 70 | THE LUXOR TEMPLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 71 | THE GREAT PYRAMID OF GIZA, EGYPT | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 72 | THE TEMPLE OF GODIN THE BIBLE | XIII Il corpo come tempio | nuovo - i templi |
| [ ] | 73 | THE SYMBOL OF THE BAPHOMET | XVI L'io e il male | nuovo |
| [ ] | 74 | ALIGORIES OF THE RIGHT BRAIN | IV Testa ed elementi | rinforzo |
| [ ] | 75 | THE FUNCTIONS OF THE RIGHT BRAIN | IV Testa ed elementi | rinforzo |
| [ ] | 76 | WHATIS HEA VEN? | XVI L'io e il male | nuovo |
| [ ] | 77 | THE TRUE MEANING OF TITHING | XVI L'io e il male | nuovo |
| [ ] | 78 | THE EGO AND THE DEVIL | XVI L'io e il male | nuovo |
| [ ] | 79 | UNVEILING THE LAYERS OF THE TRUE SELF | XVI L'io e il male | nuovo |
| [ ] | 80 | SYMBOLISM OF THE DEVIL | XVI L'io e il male | nuovo |
| [ ] | 81 | THE 5 SENSES AND LUCIFER | XVI L'io e il male | nuovo |
| [ ] | 82 | HEAVEN AND HELL | XVI L'io e il male | nuovo |
| [ ] | 83 | THE “I” WITHIN | XVI L'io e il male | nuovo |
| [ ] | 84 | MEDITATION | XIV La pratica | NUOVO - meditazione |
| [ ] | 85 | MEDITATION BENIFITS | XIV La pratica | NUOVO - meditazione |
| [ ] | 86 | THE RINGS OF MEDITATION | XIV La pratica | NUOVO - meditazione |
| [ ] | 87 | MEDITATION @ ELECTRICAL ENERGY | XIV La pratica | NUOVO - meditazione |
| [ ] | 88 | CONNECTING TO SOURCE MEDITATION | XIV La pratica | NUOVO - meditazione |
| [ ] | 89 | MEDITATION IN THE BIBLE | XIV La pratica | NUOVO - meditazione |
| [ ] | 90 | BUDDHA SYMBOLISM AND BREATHWORK | XIV La pratica | NUOVO - meditazione |
| [ ] | 91 | MEDITATION AND SELF CONTROL | XIV La pratica | NUOVO - meditazione |
| [ ] | 92 | *(pagina senza titolo: tavola di figure)* | XIV La pratica | NUOVO - meditazione |
| [ ] | 93 | *(pagina senza titolo: tavola di figure)* | XIV La pratica | NUOVO - meditazione |
| [ ] | 94 | SOUL ENERGY | XIV La pratica | NUOVO - meditazione |
| [ ] | 95 | MENTAL CONTROL OVER THE ENERGY FIELD | XIV La pratica | nuovo - controllo del campo |
| [ ] | 96 | MENTAL CONTROL OVER THE ENERGY FIELD | XIV La pratica | nuovo - controllo del campo |
| [ ] | 97 | MENTAL CONTROL OVER THE ENERGY FIELD | XIV La pratica | nuovo - controllo del campo |
| [ ] | 98 | MENTAL CONTROL OVER THE ENERGY FIELD | XIV La pratica | nuovo - controllo del campo |
| [ ] | 99 | THE BASICS GEOMETRY | VIII Cabala | rinforzo |
| [ ] | 100 | THE VESICA PISCES | VIII Cabala | rinforzo |
| [ ] | 101 | THE BRAIN AND HANDS CONNECTION | XI Mente | rinforzo |
| [ ] | 102 | THE HEART VORTEX | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 103 | THE HEART VORTEX | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 104 | THE HEART @ ITS ROLE INHUMAN CONSCIOUSNESS | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 105 | THE SOUL'S GUIDANCE AND THE ESSENCE OF OUR BEING | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 106 | THE HEARTS INFLUENCE ON THE BIOFIELD | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 107 | THE ARMOR OF GOD | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 108 | THE HEART AS AN ENERGETIC GATEWAY | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 109 | THE FLOW OF ENERGY | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 110 | MORALITY AND THE ENERGY FIELD | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 111 | BALANCING THE MIND AND HEART | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 112 | THE ANTI CHRIST CROSS GESTURE | XIII Il corpo come tempio | NUOVO - il cuore |
| [ ] | 113 | GOOD AND EVIL | XVI L'io e il male | da vedere |
| [ ] | 114 | ESOTERIC ASTROLOGY | VII Astrologia | rinforzo |
| [ ] | 115 | ESOTERIC ASTROLOGY | VII Astrologia | rinforzo |
| [ ] | 116 | THE 4 FIXED SIGNS | VII Astrologia | rinforzo |
| [ ] | 117 | THE 4 FIXED SIGNS | VII Astrologia | rinforzo |
| [ ] | 118 | THE 4 FIXED SIGNS @ THE GOSPELS | VII Astrologia | rinforzo |
| [ ] | 119 | *(pagina senza titolo: tavola di figure)* | VII Astrologia | rinforzo |
| [ ] | 120 | THE 4 FIXED SIGNS @ THE GOSPELS | VII Astrologia | rinforzo |
| [ ] | 121 | EZEKTAL VISION OF THE THRONE OF GOD | VII Astrologia | rinforzo |
| [ ] | 122 | THE ZODIAC AND ANGELS | VII Astrologia | rinforzo |
| [ ] | 123 | ASTROLOGY AND THE HUMAN BODY | VII Astrologia | rinforzo |
| [ ] | 124 | *(pagina senza titolo: tavola di figure)* | VII Astrologia | rinforzo |
| [ ] | 125 | *(pagina senza titolo: tavola di figure)* | VII Astrologia | rinforzo |
| [ ] | 126 | THE ESOTERIC UNDERSTANDING OF THE MOON | VII Astrologia | rinforzo |
| [ ] | 127 | THE MOON AND MENSTRUATION CYCLE | VII Astrologia | rinforzo |
| [ ] | 128 | SYMBOLISM OF THE MOON | VII Astrologia | rinforzo |
| [ ] | 129 | DIVINE MASCULINE AND DIVINE FEMANINE | XII Sesso e leggi | rinforzo |
| [ ] | 130 | THE OCCULT MEANING OF THE 7 PLANETS | VII Astrologia | rinforzo |
| [ ] | 131 | THE OCCULT MEANING OF THE 7 PLANETS | VII Astrologia | rinforzo |
| [ ] | 132 | THE OCCULT MEANING OF THE 7 PLANETS | VII Astrologia | rinforzo |
| [ ] | 133 | THE OCCULT MEANING OF THE 7 PLANETS | VII Astrologia | rinforzo |
| [ ] | 134 | THE OCCULT MEANING OF THE 7 PLANETS | VII Astrologia | rinforzo |
| [ ] | 135 | THE SIGNIFICANCE OF SATURN | VI Saturno | rinforzo |
| [ ] | 136 | THE SIGNIFICANCE OF SATURN | VI Saturno | rinforzo |
| [ ] | 137 | THE SKY CLOCK | VI Saturno | rinforzo |
| [ ] | 138 | *(pagina senza titolo: tavola di figure)* | V Terra piatta | da vedere |
| [ ] | 139 | THE COSMIC EGG | V Terra piatta | da vedere |
| [ ] | 140 | HELIOCENTRIC MODEL | V Terra piatta | rinforzo |
| [ ] | 141 | THE SOUL SYSTEM | VI Saturno | da vedere |
| [ ] | 142 | HOW THE SUN WORKS | V / X | rinforzo |
| [ ] | 143 | NORTH, WEST, EAST @ SOUTH | V / X | rinforzo |
| [ ] | 144 | TH SUNS MOVEMENT AND SIZE | V / X | rinforzo |
| [ ] | 145 | THE POWER OF WORDS | XV La parola | NUOVO |
| [ ] | 146 | THE POWER OF WORDS | XV La parola | NUOVO |
| [ ] | 147 | PREYING OVER FOOD | XV La parola | NUOVO |
| [ ] | 148 | HIDDEN SPELLS IN LANGUAGE | XV La parola | NUOVO |
| [ ] | 149 | HIDDEN SPELLS IN LANGUAGE | XV La parola | NUOVO |
| [ ] | 150 | THE OCCULT MEANING OF BIRTHDA ¥ CELEBRATIONS | XV La parola | NUOVO |
| [ ] | 151 | THE SUBCONSCIOUS PROGRAMMING OF VOWELS | XV La parola | NUOVO |
| [ ] | 152 | ALCOHOL | IX Corpo e dieta | rinforzo |
| [ ] | 153 | *(pagina senza titolo: tavola di figure)* | III Corpo sottile | rinforzo |
| [ ] | 154 | PLANES OF CONSCIOUSNESS | III Corpo sottile | rinforzo |
| [ ] | 155 | THE BUDDIC PLANE | III Corpo sottile | rinforzo |
| [ ] | 156 | THE ASTRAL PLANE | III Corpo sottile | rinforzo |
| [ ] | 157 | THE ASTRAL PLANE | III Corpo sottile | rinforzo |
| [ ] | 158 | THE ETHERIC PLANE | III Corpo sottile | rinforzo |
| [ ] | 159 | ASTRAL PROJECTION | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 160 | ASTRAL PROJECTION SYMBOLISM | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 161 | ASTRAL PROJECTION IN THE BIBLE | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 162 | PREPERATION FOR ASTRAL PROJECTION | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 163 | ASTRAL PROJECTION FOR BEGINNERS | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 164 | DAYDREAMING TECHNIQUE | III + XIV (le tecniche) | rinforzo + nuovo |
| [ ] | 165 | HEMISPHERIC SYNCHRONIZATION | IV / XIV | nuovo |
| [ ] | 166 | THE HOLY LAND OF ISRAEL | ? | NUOVO - non in indice |
| [ ] | 167 | THE HOLY LAND OF ISRAEL | ? | NUOVO - non in indice |
| [ ] | 168 | THE SIGNIFICANCE OF SEX | XII Sesso e leggi | rinforzo |
| [ ] | 169 | SEX MAGIC | XII Sesso e leggi | rinforzo |
| [ ] | 170 | FREEING THE MIND | XIV La pratica | nuovo |
| [ ] | 171 | THE DANGERS OF PHONES | XI Mente | NUOVO |
| [ ] | 172 | THE MENTAL PLANE HIVE-MIND | XI Mente | NUOVO |
| [ ] | 173 | THE DUAL REALMS OF THE MIND | XI + XIV | rinforzo + nuovo |
| [ ] | 174 | SUBCONSCIOUS PROGRAMS | XI + XIV | rinforzo + nuovo |
| [ ] | 175 | SUBCONSCIOUS PROGRAMS | XI + XIV | rinforzo + nuovo |
| [ ] | 176 | PROGRAMING THE SUBCONSCIOUS: AFFIRMATIONS | XI + XIV | rinforzo + nuovo |
| [ ] | 177 | CHANNELING HIGHER WISDOM | XIV La pratica | nuovo |
| [ ] | 178 | THE TRUE MEANING OF PRAYER | XV La parola | nuovo |
| [ ] | 179 | MUSICIS A FORM OF MAGIC | IX Corpo e dieta | rinforzo |
| [ ] | 180 | MUSICIS A FORM OF MAGIC | IX Corpo e dieta | rinforzo |
| [ ] | 181 | RAISING OF THE CHRISM | II Luce e pineale | rinforzo |
| [ ] | 182 | THE RESURECTION OF CHRIST | II Luce e pineale | rinforzo |
| [ ] | 183 | DIVINE FEMANINE | XII Sesso e leggi | rinforzo |
| [ ] | 184 | RAISING CONSIOUSNESS | IV / XIV | da vedere |
| [ ] | 185 | THE ELEMENTS e@ STAGES OF CONSCIOUSNESS | IV / XIV | da vedere |
| [ ] | 186 | THE TRUE MEANING OF BAPTISM | IV / XIV | da vedere |
| [ ] | 187 | THE SYMBOLISM OF TURNING WATER INTO WINE | ? | nuovo |
| [ ] | 188 | TRAUMA AND THE NERVOUS SYSTEM | XIII Il corpo come tempio | NUOVO |
| [ ] | 189 | MERIDIANS OF THE BODY | XIII Il corpo come tempio | NUOVO |
| [ ] | 190 | THE 12 MAJOR BODY MERIDIANS | XIII Il corpo come tempio | NUOVO |
| [ ] | 191 | THE OCCULT VIRTUES OF METALS | VII Astrologia (i metalli planetari) | NUOVO |
| [ ] | 192 | THE OCCULT VIRTUES OF METALS | VII Astrologia (i metalli planetari) | NUOVO |
| [ ] | 193 | OCCULT ARCHITECTURE: WASHINGTON | XI Mente e massoneria | NUOVO - architettura occulta |
| [ ] | 194 | OCCULT ARCHITECTURE: WASHINGTON | XI Mente e massoneria | NUOVO - architettura occulta |
| [ ] | 195 | ELECTRI-CITY | XI Mente e massoneria | NUOVO - architettura occulta |
| [ ] | 196 | FREEMASONIC SYMBOLISM: CHECKERD FLOOR | XI Mente e massoneria | rinforzo |
| [ ] | 197 | FREEMASONIC SYMBOLISM: 3, 5, 7 STAIRCASE | XI Mente e massoneria | rinforzo |
| [ ] | 198 | FREEMASONIC SYMBOLISM: SQUARE & COMPASS | XI Mente e massoneria | rinforzo |
| [ ] | 199 | FREEMASONIC SYMBOLISM: G | XI Mente e massoneria | rinforzo |
| [ ] | 200 | FREEMASONIC SYMBOLISM: COVERING ONE EYE | XI Mente e massoneria | rinforzo |
| [ ] | 201 | FREEMASONIC SYMBOLISM: COVERING MOUTH | XI Mente e massoneria | rinforzo |
| [ ] | 202 | FREEMASONIC SYMBOLISM: THE EYE OF PROVIDENCE | XI Mente e massoneria | rinforzo |
| [ ] | 203 | FREEMASONIC SYMBOLISM: ONE DOLLER BILL | XI Mente e massoneria | rinforzo |
| [ ] | 204 | FREEMASONIC SYMBOLISM: HAND GESTURES | XI Mente e massoneria | rinforzo |
| [ ] | 205 | FREEMASONIC SYMBOLISM: THE CROSS | XI Mente e massoneria | rinforzo |
| [ ] | 206 | FREEMASONIC SYMBOLISM: SWORD AND HEART | XI Mente e massoneria | rinforzo |
| [ ] | 207 | THE END | I Il libro | cornice - l'autore |
| [ ] | 208 | *(pagina senza titolo: tavola di figure)* | I Il libro | cornice - l'autore |
| [ ] | 209 | *(pagina senza titolo: tavola di figure)* | I Il libro | cornice - l'autore |
| [ ] | 210 | HARRY B. JOSEPH | I Il libro | cornice - l'autore |
| [ ] | 211 | MESSAGE TO HUMANITY | I Il libro | cornice - l'autore |
