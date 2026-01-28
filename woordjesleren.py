import pygame
import random
import sys
import time
import os
import json

# --- INITIALISATIE (Bovenaan je script) ---
alle_lijsten = {"Standaard": {}}
actieve_lijst_namen = ["Standaard"] # We beginnen met de standaardlijst aan
woordenlijst = {}

def laden_woorden():
    global alle_lijsten
    try:
        if os.path.exists("alle_lijsten.txt"):
            with open("alle_lijsten.txt", "r") as f:
                data = json.load(f)
                if data:
                    alle_lijsten = data
        else:
            alle_lijsten = {"Standaard": {}}
    except Exception as e:
        print(f"Kon niet laden: {e}")
        alle_lijsten = {"Standaard": {}}

def opslaan_woorden():
    global alle_lijsten
    try:
        with open("alle_lijsten.txt", "w") as f:
            json.dump(alle_lijsten, f)
    except Exception as e:
        print(f"Fout bij opslaan: {e}")

def update_actieve_woorden():
    global woordenlijst, actieve_lijst_namen, alle_lijsten
    woordenlijst = {} 
    # Als er geen lijsten zijn aangevinkt, gebruik dan de eerste lijst die bestaat
    namen_om_te_laden = actieve_lijst_namen if actieve_lijst_namen else [list(alle_lijsten.keys())[0]]
    
    for naam in namen_om_te_laden:
        if naam in alle_lijsten:
            woordenlijst.update(alle_lijsten[naam])

# Nu pas de functies aanroepen om de data klaar te zetten
laden_woorden()
update_actieve_woorden()

# --- CONFIGURATIE ---
SCHERM_BREEDTE, SCHERM_HOOGTE = 800, 600
FPS = 60
BESTAND_NAAM = "woordenlijst.txt"

# Kleuren
WIT, ZWART, GRIJS = (255, 255, 255), (0, 0, 0), (40, 40, 40)
LICHTGRIJS, ROOD, HELROOD = (150, 150, 150), (200, 0, 0), (255, 0, 0)
GROEN, BLAUW, GEEL = (50, 200, 50), (50, 100, 255), (255, 215, 0)
PAARS, ORANJE, DONKERROOD = (150, 50, 200), (255, 165, 0), (139, 0, 0)

# Globale Instellingen
regen_snelheid = 1.0     # Valt tussen 0.1 en 2.5
regen_frequentie = 200   # Valt tussen 100 en 500
quiz_tijd = 15
match_aantal = 5
schieten_levens = 3
bot_snelheid = 10
bot_moeilijkheid = 0.5

# --- INITIALISATIE ---
pygame.init()
scherm = pygame.display.set_mode((SCHERM_BREEDTE, SCHERM_HOOGTE))
pygame.display.set_caption("Word Trainer Pro v20")
klok = pygame.time.Clock()

font_titel = pygame.font.SysFont("Arial", 35, bold=True)
font_tekst = pygame.font.SysFont("Arial", 25)
font_klein = pygame.font.SysFont("Arial", 16)

# --- BESTANDSBEHEER ---
def laad_woorden():
    w = {}
    if os.path.exists(BESTAND_NAAM):
        with open(BESTAND_NAAM, "r", encoding="utf-8") as f:
            for r in f:
                if ":" in r: k, v = r.strip().split(":", 1); w[k] = v
    return w

def sla_woorden_op(w):
    with open(BESTAND_NAAM, "w", encoding="utf-8") as f:
        for k, v in w.items(): f.write(f"{k}:{v}\n")

woordenlijst = laad_woorden()

# --- HULPFUNCTIES ---
def activeer_willekeurige_jumpscare():
    keuze = random.randint(1, 5)
    start = time.time()
    while time.time() - start < 0.6:
        pygame.event.pump()
        if keuze == 1: scherm.fill(random.choice([ROOD, ZWART]))
        elif keuze == 2: 
            scherm.fill(ZWART)
            pygame.draw.circle(scherm, HELROOD, (random.randint(200,600), 300), 100)
        elif keuze == 3:
            for _ in range(1000): pygame.draw.rect(scherm, WIT, (random.randint(0,800), random.randint(0,600), 3, 3))
        elif keuze == 4:
            teken_tekst("FAILURE", font_titel, ROOD, 400, 300, center=True)
        elif keuze == 5:
            scherm.fill(random.choice([PAARS, ZWART, ROOD]))
        pygame.display.flip()

def teken_tekst(tekst, font, kleur, x, y, center=False, max_b=None):
    surf = font.render(str(tekst), True, kleur)
    if max_b and surf.get_width() > max_b:
        schaal = max_b / surf.get_width()
        font = pygame.font.SysFont("Arial", int(font.get_height() * schaal))
        surf = font.render(str(tekst), True, kleur)
    rect = surf.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    scherm.blit(surf, rect)
    return rect

# --- KLASSEN ---
class Slider:
    def __init__(self, x, y, w, min_v, max_v, start_v, label):
        self.rect = pygame.Rect(x, y, w, 8)
        self.min_v, self.max_v = min_v, max_v
        self.val = start_v
        self.knop_x = x + (start_v - min_v) / (max_v - min_v) * w
        self.label = label
    def teken(self):
        pygame.draw.rect(scherm, GRIJS, self.rect)
        pygame.draw.circle(scherm, GEEL, (int(self.knop_x), self.rect.centery), 10)
        teken_tekst(f"{self.label}: {round(self.val, 1)}", font_klein, WIT, self.rect.x, self.rect.y - 20)
    def update(self, muis_pos, klikken):
        if klikken and self.rect.inflate(20, 30).collidepoint(muis_pos):
            self.knop_x = max(self.rect.x, min(muis_pos[0], self.rect.x + self.rect.width))
            perc = (self.knop_x - self.rect.x) / self.rect.width
            self.val = self.min_v + perc * (self.max_v - self.min_v)
        return self.val

class Knop:
    def __init__(self, tekst, x, y, b, h, kleur, actie):
        self.rect = pygame.Rect(x, y, b, h); self.tekst = tekst
        self.kleur, self.actie = kleur, actie
        self.hover, self.zichtbaar, self.geselecteerd = False, True, False
    def teken(self, win, override=None):
        if not self.zichtbaar: return
        c = override if override else (self.kleur if not self.hover else [min(i+30, 255) for i in self.kleur])
        if self.geselecteerd: c = GEEL
        pygame.draw.rect(win, c, self.rect, border_radius=5)
        teken_tekst(self.tekst, font_tekst, ZWART if self.geselecteerd else WIT, self.rect.centerx, self.rect.centery, center=True, max_b=self.rect.width-5)

class Ballon:
    def __init__(self, letter):
        self.letter = letter; self.radius = 25
        self.x = random.randint(30, 770); self.y = random.randint(-500, -50)
        self.snelheid = random.uniform(1.0, 2.5); self.kleur = random.choice([PAARS, ORANJE, BLAUW])
    def update(self):
        self.y += self.snelheid
        if self.y > 600: self.y = -50; self.x = random.randint(30, 770)
    def teken(self):
        pygame.draw.circle(scherm, self.kleur, (int(self.x), int(self.y)), self.radius)
        teken_tekst(self.letter, font_tekst, WIT, self.x, self.y, center=True)
        
def check_winnaar(bord):
    lijnen = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lijnen:
        if bord[a] == bord[b] == bord[c] and bord[a] != "":
            return bord[a]
    if "" not in bord:
        return "Gelijk"
    return None

def slimme_bot_zet(bord, intelligentie):
    vrije_plekken = [i for i, v in enumerate(bord) if v == ""]
    if not vrije_plekken: return None

    # Intelligentie check (0.0 is dom, 1.0 is onfeilbaar)
    if random.random() > intelligentie:
        return random.choice(vrije_plekken)

    lijnen = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]

    # 1. Kan de bot (O) winnen?
    for a, b, c in lijnen:
        rij = [bord[a], bord[b], bord[c]]
        if rij.count("O") == 2 and rij.count("") == 1:
            return [a, b, c][[a, b, c].index([i for i in [a,b,c] if bord[i] == ""][0])]

    # 2. Moet de bot de speler (X) blokkeren?
    for a, b, c in lijnen:
        rij = [bord[a], bord[b], bord[c]]
        if rij.count("X") == 2 and rij.count("") == 1:
            return [a, b, c][[a, b, c].index([i for i in [a,b,c] if bord[i] == ""][0])]

    # 3. Pak het midden als het vrij is
    if bord[4] == "": return 4

    # 4. Anders random
    return random.choice(vrije_plekken)

def check_winnaar_vier(bord):
    # Horizontaal
    for r in range(6):
        for c in range(4):
            if bord[r][c] == bord[r][c+1] == bord[r][c+2] == bord[r][c+3] != "":
                return bord[r][c]

    # Verticaal
    for r in range(3):
        for c in range(7):
            if bord[r][c] == bord[r+1][c] == bord[r+2][c] == bord[r+3][c] != "":
                return bord[r][c]

    # Diagonaal (rechts naar beneden)
    for r in range(3):
        for c in range(4):
            if bord[r][c] == bord[r+1][c+1] == bord[r+2][c+2] == bord[r+3][c+3] != "":
                return bord[r][c]

    # Diagonaal (links naar beneden)
    for r in range(3):
        for c in range(3, 7):
            if bord[r][c] == bord[r+1][c-1] == bord[r+2][c-2] == bord[r+3][c-3] != "":
                return bord[r][c]

    # Gelijkspel check
    is_vol = True
    for c in range(7):
        if bord[0][c] == "":
            is_vol = False
            break
    if is_vol:
        return "Gelijk"

    return None

def slimme_bot_zet_vier(bord, intelligentie):
    vrije_cols = [c for c in range(7) if bord[0][c] == ""]
    if not vrije_cols: return None

    # Intelligentie-check
    if random.random() > intelligentie:
        return random.choice(vrije_cols)

    def get_vrije_rij(kolom):
        for r in reversed(range(6)):
            if bord[r][kolom] == "": return r
        return None

    # 1. Probeer direct te winnen
    for c in vrije_cols:
        r = get_vrije_rij(c)
        bord[r][c] = "O"
        if check_winnaar_vier(bord) == "O":
            bord[r][c] = ""
            return c
        bord[r][c] = ""

    # 2. Blokkeer de speler
    for c in vrije_cols:
        r = get_vrije_rij(c)
        bord[r][c] = "X"
        if check_winnaar_vier(bord) == "X":
            bord[r][c] = ""
            return c
        bord[r][c] = ""

    # 3. Strategisch midden
    if 3 in vrije_cols: return 3
    return random.choice(vrije_cols)

# --- PAUZE MENU ---
def pauze_scherm():
    global bot_moeilijkheid, bot_snelheid
    pauze = True
    s_int = Slider(300, 300, 200, 0.0, 1.0, bot_moeilijkheid, "Slimheid")
    s_speed = Slider(300, 380, 200, 5, 30, bot_snelheid, "Bot Tijd")
    
    while pauze:
        overlay = pygame.Surface((SCHERM_BREEDTE, SCHERM_HOOGTE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        scherm.blit(overlay, (0,0))
        muis = pygame.mouse.get_pos(); klik = pygame.mouse.get_pressed()[0]
        
        bot_moeilijkheid = s_int.update(muis, klik); s_int.teken()
        bot_snelheid = s_speed.update(muis, klik); s_speed.teken()
        
        teken_tekst("GEPAUZEERD", font_titel, WIT, 400, 150, center=True)
        teken_tekst("Druk op [/] om verder te gaan", font_tekst, GEEL, 400, 230, center=True)
        
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SLASH: pauze = False
        klok.tick(FPS)

# --- GAMES ---
def game_vier():
    global bot_moeilijkheid, bot_snelheid, speler_score, bot_score
    bord = [["" for _ in range(7)] for _ in range(6)]
    beurt_speler = False
    vraag_woord = random.choice(list(woordenlijst.keys())) if woordenlijst else "..."
    input_text = ""
    last_bot_move = time.time()
    penalty_einde = 0
    fout_tekst = ""
    winnaar = None

    pygame.key.start_text_input()

    while True:
        nu = time.time()
        scherm.fill(ZWART)
        
        # 1. Teken Bord
        for r in range(6):
            for c in range(7):
                x, y = 175 + c * 75, 150 + r * 70
                pygame.draw.circle(scherm, GRIJS, (x, y), 30)
                if bord[r][c] == "X": pygame.draw.circle(scherm, BLAUW, (x, y), 28)
                if bord[r][c] == "O": pygame.draw.circle(scherm, ROOD, (x, y), 28)

        # 2. Win check
        if winnaar:
            if winnaar == "X": speler_score += 1
            elif winnaar == "O": bot_score += 1
            tekst = f"{winnaar} wint!" if winnaar != "Gelijk" else "Gelijkspel!"
            teken_tekst(tekst, font_titel, GROEN, 400, 300, center=True)
            pygame.display.flip(); pygame.time.delay(2000)
            pygame.key.stop_text_input(); return

        # 3. UI en Timer
        teken_tekst(f"Vertaal: {vraag_woord}", font_tekst, WIT, 400, 30, center=True)
        bot_tijd_verstreken = nu - last_bot_move
        bot_tijd_over = max(0, int(bot_snelheid - bot_tijd_verstreken))
        teken_tekst(f"Bot zet over: {bot_tijd_over}s", font_klein, WIT, 400, 550, center=True)
        teken_tekst(f"JIJ: {speler_score} - BOT: {bot_score}", font_klein, GEEL, 400, 575, center=True)
        
        if nu < penalty_einde:
            # Toon het goede antwoord tijdens de penalty
            teken_tekst(f"PENALTY: {int(penalty_einde - nu)}s", font_tekst, ROOD, 400, 70, center=True)
            teken_tekst(f"Het goede antwoord was: {fout_tekst}", font_tekst, ORANJE, 400, 105, center=True)
        elif beurt_speler:
            teken_tekst("GOED! KLIK OP EEN KOLOM", font_tekst, GROEN, 400, 70, center=True)
        else:
            teken_tekst(f"Typ: {input_text}_", font_tekst, GEEL, 400, 70, center=True)

        # 4. Bot beurt check
        if bot_tijd_verstreken >= bot_snelheid and not winnaar:
            c_keuze = slimme_bot_zet_vier(bord, bot_moeilijkheid)
            if c_keuze is not None:
                for r in reversed(range(6)):
                    if bord[r][c_keuze] == "":
                        bord[r][c_keuze] = "O"; break
                winnaar = check_winnaar_vier(bord)
            last_bot_move = time.time()

        pygame.display.flip()

        # 5. Events
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: pygame.key.stop_text_input(); return
                if e.key == pygame.K_SLASH: 
                    pauze_scherm(); last_bot_move = time.time() - bot_tijd_verstreken
                
                if nu > penalty_einde and not beurt_speler:
                    if e.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                    elif e.key == pygame.K_TAB:
                        # Hier tonen we het goede antwoord bij een skip
                        fout_tekst = woordenlijst.get(vraag_woord, "???")
                        penalty_einde = nu + 10 # 10 seconden straf
                        input_text = ""
                        # We kiezen alvast een nieuw woord voor na de penalty
                        vraag_woord = random.choice(list(woordenlijst.keys()))
                    elif e.key == pygame.K_RETURN:
                        if input_text.strip().lower() == woordenlijst.get(vraag_woord, "").lower():
                            beurt_speler = True
                        input_text = ""
            
            if e.type == pygame.TEXTINPUT and not beurt_speler and nu > penalty_einde:
                if e.text != "/": input_text += e.text

            # 6. Muisklik
            if e.type == pygame.MOUSEBUTTONDOWN and beurt_speler and not winnaar:
                for c in range(7):
                    if abs(e.pos[0] - (175 + c * 75)) < 35:
                        if bord[0][c] == "":
                            for r in reversed(range(6)):
                                if bord[r][c] == "":
                                    bord[r][c] = "X"; break
                            winnaar = check_winnaar_vier(bord)
                            beurt_speler = False
                            if woordenlijst:
                                vraag_woord = random.choice(list(woordenlijst.keys()))
                            input_text = ""
        klok.tick(FPS)

def woordenregen():
    global regen_snelheid, regen_frequentie
    actieve_woorden = []
    score = 0
    input_text = ""
    spawn_timer = 0
    start_tijd = time.time()
    
    pygame.key.start_text_input()

    while True:
        nu = time.time()
        verstreken_seconden = nu - start_tijd
        scherm.fill(ZWART)
        
        # 1. Dynamische moeilijkheid berekenen
        # Snelheid stijgt met 0.001 per seconde
        huidige_snelheid = regen_snelheid + (verstreken_seconden * 0.001)
        # Pauze daalt met 0.15 frames per seconde (minimaal 30 frames om crashes te voorkomen)
        huidige_frequentie = max(30, regen_frequentie - (verstreken_seconden * 0.15))
        
        # 2. Woorden spawnen (Logica: Timer afgelopen OF scherm leeg)
        spawn_timer += 1
        scherm_is_leeg = len(actieve_woorden) == 0
        
        if (spawn_timer >= huidige_frequentie or scherm_is_leeg) and woordenlijst:
            nl = random.choice(list(woordenlijst.keys()))
            en = woordenlijst[nl]
            actieve_woorden.append({
                'nl': nl, 
                'en': en, 
                'x': random.randint(50, 700), 
                'y': -20
            })
            spawn_timer = 0 

        # 3. Woorden bewegen, kleuren en tekenen
        for w in actieve_woorden[:]:
            w['y'] += huidige_snelheid
            
            # Visuele waarschuwing op basis van hoogte
            kleur = WIT
            if w['y'] > 250: kleur = ORANJE
            if w['y'] > 400: kleur = ROOD
            
            teken_tekst(w['nl'], font_tekst, kleur, w['x'], w['y'])
            
            # Game Over check
            if w['y'] > 550:
                pygame.key.stop_text_input()
                teken_tekst(f"TE LAAT! {w['nl']} = {w['en']}", font_tekst, ROOD, 400, 300, center=True)
                pygame.display.flip()
                pygame.time.delay(2000)
                return

        # 4. UI: Statistieken onderaan
        pygame.draw.rect(scherm, GRIJS, (0, 550, 800, 50))
        teken_tekst(f"Typ: {input_text}", font_tekst, GEEL, 20, 560)
        teken_tekst(f"Score: {score}", font_tekst, GROEN, 650, 560)
        
        # Debug info zodat je de versnelling ziet
        stats_tekst = f"Speed: {huidige_snelheid:.3f} | Pauze: {int(huidige_frequentie)}"
        teken_tekst(stats_tekst, font_klein, WIT, 320, 565)

        # 5. Events (Typen en Pauze)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: 
                    pygame.key.stop_text_input(); return
                if e.key == pygame.K_SLASH: 
                    pauze_scherm()
                    # Herbereken start_tijd om sprongen in moeilijkheid te voorkomen
                    start_tijd = time.time() - verstreken_seconden 
                
                if e.key == pygame.K_BACKSPACE: 
                    input_text = input_text[:-1]
                if e.key == pygame.K_RETURN:
                    # Check de woorden van onder naar boven
                    for i, w in enumerate(actieve_woorden):
                        if input_text.strip().lower() == w['en'].lower():
                            actieve_woorden.pop(i)
                            score += 1
                            break
                    input_text = ""

            if e.type == pygame.TEXTINPUT:
                if e.text != "/":
                    input_text += e.text

        pygame.display.flip()
        klok.tick(FPS)

def game_quiz():
    if len(woordenlijst) < 4: return
    items = list(woordenlijst.keys()); random.shuffle(items)
    p_50, p_skip, p_frz = True, True, True
    for vraag in items:
        goed = woordenlijst[vraag]; fouten = [v for v in woordenlijst.values() if v != goed]
        opties = random.sample(list(set(fouten)), 3) + [goed]; random.shuffle(opties)
        knoppen = [Knop(o, [100, 450, 100, 450][i], [200, 200, 350, 350][i], 250, 80, BLAUW, o) for i, o in enumerate(opties)]
        t_over, wachten, bevroren = float(quiz_tijd), True, False
        klok.tick()
        while wachten:
            dt = klok.tick(FPS)/1000.0
            if not bevroren: t_over -= dt
            scherm.fill(WIT); teken_tekst(f"Vertaal: {vraag}", font_titel, ZWART, 400, 50, center=True)
            pygame.draw.rect(scherm, GRIJS, (200, 110, 400, 15))
            if t_over > 0: pygame.draw.rect(scherm, GROEN, (200, 110, int(400*(max(0, t_over)/quiz_tijd)), 15))
            
            muis = pygame.mouse.get_pos()
            for k in knoppen: k.hover = k.rect.collidepoint(muis); k.teken(scherm)
            
            pknoppen = []
            if p_50: pknoppen.append(Knop("50/50", 50, 500, 100, 40, PAARS, "50"))
            if p_skip: pknoppen.append(Knop("SKIP", 160, 500, 100, 40, ORANJE, "skip"))
            if p_frz: pknoppen.append(Knop("FREEZE", 270, 500, 100, 40, (0,150,255), "frz"))
            for pk in pknoppen: pk.hover = pk.rect.collidepoint(muis); pk.teken(scherm)

            if t_over <= 0: activeer_willekeurige_jumpscare(); return
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SLASH: pauze_scherm()
                    if e.key == pygame.K_ESCAPE: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    for k in knoppen:
                        if k.rect.collidepoint(e.pos) and k.zichtbaar:
                            if k.actie == goed: wachten = False
                            else: activeer_willekeurige_jumpscare(); return
                    for pk in pknoppen:
                        if pk.rect.collidepoint(e.pos):
                            if pk.actie == "50": 
                                p_50, c = False, 0
                                for k in knoppen: 
                                    if k.actie != goed and c < 2: k.zichtbaar = False; c += 1
                            if pk.actie == "skip": p_skip, wachten = False, False
                            if pk.actie == "frz": p_frz, bevroren = False, True

def game_match():
    aantal = int(match_aantal); items = list(woordenlijst.items()); random.shuffle(items)
    while len(items) >= aantal:
        ronde = items[:aantal]; items = items[aantal:]; h = min(50, 400 // aantal)
        links = [Knop(w, 100, 100+i*(h+10), 250, h, BLAUW, w) for i, (w,v) in enumerate(ronde)]
        rechts = [Knop(v, 450, 100+i*(h+10), 250, h, PAARS, v) for i, (w,v) in enumerate(ronde)]
        random.shuffle(rechts); l_sel, r_sel = None, None
        for i, k in enumerate(rechts): k.rect.y = 100+i*(h+10)
        while any(k.zichtbaar for k in links):
            scherm.fill(ZWART)
            for k in links+rechts:
                if k.zichtbaar: k.hover = k.rect.collidepoint(pygame.mouse.get_pos()); k.teken(scherm)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SLASH: pauze_scherm()
                    if e.key == pygame.K_ESCAPE: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    for k in links+rechts:
                        if k.zichtbaar and k.rect.collidepoint(e.pos):
                            if k in links: 
                                if l_sel: l_sel.geselecteerd = False
                                l_sel = k; k.geselecteerd = True
                            else:
                                if r_sel: r_sel.geselecteerd = False
                                r_sel = k; k.geselecteerd = True
                    if l_sel and r_sel:
                        if woordenlijst[l_sel.actie] == r_sel.actie: l_sel.zichtbaar = r_sel.zichtbaar = False
                        else: l_sel.geselecteerd = r_sel.geselecteerd = False
                        l_sel = r_sel = None

def game_schieten():
    score, levens = 0, int(schieten_levens)
    while levens > 0:
        vraag = random.choice(list(woordenlijst.keys())); antwoord = woordenlijst[vraag].upper()
        idx, kogels, ballonnen = 0, [], [Ballon(l) for l in antwoord]
        for _ in range(10): ballonnen.append(Ballon(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")))
        bezig = True
        while bezig and levens > 0:
            scherm.fill(ZWART); muis_x = pygame.mouse.get_pos()[0]
            teken_tekst(f"Schiet de letters: {vraag}", font_tekst, GEEL, 20, 20)
            voortgang = "".join([l if i < idx else "_" for i, l in enumerate(antwoord)])
            teken_tekst(voortgang, font_titel, WIT, 20, 60)
            pygame.draw.rect(scherm, GROEN, (muis_x-25, 570, 50, 30))
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SLASH: pauze_scherm()
                    if e.key == pygame.K_ESCAPE: return
                if e.type == pygame.MOUSEBUTTONDOWN: kogels.append(pygame.Rect(muis_x-5, 550, 10, 20))
            for k in kogels[:]:
                k.y -= 10
                if k.y < 0: kogels.remove(k)
                else: pygame.draw.ellipse(scherm, GEEL, k)
            for b in ballonnen:
                b.update(); b.teken()
                for k in kogels[:]:
                    if k.colliderect(pygame.Rect(b.x-b.radius, b.y-b.radius, b.radius*2, b.radius*2)):
                        kogels.remove(k)
                        if b.letter == antwoord[idx]: 
                            idx += 1; b.y = -100
                            if idx >= len(antwoord): score += 50; bezig = False
                        else: activeer_willekeurige_jumpscare(); levens -= 1; bezig = False
            pygame.display.flip(); klok.tick(FPS)

def game_toets():
    global alle_lijsten, actieve_lijst_namen
    
    # 1. Update de actieve woorden op basis van vinkjes in de editor
    update_actieve_woorden()
    
    if not woordenlijst:
        scherm.fill(ZWART)
        teken_tekst("GEEN LIJSTEN GESELECTEERD", font_titel, ROOD, 400, 250, center=True)
        teken_tekst("Vink eerst lijsten aan in de Editor", font_tekst, WIT, 400, 320, center=True)
        pygame.display.flip()
        pygame.time.delay(2000)
        return

    # Vragen voorbereiden
    vragen = list(woordenlijst.keys())
    random.shuffle(vragen)
    
    index = 0
    input_text = ""
    fout_tekst = ""
    is_af = False
    toets_gehaald = False

    pygame.key.start_text_input()

    while True:
        nu = time.time()
        scherm.fill(ZWART)
        
        # Voortgangsbalk
        progress = (index / len(vragen)) * 800
        pygame.draw.rect(scherm, GRIJS, (0, 0, 800, 10))
        pygame.draw.rect(scherm, GROEN, (0, 0, progress, 10))

        if is_af:
            teken_tekst("FOUT!", font_titel, ROOD, 400, 250, center=True)
            teken_tekst(f"Het juiste antwoord was: {fout_tekst}", font_tekst, WIT, 400, 320, center=True)
            teken_tekst("Druk op een toets voor menu", font_klein, GRIJS, 400, 400, center=True)
            pygame.display.flip()
            
            wachten = True
            while wachten:
                for e in pygame.event.get():
                    if e.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]: wachten = False
            pygame.key.stop_text_input()
            return

        if toets_gehaald:
            teken_tekst("GEFELICITEERD!", font_titel, GROEN, 400, 150, center=True)
            teken_tekst("Je hebt de geselecteerde lijsten voltooid.", font_tekst, WIT, 400, 210, center=True)
            teken_tekst("Wil je de inhoud van deze lijsten wissen?", font_klein, GEEL, 400, 270, center=True)
            
            # Toon welke lijsten gewist gaan worden
            lijst_str = ", ".join(actieve_lijst_namen)
            teken_tekst(f"Lijsten: {lijst_str}", font_klein, GRIJS, 400, 300, center=True)

            k_ja = Knop("JA, WIS DEZE LIJSTEN", 150, 380, 240, 50, ROOD, "ja")
            k_nee = Knop("NEE, BEWAAR ZE", 410, 380, 240, 50, GRIJS, "nee")
            
            muis = pygame.mouse.get_pos()
            klik = False
            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN: klik = True
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            k_ja.hover = k_ja.rect.collidepoint(muis); k_ja.teken(scherm)
            k_nee.hover = k_nee.rect.collidepoint(muis); k_nee.teken(scherm)
            
            if klik:
                if k_ja.hover:
                    # Wis de inhoud van elke aangevinkte lijst
                    for naam in actieve_lijst_namen:
                        if naam in alle_lijsten:
                            alle_lijsten[naam] = {}
                    opslaan_woorden()
                    update_actieve_woorden()
                    pygame.key.stop_text_input()
                    return
                if k_nee.hover:
                    pygame.key.stop_text_input()
                    return
            
            pygame.display.flip()
            continue

        # Vraag stellen
        huidige_vraag = vragen[index]
        teken_tekst(f"Vraag {index + 1} van {len(vragen)}", font_klein, LICHTGRIJS, 400, 40, center=True)
        teken_tekst(f"Vertaal: {huidige_vraag}", font_titel, WIT, 400, 200, center=True)
        teken_tekst(f"Typ: {input_text}_", font_tekst, GEEL, 400, 300, center=True)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: pygame.key.stop_text_input(); return
                if e.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                if e.key == pygame.K_RETURN:
                    if input_text.strip().lower() == woordenlijst[huidige_vraag].lower():
                        index += 1
                        input_text = ""
                        if index >= len(vragen): toets_gehaald = True
                    else:
                        fout_tekst = woordenlijst[huidige_vraag]
                        is_af = True
            if e.type == pygame.TEXTINPUT:
                if not is_af: input_text += e.text

        pygame.display.flip()
        klok.tick(FPS)
        
# Voeg bovenaan bij je globale instellingen toe:
bot_moeilijkheid = 0.5 

# Voeg deze twee variabelen toe aan je Globale Instellingen bovenin je script
speler_score = 0
bot_score = 0

def check_winnaar_bke(bord):
    # Alle mogelijke winnende combinaties (indexen van de lijst)
    win_patronen = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), # Horizontaal
        (0, 3, 6), (1, 4, 7), (2, 5, 8), # Verticaal
        (0, 4, 8), (2, 4, 6)             # Diagonaal
    ]

    for p in win_patronen:
        if bord[p[0]] == bord[p[1]] == bord[p[2]] != "":
            return bord[p[0]] # Geeft "X" of "O" terug

    # Check voor gelijkspel (als er geen lege plekken meer zijn)
    if "" not in bord:
        return "Gelijk"

    return None

def game_bke():
    global bot_snelheid, speler_score, bot_score, bot_moeilijkheid
    update_actieve_woorden()
    
    if not woordenlijst:
        scherm.fill(ZWART)
        teken_tekst("GEEN WOORDEN GELADEN", font_titel, ROOD, 400, 300, center=True)
        pygame.display.flip(); pygame.time.delay(2000)
        return
    
    bord = ["" for _ in range(9)]
    beurt_speler = False  
    vraag_woord = random.choice(list(woordenlijst.keys()))
    input_text = ""
    last_bot_move = time.time()
    penalty_einde = 0
    fout_tekst = ""
    winnaar = None

    pygame.key.start_text_input()

    running = True
    while running:
        scherm.fill(ZWART)
        nu = time.time()
        muis = pygame.mouse.get_pos()

        # 1. Teken het BKE-raster
        for i in range(9):
            x = 250 + (i % 3) * 105
            y = 150 + (i // 3) * 105
            rect = pygame.Rect(x, y, 100, 100)
            pygame.draw.rect(scherm, GRIJS, rect)
            if bord[i] == "X": teken_tekst("X", font_titel, BLAUW, x+50, y+50, center=True)
            if bord[i] == "O": teken_tekst("O", font_titel, ROOD, x+50, y+50, center=True)

        # 2. UI en Informatie
        bot_tijd_verstreken = nu - last_bot_move
        bot_tijd_over = max(0, int(bot_snelheid - bot_tijd_verstreken))
        
        teken_tekst(f"Vertaal: {vraag_woord}", font_tekst, WIT, 400, 50, center=True)
        teken_tekst(f"Bot zet over: {bot_tijd_over}s", font_klein, WIT, 400, 500, center=True)
        teken_tekst(f"JIJ: {speler_score} - BOT: {bot_score}", font_klein, GEEL, 400, 530, center=True)

        if nu < penalty_einde:
            teken_tekst(f"PENALTY: {int(penalty_einde - nu)}s", font_tekst, ROOD, 400, 100, center=True)
            teken_tekst(f"Antwoord was: {fout_tekst}", font_klein, ORANJE, 400, 130, center=True)
        elif beurt_speler:
            teken_tekst("GOED! KLIK OP EEN VAKJE", font_tekst, GROEN, 400, 100, center=True)
        else:
            teken_tekst(f"Typ: {input_text}_", font_tekst, GEEL, 400, 100, center=True)

        # 3. Bot Logica
        if not beurt_speler and bot_tijd_verstreken >= bot_snelheid and not winnaar:
            zet = slimme_bot_zet(bord, bot_moeilijkheid)
            if zet is not None:
                bord[zet] = "O"
                last_bot_move = nu
                winnaar = check_winnaar_bke(bord)

        # 4. Winnaar afhandeling
        if winnaar:
            if winnaar == "X": speler_score += 1; tekst = "JIJ WINT!"
            elif winnaar == "O": bot_score += 1; tekst = "BOT WINT!"
            else: tekst = "GELIJKSPEL!"
            teken_tekst(tekst, font_titel, GROEN, 400, 300, center=True)
            pygame.display.flip(); pygame.time.delay(2000)
            running = False

        # 5. Events
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            # Toetsenbord acties
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                
                if e.key == pygame.K_SLASH:
                    pauze_scherm()
                    last_bot_move = time.time() - bot_tijd_verstreken # Timer herstellen

                if nu > penalty_einde and not beurt_speler:
                    if e.key == pygame.K_TAB:
                        fout_tekst = woordenlijst.get(vraag_woord, "???")
                        penalty_einde = nu + 10 # De 10 seconden straf
                        vraag_woord = random.choice(list(woordenlijst.keys()))
                        input_text = ""
                    
                    if e.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                    
                    if e.key == pygame.K_RETURN:
                        if input_text.strip().lower() == woordenlijst.get(vraag_woord, "").lower():
                            beurt_speler = True
                        else:
                            activeer_willekeurige_jumpscare()
                        input_text = ""

            # Tekst invoer
            if e.type == pygame.TEXTINPUT and not beurt_speler and nu > penalty_einde:
                if e.text not in ["/", "\t"]: input_text += e.text

            # Muisklikken (Vakje kiezen)
            if e.type == pygame.MOUSEBUTTONDOWN and beurt_speler and not winnaar:
                for i in range(9):
                    x = 250 + (i % 3) * 105
                    y = 150 + (i // 3) * 105
                    vak_rect = pygame.Rect(x, y, 100, 100)
                    if vak_rect.collidepoint(e.pos) and bord[i] == "":
                        bord[i] = "X"
                        beurt_speler = False
                        winnaar = check_winnaar_bke(bord)
                        vraag_woord = random.choice(list(woordenlijst.keys()))
                        last_bot_move = time.time()

        pygame.display.flip()
        klok.tick(FPS)
    pygame.key.stop_text_input()

def game_flash():
    items = list(woordenlijst.items()); random.shuffle(items)
    for w, v in items:
        toon = False
        while True:
            scherm.fill(ZWART); pygame.draw.rect(scherm, GRIJS, (100, 150, 600, 250), border_radius=15)
            teken_tekst(w, font_titel, WIT, 400, 230, center=True)
            if toon: teken_tekst(v, font_tekst, GROEN, 400, 320, center=True)
            btn = Knop("Volgende" if toon else "Toon", 300, 450, 200, 60, BLAUW, "ok")
            btn.hover = btn.rect.collidepoint(pygame.mouse.get_pos()); btn.teken(scherm)
            pygame.display.flip()
            e = pygame.event.wait()
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return
                if e.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    if not toon: toon = True
                    else: break
            if e.type == pygame.MOUSEBUTTONDOWN and btn.rect.collidepoint(e.pos):
                if not toon: toon = True
                else: break

def editor_scherm():
    global alle_lijsten, actieve_lijst_namen
    running = True
    geselecteerde_lijst = list(alle_lijsten.keys())[0] if alle_lijsten else None
    
    # Input variabelen
    input_nl = ""
    input_en = ""
    input_lijst_naam = geselecteerde_lijst if geselecteerde_lijst else ""
    actief_veld = "nl"
    
    # SCROLL VARIABELEN
    scroll_woorden = 0
    max_zichtbaar_woorden = 12 
    
    scroll_lijsten = 0
    max_zichtbaar_lijsten = 9  # Aantal lijsten dat links in beeld past

    while running:
        scherm.fill((20, 20, 20))
        muis = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        # --- 1. TITEL ---
        teken_tekst("WOORDEN & LIJSTEN BEHEREN", font_titel, GEEL, 400, 30, center=True)

        # --- 2. LINKER KOLOM: LIJSTEN (MET SCROLL) ---
        pygame.draw.rect(scherm, GRIJS, (20, 70, 200, 420), border_radius=10)
        
        alle_namen = list(alle_lijsten.keys())
        teken_tekst(f"Lijsten ({len(alle_namen)})", font_tekst, WIT, 30, 80)
        
        # Scroll indicator lijsten
        if len(alle_namen) > max_zichtbaar_lijsten:
             teken_tekst(f"Scroll: {scroll_lijsten}-{min(scroll_lijsten+max_zichtbaar_lijsten, len(alle_namen))}", font_klein, (200,200,200), 130, 85)

        y_lijst = 120
        # Slice de lijsten op basis van scroll positie
        zichtbare_lijsten = alle_namen[scroll_lijsten : scroll_lijsten + max_zichtbaar_lijsten]

        for naam in zichtbare_lijsten:
            l_rect = pygame.Rect(30, y_lijst, 180, 35)
            l_kleur = GEEL if naam == geselecteerde_lijst else (100, 100, 100)
            pygame.draw.rect(scherm, l_kleur, l_rect, border_radius=5)
            
            t_kleur = ZWART if naam == geselecteerde_lijst else WIT
            teken_tekst(naam, font_klein, t_kleur, 40, y_lijst + 8)
            
            v_rect = pygame.Rect(185, y_lijst + 10, 15, 15)
            v_kleur = GROEN if naam in actieve_lijst_namen else ROOD
            pygame.draw.rect(scherm, v_kleur, v_rect)

            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if l_rect.collidepoint(e.pos): 
                        geselecteerde_lijst = naam
                        input_lijst_naam = naam
                        scroll_woorden = 0 # Reset woord-scroll als je van lijst wisselt
                    if v_rect.collidepoint(e.pos):
                        if naam in actieve_lijst_namen: actieve_lijst_namen.remove(naam)
                        else: actieve_lijst_namen.append(naam)
            y_lijst += 40

        btn_nieuwe_lijst = Knop("+ NIEUWE LIJST", 20, 510, 200, 40, BLAUW, "nieuw_lijst")
        btn_nieuwe_lijst.hover = btn_nieuwe_lijst.rect.collidepoint(muis)
        btn_nieuwe_lijst.teken(scherm)

        # --- 3. MIDDELSTE KOLOM: WOORDEN (MET SCROLL) ---
        pygame.draw.rect(scherm, (40, 40, 40), (240, 70, 280, 480), border_radius=10)
        if geselecteerde_lijst:
            woorden_items = list(alle_lijsten[geselecteerde_lijst].items())
            totaal_woorden = len(woorden_items)
            
            teken_tekst(f"Inhoud ({totaal_woorden})", font_tekst, WIT, 250, 80)
            
            # Scroll indicator woorden
            if totaal_woorden > max_zichtbaar_woorden:
                teken_tekst(f"Scroll: {scroll_woorden}-{min(scroll_woorden+max_zichtbaar_woorden, totaal_woorden)}", font_klein, (200,200,200), 450, 85)

            y_woord = 120
            zichtbare_items = woorden_items[scroll_woorden : scroll_woorden + max_zichtbaar_woorden]

            for nl, en in zichtbare_items:
                w_rect = pygame.Rect(250, y_woord, 260, 30)
                pygame.draw.rect(scherm, (60, 60, 60), w_rect)
                teken_tekst(f"{nl} = {en}", font_klein, WIT, 260, y_woord + 5)
                
                d_rect = pygame.Rect(485, y_woord + 5, 20, 20)
                pygame.draw.rect(scherm, ROOD, d_rect)
                
                for e in events:
                    if e.type == pygame.MOUSEBUTTONDOWN and d_rect.collidepoint(e.pos):
                        del alle_lijsten[geselecteerde_lijst][nl]
                        opslaan_woorden()
                        if scroll_woorden > 0 and len(alle_lijsten[geselecteerde_lijst]) <= scroll_woorden:
                            scroll_woorden -= 1
                y_woord += 35

        # --- 4. RECHTER KOLOM: ACTIES ---
        teken_tekst("Lijst Naam", font_tekst, GEEL, 540, 80)
        rect_lijst_naam = pygame.Rect(540, 110, 220, 35)
        pygame.draw.rect(scherm, WIT if actief_veld == "lijst_naam" else GRIJS, rect_lijst_naam)
        teken_tekst(input_lijst_naam, font_klein, ZWART, 550, 118)

        teken_tekst("Nieuw Woord", font_tekst, GEEL, 540, 170)
        rect_nl = pygame.Rect(540, 200, 220, 35)
        rect_en = pygame.Rect(540, 260, 220, 35)
        
        pygame.draw.rect(scherm, WIT if actief_veld == "nl" else GRIJS, rect_nl)
        pygame.draw.rect(scherm, WIT if actief_veld == "en" else GRIJS, rect_en)
        
        teken_tekst(f"NL: {input_nl}", font_klein, ZWART, 550, 208)
        teken_tekst(f"EN: {input_en}", font_klein, ZWART, 550, 268)
        
        btn_voeg_toe = Knop("VOEG TOE [ENTER]", 540, 310, 220, 40, GROEN, "add")
        btn_voeg_toe.hover = btn_voeg_toe.rect.collidepoint(muis)
        btn_voeg_toe.teken(scherm)

        btn_del_lijst = Knop("WIS DEZE LIJST", 540, 510, 220, 40, DONKERROOD, "del")
        btn_del_lijst.hover = btn_del_lijst.rect.collidepoint(muis)
        btn_del_lijst.teken(scherm)

        # --- 5. EVENTS ---
        for e in events:
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            # --- SCROLL LOGICA (SLIMME DETECTIE) ---
            if e.type == pygame.MOUSEWHEEL:
                # 1. Scrollen in LIJSTEN (Linkerkant: muis X < 230)
                if muis[0] < 230:
                    scroll_lijsten -= e.y
                    max_scroll_lijst = max(0, len(alle_lijsten) - max_zichtbaar_lijsten)
                    scroll_lijsten = max(0, min(scroll_lijsten, max_scroll_lijst))

                # 2. Scrollen in WOORDEN (Midden: muis X tussen 240 en 520)
                elif 240 < muis[0] < 520 and geselecteerde_lijst:
                    scroll_woorden -= e.y 
                    max_scroll_woord = max(0, len(alle_lijsten[geselecteerde_lijst]) - max_zichtbaar_woorden)
                    scroll_woorden = max(0, min(scroll_woorden, max_scroll_woord))

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                
                # TAB wisselt velden (zonder tekst input)
                if e.key == pygame.K_TAB: 
                    if actief_veld == "nl": actief_veld = "en"
                    elif actief_veld == "en": actief_veld = "lijst_naam"
                    else: actief_veld = "nl"
                    continue 

                if e.key == pygame.K_BACKSPACE:
                    if actief_veld == "nl": input_nl = input_nl[:-1]
                    elif actief_veld == "en": input_en = input_en[:-1]
                    elif actief_veld == "lijst_naam": input_lijst_naam = input_lijst_naam[:-1]
                
                elif e.key == pygame.K_RETURN:
                    if actief_veld == "lijst_naam":
                        if input_lijst_naam and input_lijst_naam not in alle_lijsten:
                            alle_lijsten[input_lijst_naam] = alle_lijsten.pop(geselecteerde_lijst)
                            if geselecteerde_lijst in actieve_lijst_namen:
                                actieve_lijst_namen.remove(geselecteerde_lijst)
                                actieve_lijst_namen.append(input_lijst_naam)
                            geselecteerde_lijst = input_lijst_naam
                            opslaan_woorden()
                    else: 
                        if input_nl and input_en and geselecteerde_lijst:
                            alle_lijsten[geselecteerde_lijst][input_nl] = input_en
                            input_nl, input_en = "", ""
                            opslaan_woorden()
                            actief_veld = "nl"
                            # Auto-scroll woorden
                            totaal = len(alle_lijsten[geselecteerde_lijst])
                            if totaal > max_zichtbaar_woorden:
                                scroll_woorden = totaal - max_zichtbaar_woorden
                else:
                    if e.key != pygame.K_TAB:
                        if actief_veld == "nl": input_nl += e.unicode
                        elif actief_veld == "en": input_en += e.unicode
                        elif actief_veld == "lijst_naam": input_lijst_naam += e.unicode

            if e.type == pygame.MOUSEBUTTONDOWN:
                if rect_nl.collidepoint(e.pos): actief_veld = "nl"
                if rect_en.collidepoint(e.pos): actief_veld = "en"
                if rect_lijst_naam.collidepoint(e.pos): actief_veld = "lijst_naam"
                
                if btn_nieuwe_lijst.rect.collidepoint(e.pos):
                    nieuwe_naam = f"Lijst {len(alle_lijsten)+1}"
                    counter = 1
                    while nieuwe_naam in alle_lijsten:
                        nieuwe_naam = f"Lijst {len(alle_lijsten)+1}_{counter}"
                        counter += 1     
                    alle_lijsten[nieuwe_naam] = {}
                    geselecteerde_lijst = nieuwe_naam
                    input_lijst_naam = nieuwe_naam
                    opslaan_woorden()
                    
                    # Auto-scroll naar de nieuwe lijst
                    scroll_lijsten = max(0, len(alle_lijsten) - max_zichtbaar_lijsten)
                    scroll_woorden = 0

                if btn_voeg_toe.rect.collidepoint(e.pos):
                    if input_nl and input_en and geselecteerde_lijst:
                        alle_lijsten[geselecteerde_lijst][input_nl] = input_en
                        input_nl, input_en = "", ""
                        opslaan_woorden()
                        actief_veld = "nl"

                if btn_del_lijst.rect.collidepoint(e.pos):
                    if len(alle_lijsten) > 1:
                        del alle_lijsten[geselecteerde_lijst]
                        geselecteerde_lijst = list(alle_lijsten.keys())[0]
                        input_lijst_naam = geselecteerde_lijst
                        scroll_lijsten = 0 # Reset scroll om crash te voorkomen
                        opslaan_woorden()

        pygame.display.flip()
        klok.tick(FPS)

# --- HOOFDMENU ---
def hoofdmenu():
    global regen_snelheid, regen_frequentie, quiz_tijd, bot_snelheid, schieten_levens, bot_moeilijkheid, match_aantal
    
    # Sliders configureren met de nieuwe waarden:
    # regen_snelheid van 0.1 tot 2.5
    s_regen_speed = Slider(300, 90, 140, 0.1, 2.5, regen_snelheid, "Snelheid")
    # regen_frequentie van 100 tot 500 (hoger = meer pauze tussen woorden)
    s_regen_freq  = Slider(460, 90, 140, 100, 500, regen_frequentie, "Pauze")
    
    s_quiz        = Slider(300, 140, 140, 3, 30, quiz_tijd, "Tijd")
    s_match       = Slider(300, 190, 140, 3, 15, match_aantal, "Paren")
    s_schiet      = Slider(300, 240, 140, 1, 10, schieten_levens, "Levens")
    s_bke_speed   = Slider(300, 290, 140, 5, 30, bot_snelheid, "Bot Tijd")
    s_vier_speed  = Slider(300, 340, 140, 5, 30, bot_snelheid, "Bot Tijd")

    s_bke_smart   = Slider(460, 290, 140, 0.0, 1.0, bot_moeilijkheid, "Slimheid")
    s_vier_smart  = Slider(460, 340, 140, 0.0, 1.0, bot_moeilijkheid, "Slimheid")

    knoppen = [
        Knop("Regen", 50, 80, 220, 40, GROEN, "r"),
        Knop("Quiz", 50, 130, 220, 40, ORANJE, "q"),
        Knop("Match", 50, 180, 220, 40, BLAUW, "m"),
        Knop("Schieten", 50, 230, 220, 40, PAARS, "s"),
        Knop("Boter-Kaas", 50, 280, 220, 40, ROOD, "bke"),
        Knop("Vier op Rij", 50, 330, 220, 40, BLAUW, "vier"),
        Knop("Toets", 50, 380, 220, 40, GEEL, "t"),
        Knop("Editor", 50, 450, 220, 40, LICHTGRIJS, "e"),
        Knop("Quit", 50, 510, 220, 40, GRIJS, "quit")
    ]
    
    while True:
        scherm.fill(ZWART)
        muis = pygame.mouse.get_pos()
        klik = False
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1: klik = True
            
        # Sliders updaten
        regen_snelheid   = s_regen_speed.update(muis, klik); s_regen_speed.teken()
        regen_frequentie = s_regen_freq.update(muis, klik); s_regen_freq.teken()
        quiz_tijd        = s_quiz.update(muis, klik); s_quiz.teken()
        match_aantal     = s_match.update(muis, klik); s_match.teken()
        schieten_levens  = s_schiet.update(muis, klik); s_schiet.teken()
        bot_snelheid     = s_bke_speed.update(muis, klik); s_bke_speed.teken()
        bot_moeilijkheid = s_bke_smart.update(muis, klik); s_bke_smart.teken()
        
        # Synchroniseer de Vier-op-een-Rij waarden met dezelfde variabelen
        bot_snelheid     = s_vier_speed.update(muis, klik); s_vier_speed.teken()
        bot_moeilijkheid = s_vier_smart.update(muis, klik); s_vier_smart.teken()

        teken_tekst("WORD TRAINER PRO", font_titel, WIT, 400, 30, center=True)

        for k in knoppen:
            k.hover = k.rect.collidepoint(muis)
            k.teken(scherm)
            if klik and k.hover:
                if k.actie == "r": woordenregen()
                elif k.actie == "q": game_quiz()
                elif k.actie == "m": game_match()
                elif k.actie == "s": game_schieten()
                elif k.actie == "bke": game_bke()
                elif k.actie == "vier": game_vier()
                elif k.actie == "t": game_toets()
                elif k.actie == "e": editor_scherm()
                elif k.actie == "quit": pygame.quit(); sys.exit()

        pygame.display.flip()
        klok.tick(FPS)

if __name__ == "__main__":
    # INITIALISATIE
    woordenlijst = {}
    laden_woorden() # Laad de dictionary uit woorden.txt

    # START HET MENU
    hoofdmenu()
