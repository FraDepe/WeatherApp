import datetime

frasi = [
        "Com'è il tempo oggi sull'Everest",
        "Com'è il tempo dopodomani sull'Everest",
        "Com'è il tempo a Roma oggi", 
        "Com'è il tempo a mezzogiorno sul monte", 
        "Com'è il tempo domani a Sant'Agostino",
        "Com'è il tempo martedì a Casal Monastero", 
        "Com'è il tempo a Casal Monastero martedì", 
        "Com'è il tempo oggi alle 14 ai Parioli",     
        "Com'è il tempo tra 3 giorni alle 17:30 all'Eur", 
        "Com'è il tempo mercoledì alle 19 a Colle Dell'oro"
        ]


def extractLocation(frase):
    if " a " in frase:
        return frase[frase.find(" a ")+3:]
    elif " all'" in frase:
        return frase[frase.find(" all'")+5:]
    elif " ad " in frase:
        return frase[frase.find(" ad ")+4:]
    elif " ai " in frase:
        return frase[frase.find(" ai ")+4:]
    elif " sull'" in frase:
        return frase[frase.find(" sull'")+6:]
    elif " sul " in frase:
        return frase[frase.find(" sul ")+5:]


def diffInDays(day):
    today = datetime.date.today()
    diff = 0
    while day != today.strftime("%A"):
        diff += 1
        today = today + datetime.timedelta(1)
    return diff     #Funzione chiamata per controllare che si arrivi massimo a 4 (se passano più di 4 giorni non possiamo prevedere il tempo)
    


#handle l'una mezzanotte mezzogiorno
#handle 13:00 14:30 15:12 
def extractTime(frase):
    orario = -1
    giorno = datetime.date.today().strftime("%A")

    if "l'una" in frase:
        orario = "01:00"
    elif "mezzanotte" in frase:
        orario = "00"
    elif "mezzogiorno" in frase:
        orario = "12"

    if orario == -1:    # Faccio solo se l'orario non è ancora stato definito
        parole = frase.split(" ")
        for parola in parole:
            if parola.isdigit():
                orario = parola
            elif ":" in parola:
                orario = parola

    if "oggi" in frase:
        pass
    elif "dopodomani" in frase or "tra due giorni" in frase or "fra due giorni" in frase or "tra 2 giorni" in frase or "fra 2 giorni" in frase:
        giorno = (datetime.date.today() + datetime.timedelta(2)).strftime("%A")
    elif "domani" in frase or "tra un giorno" in frase or "fra un giorno" in frase or "tra 1 giorno" in frase or "fra 1 giorno" in frase:
        giorno = (datetime.date.today() + datetime.timedelta(1)).strftime("%A")
    elif "tra tre giorni" in frase or "fra tre giorni" in frase or "tra 3 giorni" in frase or "fra 3 giorni" in frase:
        giorno = (datetime.date.today() + datetime.timedelta(3)).strftime("%A")
    elif "tra quattro giorni" in frase or "fra quattro giorni" in frase or "tra 4 giorni" in frase or "fra 4 giorni" in frase:
        giorno = (datetime.date.today() + datetime.timedelta(4)).strftime("%A")
    elif " tra " in frase or " fra " in frase:
        giorno = None
    elif "luned" in frase:
        giorno = "Monday"
    elif "marted" in frase:
        giorno = "Tuesday"
    elif "mercoled" in frase:
        giorno = "Wednesday"
    elif "gioved" in frase:
        giorno = "Thursday"
    elif "venerd" in frase:
        giorno = "Friday"
    elif "sabato" in frase:
        giorno = "Saturday"
    elif "domenica" in frase:
        giorno = "Sunday"
    else:
        pass
    return (giorno, orario)


#for x in range(len(frasi)):
#    print(f"{frasi[x]}  {extractTime(frasi[x])[0]}")

#print(diffInDays("Friday"))

    # day = ""        # Opzionale (default è datetime.datetime.today())
    # hour = ""       # Opzionale
    # location = ""   # Obbligatoria


#frase --> Il tempo a {roma} {martedi/oggi} sarà {soleggiato} con una temperatura media di {17} gradi. 
#          Il tempo a {self.location}, {self.day} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp}


time = datetime.datetime.fromtimestamp(1697036400)

#print(str(time + datetime.timedelta(hours=1)).split(" ")[1])
#print("17:00" in str(datetime.datetime.fromtimestamp(1697036400)))
# hour = "24:00"
# available_hours = ("02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00")
# if hour < available_hours[0] or hour > available_hours[-1]:
#         print(available_hours[0])
# for x in range(0, len(available_hours)-1):
#     if hour > available_hours[x] and hour < available_hours[x+1]:
#         print(available_hours[x+1])

print(str(time)[11:16] >= "17:00")

