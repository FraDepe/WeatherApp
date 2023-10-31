from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.gridlayout import MDGridLayout 
from kivy.base import EventLoop
from kivymd.uix.dialog import MDDialog
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
import datetime
from plyer import tts, stt


##############################################################################################


class MainPage(Screen):
    
    sentence = ""
    sentences = ""
    dialog = None
    talked = False


    # Funzione eseguita all'avvio dell'applicazione
    def on_start(self): 
        EventLoop.window.bind(on_keyboard=self.key_pressed)

    def on_enter(self):
        if not self.talked:
            try:
                tts.speak("Per effettuare una richiesta, toccare lo schermo e aspettare il segnale acustico. Per entrare nella modalità per non vedenti, aggiungere ad inizio richiesta, non vedente. È necessario specificare la località a fine frase. Previsioni disponibili fino a 5 giorni compreso oggi.")
                self.talked = True
            except NotImplementedError:
                self.openAlertDialog()

    # Funzione eseguita alla pressione del microfono per cominciare ad eseguire le funzione dello stt    
    def listenToSearch(self):        
        self.start_listening()


    # Funzione che esegue l'engine vocale per il riconoscimento delle frasi
    def start_listening(self):
        self.sentence = ""
        try:
            stt.start()
            Clock.schedule_interval(self.check_state, 4 / 5)
        except NotImplementedError:
            self.openAlertDialog()
        except:
            tts.speak("Qualcosa è andato storto. Riprova")


    # Funzione eseguita una volta che l'engine ha rilevato che nessuno sta parlando
    def stop_listening(self):      
        stt.stop()
        self.update()
        Clock.unschedule(self.check_state)

        if self.sentences == []:
            self.noSentences()
            return
        self.sentence = self.sentences[0]

        if "non vedente" in self.sentence or "Non vedente" in self.sentence:
            self.manager.current = 'forecastblind'
            self.manager.transition.direction = 'left'
        else:
            self.manager.current = 'forecast'
            self.manager.transition.direction = 'left'
        return


    # Funzione chiamata in loop mentre l'engine ascolta per controllare se si sta ancora parlando o no
    def check_state(self, dt):
        if not stt.listening:
            self.stop_listening()


    # Funzione chiamata per ottenere la frase catturata dall'engine
    def update(self):
        self.sentences = stt.results


    # Funzione che binda il back button di android per chiudere l'app
    def key_pressed(self, window, key, *args):
        if key == 27:
            if self.manager.current == 'forecast':
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                return True
            return False


    # Funzione eseguita in caso di errore da parte dell'engine vocale
    def openAlertDialog(self):
        self.dialog = MDDialog(
            text="Non è stato trovato nessun engine vocale"
        )
        self.dialog.open()


    # Funzione chiamata in caso non sia stata catturata nessuna frase
    def noSentences(self):
        tts.speak("Non ho capito, ripetere per favore")


##############################################################################################


class ForecastPage(Screen):

    response_today = None
    response_forecast = None
    latitude = ""
    longitude = ""
    sentence = ""
    sentences = ""
    day = ""                # Opzionale di default datetime.datetime.today().strftime("%A") 
    hour = ""               # Opzionale (-1 se non specificato)
    location = ""           # Obbligatorio


    # Funzione chiamata all'avvio della nuova pagina e si occupa di popolarla di widget
    def on_enter(self):     

        EventLoop.window.bind(on_keyboard=self.key_pressed)

        self.sentence = self.manager.get_screen("main").sentence # Prendo la frase da esaminare

        self.location = self.extractLocation(self.sentence)

        if self.location == None:
            tts.speak("Non ho capito in quale località. Riprova")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        self.day, self.hour = self.extractTime(self.sentence)
        if self.day == 0: 
            self.day = datetime.date.today().strftime("%A") 

        if type(self.hour) == str:
            if not self.check_hour(self.hour):
                tts.speak("Orario non valido. Riprova")
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                return

        print(self.sentence)
        print(self.location)
        print(self.day)
        print(self.hour)
        print(self.diffInDays(self.day))

        if self.diffInDays(self.day) > 4:
            tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return
        elif self.diffInDays(self.day) == -1:
            tts.speak("Specificare un giorno del mese valido")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        UrlRequest(f"http://api.openweathermap.org/geo/1.0/direct?q={self.location.replace(' ', '+')}&limit=1&appid=c0b583a8bb8b03e64dd0e16bccda95bf", on_success=self.gotCoordinates, on_error=self.gotAnError, on_failure=self.gotAnError)
        
        return 
    

    # Funzione chiamata se la UrlRequest per le coordinate va a buon fine
    def gotCoordinates(self, req, r):
        if r == []:
            self.gotNoCoordinates()
            return
        self.latitude = r[0]['lat']
        self.longitude = r[0]['lon']
        self.ids['topappbar'].title = self.location
        
        UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={str(self.latitude)}&lon={str(self.longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric", on_success=self.gotWeatherToday, on_error=self.gotAnError, on_failure=self.gotAnError)


    # Funzione chiamata se la UrlRequest per la previsione di oggi va a buon fine
    def gotWeatherToday(self, req, r):
        if r == []:
            self.gotAnError(req, r)
            return
        self.response_today=r
        UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat={str(self.latitude)}&lon={str(self.longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric", on_success=self.gotWeatherForecast, on_error=self.gotAnError, on_failure=self.gotAnError)


    # Funzione chiamata se la UrlRequest per la previsione
    def gotWeatherForecast(self, req, r):
        if r == []:
            self.gotAnError(req, r)
            return
        self.response_forecast=r

        self.getToday(self.response_today, self.response_forecast)
        self.responseToAudio()
        return


    # Funzione che esegue l'engine vocale per il riconoscimento delle frasi
    def new_request(self):
        self.sentence = ""
        try:
            stt.start()
            Clock.schedule_interval(self.check_state, 4 / 5)
        except NotImplementedError:
            self.openAlertDialog()
        except:
            tts.speak("Qualcosa è andato storto. Riprova")


    # Funzione eseguita una volta che l'engine ha rilevato che nessuno sta parlando
    def stop_listening_for_new_request(self):      
        stt.stop()
        self.update()
        Clock.unschedule(self.check_state)

        if self.sentences == []:
            self.noSentences()
            return
        
        self.sentence = self.sentences[0]

        new_day, new_hour = self.extractTime(self.sentence) 

        if new_day == -1:
            tts.speak("Giorno non valido.")
            return
        elif new_day == None:
            tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
            return
        if new_day != 0:
            if self.diffInDays(new_day) > 4:
                tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
                return

        if type(self.hour) == str:
            if not self.check_hour(self.hour):
                tts.speak("Orario non valido")
                return

        print(new_day, new_hour)

        # add check on day and hour

        if new_hour != -1 and new_day != 0:
            self.day = new_day
            self.newAudioResponse(new_hour, new_day) 
        elif new_hour != -1: 
            self.newAudioResponse(new_hour, None) 
        elif new_day != 0:
            self.day = new_day
            self.newAudioResponse(None, new_day) 
        else: 
            tts.speak("Non ho capito, riprova") 
        return


    # Funzione per il nuovo response audio
    def newAudioResponse(self, hour, day):        
        # dovrei modificare getGeneralWeather e quell'altra in modo che prenda valori hour e day da input e non dalla classe
        if hour == None:
            main_weather, main_temp, main_wind, main_hum = self.getGeneralWeather(day)
            frase = f"{self.dayTranslate(day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi e con {self.windTranslate(main_wind)}"

        elif day == None:
            if type(hour) != list:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, self.day)
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"
            else:
                list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
                if hour[0] < str(datetime.datetime.now())[11:16] and self.day == datetime.date.today().strftime("%A"):
                    frase = "La fascia oraria richiesta è già passata"
                else:
                    for orario in hour:
                        temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                        list_weather.append(temp_weather)
                        list_temp.append(temp_temp)
                        list_wind.append(temp_wind)
                        list_hum.append(temp_hum)
                    
                    main_temp = round(sum(list_temp)/2)
                    main_wind = round(sum(list_wind)/2)
                    main_hum = round(sum(list_hum)/2)

                    if "07:00" in hour:
                        fascia_oraria = "in mattinata"
                    elif "13:00" in hour:
                        fascia_oraria = "pomeriggio"
                    else:
                        fascia_oraria = "in serata"

                    weather1 = self.weatherTranslate(list_weather[0])
                    weather2 = self.weatherTranslate(list_weather[1])
                    if weather1 != weather2:
                        result_weather = "prima " + weather1 + " e poi " + weather2
                    else:
                        result_weather = weather1
                    if "temperatura" not in self.sentence:
                        frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}."
                    else:
                        frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità."

        else:
            if type(hour) != list:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, day)
                frase = f"{self.dayTranslate(day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"
            else:
                list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
                if hour[0] < str(datetime.datetime.now())[11:16] and day == datetime.date.today().strftime("%A"):
                    frase = "La fascia oraria richiesta è già passata"
                else:
                    for orario in hour:
                        temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, day)
                        list_weather.append(temp_weather)
                        list_temp.append(temp_temp)
                        list_wind.append(temp_wind)
                        list_hum.append(temp_hum)
                    
                    main_temp = round(sum(list_temp)/2)
                    main_wind = round(sum(list_wind)/2)
                    main_hum = round(sum(list_hum)/2)

                    if "07:00" in hour:
                        fascia_oraria = "in mattinata"
                    elif "13:00" in hour:
                        fascia_oraria = "pomeriggio"
                    else:
                        fascia_oraria = "in serata"

                    weather1 = self.weatherTranslate(list_weather[0])
                    weather2 = self.weatherTranslate(list_weather[1])
                    if weather1 != weather2:
                        result_weather = "prima " + weather1 + " e poi " + weather2
                    else:
                        result_weather = weather1
                    if "temperatura" not in self.sentence:
                        frase = f"{self.dayTranslate(day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}."
                    else:
                        frase = f"{self.dayTranslate(day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità."

        tts.speak(frase)
        return 


    # Funzione chiamata in loop mentre l'engine ascolta per controllare se si sta ancora parlando o no
    def check_state(self, dt):
        if not stt.listening:
            self.stop_listening_for_new_request()


    # Funzione chiamata per ottenere la frase catturata dall'engine
    def update(self):
        self.sentences = stt.results


    # Funzione chiamata in caso non sia stata catturata nessuna frase
    def noSentences(self):
        tts.speak("Non ho capito, ripetere per favore")
        return


    # Funzione chiamata in caso di località non trovata
    def gotNoCoordinates(self):
        tts.speak("Località non trovata")
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        return


    # Funzione chiamata in caso di errore da parte della UrlRequest
    def gotAnError(self, req, r):
        tts.speak("C'è stato un errore con la richiesta al servizio per le previsioni. Riprova")
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        return


    # Fuzione che crea e inserisce i vari ExpansionPanel con le previsioni
    def getToday(self, result_today, result_forecast):
        print(self.sentence)

        self.ids['today_icon'].source = self.getIcon(result_today['weather'][0]['description'], result_today['weather'][0]['main'], result_today['dt'])
        
        for x in result_forecast['list']:
            info = HourlyForecast()
            panel = MDExpansionPanel(
                content = info,
                
                icon = self.getIcon(x['weather'][0]['description'], x['weather'][0]['main'], x['dt']),
                panel_cls = MDExpansionPanelOneLine(
                    text = self.getDay(x['dt'])
                ),
            )
            info.ids['humid'].text = str(x['main']['humidity']) + "%"
            info.ids['temp'].text = str(round(x['main']['temp'])) + "°C"
            info.ids['press'].text = str(x['main']['pressure']) + " hPa"
            info.ids['wind'].text = str(round(x['wind']['speed']*3.6)) + " Km/h"
            self.ids.forecast_container.add_widget(panel)
        return


    # Funzione che formula ed effettua la risposta vocale
    def responseToAudio(self):

        # Se ho una richiesta generale (senza orario) ad un giorno futuro diverso da oggi
        if self.hour == -1 and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp, main_wind, main_hum = self.getGeneralWeather(self.day)
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi e con il {main_hum} percento di umidità media. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"

        # Se ho una richiesta specifica (con orario) ad un giorno futuro diverso da oggi
        elif type(self.hour) == str and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day)
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"

        # Se ho una richiesta generale (senza orario) per oggi
        elif self.hour == -1 and self.day == datetime.datetime.today().strftime("%A"):
            main_weather = self.response_today['weather'][0]['main']
            main_temp = round(self.response_today['main']['temp'])
            main_wind = self.response_today['wind']['speed']
            main_hum = self.response_today['main']['humidity']
            if "temperatura" not in self.sentence:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
            else:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"

        # Se ho una richiesta specifica (con orario) per oggi
        elif type(self.hour) == str and self.day == datetime.datetime.today().strftime("%A"):
            if self.hour < str(datetime.datetime.now())[11:16]:
                frase = f"Le {self.hour} sono già passate, prova con un altro orario"
            else:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day)
                if "temperatura" not in self.sentence:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
                else:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"                    

        # Se ho una richiesta per oggi con fascia oraria
        elif type(self.hour) == list and self.day == datetime.datetime.today().strftime("%A"):
            list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
            if self.hour[0] < str(datetime.datetime.now())[11:16]:
                frase = "La fascia oraria richiesta è già passata"
            else:
                for orario in self.hour:
                    temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                    list_weather.append(temp_weather)
                    list_temp.append(temp_temp)
                    list_wind.append(temp_wind)
                    list_hum.append(temp_hum)
                
                main_temp = round(sum(list_temp)/2)
                main_wind = round(sum(list_wind)/2)
                main_hum = round(sum(list_hum)/2)

                if "07:00" in self.hour:
                    fascia_oraria = "in mattinata"
                elif "13:00" in self.hour:
                    fascia_oraria = "pomeriggio"
                else:
                    fascia_oraria = "in serata"

                weather1 = self.weatherTranslate(list_weather[0])
                weather2 = self.weatherTranslate(list_weather[1])
                if weather1 != weather2:
                    result_weather = "prima " + weather1 + " e poi " + weather2
                else:
                    result_weather = weather1
                if "temperatura" not in self.sentence:
                    frase = f"Oggi {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
                else:
                    frase = f"Oggi {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"

        # Se ho una richiesta per un giorno futuro con fascia oraria
        elif type(self.hour) == list and self.day != datetime.datetime.today().strftime("%A"):
            list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
            for orario in self.hour:
                temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                list_weather.append(temp_weather)
                list_temp.append(temp_temp)
                list_wind.append(temp_wind)
                list_hum.append(temp_hum)
            
            main_temp = round(sum(list_temp)/2)
            main_wind = round(sum(list_wind)/2)
            main_hum = round(sum(list_hum)/2)

            if "07:00" in self.hour:
                fascia_oraria = "in mattinata"
            elif "13:00" in self.hour:
                fascia_oraria = "pomeriggio"
            else:
                fascia_oraria = "in serata"

            weather1 = self.weatherTranslate(list_weather[0])
            weather2 = self.weatherTranslate(list_weather[1])
            if weather1 != weather2:
                result_weather = "prima " + weather1 + " e poi " + weather2
            else:
                result_weather = weather1
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"
            else:
                frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo, altrimenti premere indietro"

        print(frase)
        tts.speak(frase)
        return


    # Risposta a richiesta futura specifica (con orario)
    def getSpecificWeather(self, hour, day):
        available_hours_temp = ("02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00")
        available_hours = ("01:00", "04:00", "07:00", "10:00", "13:00", "16:00", "19:00", "22:00")
        if hour not in available_hours:
            if hour < available_hours[0] or hour > available_hours[-1]:
                if "23" in hour or "24" in hour:
                    custom_hour = available_hours[-1]
                else:
                    custom_hour = available_hours[0]
            else:
                for x in range(0, len(available_hours)-1):
                    if hour > available_hours[x] and hour < available_hours[x+1]:
                        custom_hour = available_hours[x+1]
        else:
            custom_hour = hour

        for desc in self.response_forecast['list']:
                if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == day and custom_hour in str(datetime.datetime.fromtimestamp(desc['dt'])):
                    weather = desc['weather'][0]['main']
                    temp = desc['main']['temp']
                    wind = desc['wind']['speed']*3.6
                    hum = desc['main']['humidity']

        return weather, round(temp), wind, hum


    # Risposta a richiesta futura generale (senza orario)
    def getGeneralWeather(self, day):  
        stats = {}
        avarage_temp = 0
        average_wind = 0
        average_hum = 0
        for desc in self.response_forecast['list']:
            if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == day:
                if desc['weather'][0]['main'] in stats:
                    stats.update({desc['weather'][0]['main']: stats[desc['weather'][0]['main']] + 1})
                else:
                    stats.update({desc['weather'][0]['main']: 1})
                avarage_temp += desc['main']['temp']
                average_wind += desc['wind']['speed']*3.6
                average_hum += desc['main']['humidity']

        highest = ""
        temp = 0 
        #print(stats.items())
        for key in stats.keys():
            if stats[key] > temp:
                highest = key
                temp = stats[key]
        return highest, round(avarage_temp/8), round(average_wind/8), round(average_hum/8)


    # Funzione per controllare che l'orario inserito sia valido
    def check_hour(self, hour):
        if int(hour.split(":")[0]) > 24 or int(hour.split(":")[1]) > 59:
            return False
        return True


    # Funzione che traduce il valore del vento per la risposta vocale
    def windTranslate(self, wind):
        if wind <= 5:
            return "vento calmo"
        elif wind <= 18:
            return "una brezza leggera"
        elif wind <= 38:
            return "vento moderato"
        elif wind <= 60:
            return "vento forte"
        elif wind <= 88:
            return "una forte burrasca"
        else:
            return "una forte tempesta"


    # Funzione che traduce self.day in italiano per la risposta vocale
    def dayTranslate(self, day):
        if datetime.datetime.today().strftime("%A") == day:
            return "oggi"
        else:
            if day == "Monday":
                return "lunedì"
            elif day == "Tuesday":
                return "martedì"
            elif day == "Wednesday":
                return "mercoledì"
            elif day == "Thursday":
                return "giovedì"
            elif day == "Friday":
                return "venerdì"
            elif day == "Saturday":
                return "sabato"
            elif day == "Sunday":
                return "domenica"


    # Funzione che traduce l'informazione del tempo ricevuta dalla request in italiano per la risposta vocale
    def weatherTranslate(self, weather):
        if weather == "Thunderstorm" or weather == "Squall" or weather == "Tornado":
            return "temporalesco"
        elif weather == "Drizzle":
            return "piovigginoso"
        elif weather == "Clouds":
            return "nuvoloso"
        elif weather == "Clear":
            return "sereno"
        elif weather == "Rain":
            return "piovoso"
        elif weather == "Snow":
            return "nevoso"
        elif weather == "Mist" or weather == "Smoke" or weather == "Haze" or weather == "Fog":
            return "nebbioso"
        elif weather == "Dust" or weather == "Sand" or weather == "Ash":
            return "polveroso"


    # Funzione che estrae la località richiesta
    def extractLocation(self, frase):
        if " a " in frase:
            return frase[frase.rfind(" a ")+3:]
        elif " all'" in frase:
            return frase[frase.rfind(" all'")+5:]
        elif " ad " in frase:
            return frase[frase.rfind(" ad ")+4:]
        elif " ai " in frase:
            return frase[frase.rfind(" ai ")+4:]
        elif " sull'" in frase:
            return frase[frase.rfind(" sull'")+6:]
        elif " sul " in frase:
            return frase[frase.rfind(" sul ")+5:]


    # Funzione che estrae dalla frase il giorno e l'orario richiesto (l'orario se non viene specificato è -1)
    def extractTime(self, frase):
        orario = -1
        giorno = 0
        giorno_del_mese = None

        if "l'una" in frase:
            orario = "01:00"
        elif "mezzanotte" in frase:
            orario = "00:00"
        elif "mezzogiorno" in frase:
            orario = "12:00"

        if orario == -1:    # Faccio solo se l'orario non è ancora stato definito
            parole = frase.split(" ")
            for parola in parole:
                if parola.isdigit():
                    giorno_del_mese = int(parola)
                elif ":" in parola:
                    if len(parola) == 4:
                        orario = "0"+parola
                    else:
                        orario = parola

        if orario == -1:
            if "mattina" in frase:
                orario = ["07:00", "10:00"]
            elif "pomeriggio" in frase:
                orario = ["13:00", "16:00"]
            elif "sera" in frase:
                orario = ["19:00", "22:00"]

        if giorno_del_mese == None or " giorni " in frase:
            if "oggi" in frase:
                giorno = datetime.date.today().strftime("%A") 
            elif "dopodomani" in frase or "tra due giorni" in frase or "fra due giorni" in frase or "tra 2 giorni" in frase or "fra 2 giorni" in frase:
                giorno = (datetime.date.today() + datetime.timedelta(2)).strftime("%A")
            elif "domani" in frase or "tra un giorno" in frase or "fra un giorno" in frase or "tra 1 giorno" in frase or "fra 1 giorno" in frase:
                giorno = (datetime.date.today() + datetime.timedelta(1)).strftime("%A")
            elif "tra tre giorni" in frase or "fra tre giorni" in frase or "tra 3 giorni" in frase or "fra 3 giorni" in frase:
                giorno = (datetime.date.today() + datetime.timedelta(3)).strftime("%A")
            elif "tra quattro giorni" in frase or "fra quattro giorni" in frase or "tra 4 giorni" in frase or "fra 4 giorni" in frase:
                giorno = (datetime.date.today() + datetime.timedelta(4)).strftime("%A")
            elif " tra " in frase or " fra " in frase or "ieri" in frase or " era " in frase or "'era " in frase:
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
        else:
            limitDayMonth = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
            if giorno_del_mese > 0 and giorno_del_mese <= limitDayMonth[datetime.datetime.today().month]:
                diff_in_days = 0
                data = datetime.datetime.today()
                while giorno_del_mese != data.day and diff_in_days < 5:
                    diff_in_days += 1
                    data += datetime.timedelta(1)
                if diff_in_days <= 4:
                    giorno = data.strftime("%A")
                else:
                    giorno = None
            else:
                giorno = -1
                
        return giorno, orario


    # Funzione chiamata per controllare che si arrivi massimo a 4 (se passano più di 4 giorni non possiamo prevedere il tempo)
    def diffInDays(self, day):
        if day == None:
            return 6
        if day == -1:
            return -1
        today = datetime.date.today()
        diff = 0
        while day != today.strftime("%A"):
            diff += 1
            today = today + datetime.timedelta(1)
        return diff     
    

    # Funzione bindata al tasto indietro della topbar
    def goBack(self):
        self.ids['forecast_container'].clear_widgets()
        self.ids['today_icon'].source = "media/default.png"
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        self.response_today = None
        self.response_forecast = None
        self.ids['topappbar'].title = ""
        self.sentence = ""
        self.day = ""
        self.hour = ""
        self.location = ""
        return True


    # Funzione che binda il back button di android per far tornare indietro alla main page 
    def key_pressed(self, window, key, *args):  
        if key == 27:
            if self.manager.current == 'forecast':
                self.ids['forecast_container'].clear_widgets()
                self.ids['today_icon'].source = "media/default.png"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                self.response_today = None
                self.response_forecast = None
                self.ids['topappbar'].title = ""
                self.sentence = ""
                self.day = ""
                self.hour = ""
                self.location = ""
                return True
            return False


    # Funzione per ricavare l'icona dalla cartella "media"
    def getIcon(self, descritpion, main, timestamp):
        time = str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        if main == "Thunderstorm":
            return "media/thunderstorm.png"
        elif main == "Drizzle":
            return "media/rain.png"
        elif descritpion in ("clear sky", "few clouds", "light rain"):
            if time >= "06:00" and time <= "18:00":
                return "media/day/" + descritpion.replace(" ", "_") + ".png"
            else:
                return "media/night/" + descritpion.replace(" ", "_") + ".png"
        else:
            return "media/" + descritpion.replace(" ", "_").replace("/", "_") + ".png"
         

    # Funzione che traduce i timestamp in giorni della settimana
    def getDay(self,timestamp):
        translate = {"Monday" : "Lunedì", "Tuesday" : "Martedì", "Wednesday" : "Mercoledì", "Thursday" : "Giovedì", "Friday" : "Venerdì", "Saturday" : "Sabato", "Sunday" : "Domenica"}
        day = datetime.datetime.fromtimestamp(timestamp).strftime("%A")
        if datetime.datetime.now().strftime("%A") in day:
            return "Oggi " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        else:
            return translate[day] + " " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
    


##############################################################################################



class ForecastPageBlind(Screen):
    
    response_today = None
    response_forecast = None
    latitude = ""
    longitude = ""
    sentence = ""
    day = ""                # Opzionale, di default 0
    hour = ""               # Opzionale (-1 se non specificato)
    location = ""           # Obbligatorio
    to_tell = []
    istruction_told_one = False


    # Funzione chiamata all'avvio della nuova pagina e si occupa di popolarla di widget (immagine in questo caso)
    def on_enter(self):     

        EventLoop.window.bind(on_keyboard=self.key_pressed)

        self.sentence = self.manager.get_screen("main").sentence # Prendo la frase da esaminare

        self.location = self.extractLocation(self.sentence)

        if self.location == None:
            tts.speak("Non ho capito in quale località. Riprova")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        self.day, self.hour = self.extractTime(self.sentence)
        if self.day == 0: 
            self.day = datetime.date.today().strftime("%A") 

        if type(self.hour) == str:
            if not self.check_hour(self.hour):
                tts.speak("Orario non valido")
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                return
        if type(self.hour) == list and self.day == datetime.date.today().strftime("%A"):
            if self.hour[0] < str(datetime.datetime.now())[11:16]:
                frase = "La fascia oraria richiesta è già passata. Riprova"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                return

        print(self.sentence)
        print(self.location)
        print(self.day)
        print(self.hour)
        print(self.diffInDays(self.day))

        if self.diffInDays(self.day) > 4:
            tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return
        elif self.diffInDays(self.day) == -1:
            tts.speak("Specificare un giorno del mese valido")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        UrlRequest(f"http://api.openweathermap.org/geo/1.0/direct?q={self.location.replace(' ', '+')}&limit=1&appid=c0b583a8bb8b03e64dd0e16bccda95bf", on_success=self.gotCoordinates, on_error=self.gotAnError, on_failure=self.gotAnError)
        return


    # Funzione chiamata se la UrlRequest per le coordinate va a buon fine
    def gotCoordinates(self, req, r):
        if r == []:
            self.gotNoCoordinates()
            return
        self.latitude = r[0]['lat']
        self.longitude = r[0]['lon']
        self.ids['topappbar_blind'].title = self.location
        
        UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={str(self.latitude)}&lon={str(self.longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric", on_success=self.gotWeatherToday, on_error=self.gotAnError, on_failure=self.gotAnError)


    # Funzione chiamata se la UrlRequest per la previsione di oggi va a buon fine
    def gotWeatherToday(self, req, r):
        if r == []:
            self.gotAnError(req, r)
            return
        self.response_today=r
        UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat={str(self.latitude)}&lon={str(self.longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric", on_success=self.gotWeatherForecast, on_error=self.gotAnError, on_failure=self.gotAnError)


    # Funzione chiamata se la UrlRequest per la previsione
    def gotWeatherForecast(self, req, r):
        if r == []:
            self.gotAnError(req, r)
            return
        self.response_forecast=r

        self.ids['today_icon_blind'].source = self.getIcon(self.response_today['weather'][0]['description'], self.response_today['weather'][0]['main'], self.response_today['dt'])
        self.responseToAudio()
        return


    # Funzione che formula ed effettua la risposta vocale
    def responseToAudio(self):

        # Se ho una richiesta generale (senza orario) ad un giorno futuro diverso da oggi
        if self.hour == -1 and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp, main_wind, main_hum = self.getGeneralWeather(self.day) 
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi e con il {main_hum} percento di umidità media. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."

        # Se ho una richiesta specifica (con orario) ad un giorno futuro diverso da oggi
        elif type(self.hour) == str and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day) 
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."

        # Se ho una richiesta generale (senza orario) per oggi
        elif self.hour == -1 and self.day == datetime.datetime.today().strftime("%A"):
            main_weather = self.response_today['weather'][0]['main']
            main_temp = round(self.response_today['main']['temp'])
            main_wind = self.response_today['wind']['speed']
            main_hum = self.response_today['main']['humidity']
            if "temperatura" not in self.sentence:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
            else:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."

        # Se ho una richiesta specifica (con orario) per oggi
        elif type(self.hour) == str and self.day == datetime.datetime.today().strftime("%A"):
            if self.hour < str(datetime.datetime.now())[11:16]:
                frase = f"Le {self.hour} sono già passate, prova con un altro orario"
                self.ids['today_icon_blind'].source = "media/default.png"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                self.ids['topappbar_blind'].title = ""
                self.sentence = ""
                self.day = ""
                self.hour = ""
                self.location = ""
            else:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day) 
                if "temperatura" not in self.sentence:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
                else:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."                    

        # Se ho una richiesta per oggi con fascia oraria
        elif type(self.hour) == list and self.day == datetime.datetime.today().strftime("%A"):
            list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
            if self.hour[0] < str(datetime.datetime.now())[11:16]:
                frase = "La fascia oraria richiesta è già passata"
            else:
                for orario in self.hour:
                    temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                    list_weather.append(temp_weather)
                    list_temp.append(temp_temp)
                    list_wind.append(temp_wind)
                    list_hum.append(temp_hum)
                
                main_temp = round(sum(list_temp)/2)
                main_wind = round(sum(list_wind)/2)
                main_hum = round(sum(list_hum)/2)

                if "07:00" in self.hour:
                    fascia_oraria = "in mattinata"
                elif "13:00" in self.hour:
                    fascia_oraria = "pomeriggio"
                else:
                    fascia_oraria = "in serata"

                weather1 = self.weatherTranslate(list_weather[0])
                weather2 = self.weatherTranslate(list_weather[1])
                if weather1 != weather2:
                    result_weather = "prima " + weather1 + " e poi " + weather2
                else:
                    result_weather = weather1
                if "temperatura" not in self.sentence:
                    frase = f"Oggi {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
                else:
                    frase = f"Oggi {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."

        # Se ho una richiesta per un giorno futuro con fascia oraria
        elif type(self.hour) == list and self.day != datetime.datetime.today().strftime("%A"):
            list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
            for orario in self.hour:
                temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                list_weather.append(temp_weather)
                list_temp.append(temp_temp)
                list_wind.append(temp_wind)
                list_hum.append(temp_hum)
            
            main_temp = round(sum(list_temp)/2)
            main_wind = round(sum(list_wind)/2)
            main_hum = round(sum(list_hum)/2)

            if "07:00" in self.hour:
                fascia_oraria = "in mattinata"
            elif "13:00" in self.hour:
                fascia_oraria = "pomeriggio"
            else:
                fascia_oraria = "in serata"

            weather1 = self.weatherTranslate(list_weather[0])
            weather2 = self.weatherTranslate(list_weather[1])
            if weather1 != weather2:
                result_weather = "prima " + weather1 + " e poi " + weather2
            else:
                result_weather = weather1
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."
            else:
                frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità. Toccare la parte inferiore dello schermo per avere previsioni trioràrie dettagliate, quella superiore per effettuare un'altra richiesta su {self.location} o tornare indietro per una nuova richiesta."


        print(frase)
        tts.speak(frase)
        return


    # Funzione per la descrizione vocale sequenziale
    def next(self):
        translate = {"Monday" : "Lunedì", "Tuesday" : "Martedì", "Wednesday" : "Mercoledì", "Thursday" : "Giovedì", "Friday" : "Venerdì", "Saturday" : "Sabato", "Sunday" : "Domenica"}

        # Se la lista di previsioni triorarie del giorno è vuota va popolata
        if self.to_tell == []:
            counter = 0
            for info_table in self.response_forecast['list']:
                if datetime.datetime.fromtimestamp(info_table['dt']).strftime("%A") == self.day:
                    self.to_tell.append(counter)
                counter += 1
            self.to_tell.append(77)

        # Se la lista di previsioni triorarie ha come primo e unico elemento 77 allora sono state date tutte le previsioni
        if self.to_tell[0] == 77:
            tts.speak("Previsioni per la giornata finite")
        else:
            info_to_tell = self.response_forecast['list'][self.to_tell[0]]
            time = str(datetime.datetime.fromtimestamp(info_to_tell['dt'])).split(" ")[1][:-3]
            if datetime.datetime.fromtimestamp(info_to_tell['dt']).strftime("%A") == datetime.datetime.today().strftime("%A"):
                day = "Oggi"
            else:
                day = translate[datetime.datetime.fromtimestamp(info_to_tell['dt']).strftime("%A")]
            weather = info_to_tell['weather'][0]['main']
            temp = round(info_to_tell['main']['temp'])
            hum = info_to_tell['main']['humidity']
            press = info_to_tell['main']['pressure']
            wind = round(info_to_tell['wind']['speed']*3.6)
            frase = f"{day} alle {time} sarà {self.weatherTranslate(weather)} con temperatura di {temp} gradi, tasso di umidità del {hum} percento, pressione di {press} hPa e con {self.windTranslate(wind)}."
            self.to_tell.pop(0)
            tts.speak(frase)
            



    # Risposta a richiesta futura specifica (con orario)
    def getSpecificWeather(self, hour, day): 
        available_hours_temp = ("02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00")
        available_hours = ("01:00", "04:00", "07:00", "10:00", "13:00", "16:00", "19:00", "22:00")
        if hour not in available_hours:
            if hour < available_hours[0] or hour > available_hours[-1]:
                if "23" in hour or "24" in hour:
                    custom_hour = available_hours[-1]
                else:
                    custom_hour = available_hours[0]
            else:
                for x in range(0, len(available_hours)-1):
                    if hour > available_hours[x] and hour < available_hours[x+1]:
                        custom_hour = available_hours[x+1]
        else:
            custom_hour = hour

        for desc in self.response_forecast['list']:
                if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == day and custom_hour in str(datetime.datetime.fromtimestamp(desc['dt'])):
                    weather = desc['weather'][0]['main']
                    temp = desc['main']['temp']
                    wind = desc['wind']['speed']*3.6
                    hum = desc['main']['humidity']

        return weather, round(temp), wind, hum


    # Risposta a richiesta futura generale (senza orario) #######
    def getGeneralWeather(self, day):  
        stats = {}
        avarage_temp = 0
        average_wind = 0
        average_hum = 0
        for desc in self.response_forecast['list']:
            if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == day:
                if desc['weather'][0]['main'] in stats:
                    stats.update({desc['weather'][0]['main']: stats[desc['weather'][0]['main']] + 1})
                else:
                    stats.update({desc['weather'][0]['main']: 1})
                avarage_temp += desc['main']['temp']
                average_wind += desc['wind']['speed']*3.6
                average_hum += desc['main']['humidity']

        highest = ""
        temp = 0 
        #print(stats.items())
        for key in stats.keys():
            if stats[key] > temp:
                highest = key
                temp = stats[key]
        return highest, round(avarage_temp/8), round(average_wind/8), round(average_hum/8)


    # Funzione per ricavare l'icona dalla cartella "media"
    def getIcon(self, descritpion, main, timestamp):
        time = str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        if main == "Thunderstorm":
            return "media/thunderstorm.png"
        elif main == "Drizzle":
            return "media/rain.png"
        elif descritpion in ("clear sky", "few clouds", "light rain"):
            if time >= "06:00" and time <= "18:00":
                return "media/day/" + descritpion.replace(" ", "_") + ".png"
            else:
                return "media/night/" + descritpion.replace(" ", "_") + ".png"
        else:
            return "media/" + descritpion.replace(" ", "_").replace("/", "_") + ".png"
        

    # Funzione che traduce il valore del vento per la risposta vocale
    def windTranslate(self, wind):
        if wind <= 5:
            return "vento calmo"
        elif wind <= 18:
            return "una brezza leggera"
        elif wind <= 38:
            return "vento moderato"
        elif wind <= 60:
            return "vento forte"
        elif wind <= 88:
            return "una forte burrasca"
        else:
            return "una forte tempesta"


    # Funzione che traduce self.day in italiano per la risposta vocale
    def dayTranslate(self, day):
        if datetime.datetime.today().strftime("%A") == day:
            return "oggi"
        else:
            if day == "Monday":
                return "lunedì"
            elif day == "Tuesday":
                return "martedì"
            elif day == "Wednesday":
                return "mercoledì"
            elif day == "Thursday":
                return "giovedì"
            elif day == "Friday":
                return "venerdì"
            elif day == "Saturday":
                return "sabato"
            elif day == "Sunday":
                return "domenica"


    # Funzione che traduce l'informazione del tempo ricevuta dalla request in italiano per la risposta vocale
    def weatherTranslate(self, weather):
        if weather == "Thunderstorm" or weather == "Squall" or weather == "Tornado":
            return "temporalesco"
        elif weather == "Drizzle":
            return "piovigginoso"
        elif weather == "Clouds":
            return "nuvoloso"
        elif weather == "Clear":
            return "sereno"
        elif weather == "Rain":
            return "piovoso"
        elif weather == "Snow":
            return "nevoso"
        elif weather == "Mist" or weather == "Smoke" or weather == "Haze" or weather == "Fog":
            return "nebbioso"
        elif weather == "Dust" or weather == "Sand" or weather == "Ash":
            return "polveroso"
        
    
    # Funzione chiamata in caso di località non trovata
    def gotNoCoordinates(self):
        tts.speak("Località non trovata")
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        return


    # Funzione chiamata in caso di errore da parte della UrlRequest
    def gotAnError(self, req, r):
        tts.speak("C'è stato un errore con la richiesta al servizio per le previsioni. Riprova")
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        return


    # Funzione chiamata per controllare che si arrivi massimo a 4 (se passano più di 4 giorni non possiamo prevedere il tempo)
    def diffInDays(self, day):
        if day == None:
            return 6
        if day == -1:
            return -1
        today = datetime.date.today()
        diff = 0
        while day != today.strftime("%A"):
            diff += 1
            today = today + datetime.timedelta(1)
        return diff
    

    # Funzione che estrae dalla frase il giorno e l'orario richiesto (l'orario se non viene specificato è -1)
    def extractTime(self, frase):
        orario = -1
        giorno = 0 #######
        giorno_del_mese = None

        if "l'una" in frase:
            orario = "01:00"
        elif "mezzanotte" in frase:
            orario = "00:00"
        elif "mezzogiorno" in frase:
            orario = "12:00"

        if orario == -1:    # Faccio solo se l'orario non è ancora stato definito
            parole = frase.split(" ")
            for parola in parole:
                if parola.isdigit():
                    giorno_del_mese = int(parola)
                elif ":" in parola:
                    if len(parola) == 4:
                        orario = "0"+parola
                    else:
                        orario = parola

        if orario == -1:
            if "mattina" in frase:
                orario = ["07:00", "10:00"]
            elif "pomeriggio" in frase:
                orario = ["13:00", "16:00"]
            elif "sera" in frase:
                orario = ["19:00", "22:00"]

        if giorno_del_mese == None or " giorni " in frase:
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
            elif " tra " in frase or " fra " in frase or "ieri" in frase or " era " in frase or "'era " in frase:
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
        else:
            limitDayMonth = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
            if giorno_del_mese > 0 and giorno_del_mese <= limitDayMonth[datetime.datetime.today().month]:
                diff_in_days = 0
                data = datetime.datetime.today()
                while giorno_del_mese != data.day and diff_in_days < 5:
                    diff_in_days += 1
                    data += datetime.timedelta(1)
                if diff_in_days <= 4:
                    giorno = data.strftime("%A")
                else:
                    giorno = None
            else:
                giorno = -1
                
        return giorno, orario


    # Funzione che estrae la località richiesta
    def extractLocation(self, frase):
        if " a " in frase:
            return frase[frase.rfind(" a ")+3:]
        elif " all'" in frase:
            return frase[frase.rfind(" all'")+5:]
        elif " ad " in frase:
            return frase[frase.rfind(" ad ")+4:]
        elif " ai " in frase:
            return frase[frase.rfind(" ai ")+4:]
        elif " sull'" in frase:
            return frase[frase.rfind(" sull'")+6:]
        elif " sul " in frase:
            return frase[frase.rfind(" sul ")+5:]


    # Funzione bindata al tasto indietro della topbar
    def goBack(self):
        self.ids['today_icon_blind'].source = "media/default.png"
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        self.ids['topappbar_blind'].title = ""
        self.sentence = ""
        self.day = ""
        self.hour = ""
        self.location = ""
        self.response_today = None
        self.response_forecast = None
        self.to_tell == []
        tts.speak("Tornato indietro")
        return True


    # Funzione che binda il back button di android per far tornare indietro alla main page 
    def key_pressed(self, window, key, *args):  
        if key == 27:
            if self.manager.current == 'forecastblind':
                self.ids['today_icon_blind'].source = "media/default.png"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                self.response_today = None
                self.response_forecast = None
                self.ids['topappbar_blind'].title = ""
                self.sentence = ""
                self.day = ""
                self.hour = ""
                self.location = ""
                self.to_tell == []
                tts.speak("Tornato indietro")
                return True
            return False


    # Funzione per controllare che l'orario inserito sia valido
    def check_hour(self, hour):
        if int(hour.split(":")[0]) > 24 or int(hour.split(":")[1]) > 59:
            return False
        return True


    # Funzione che esegue l'engine vocale per il riconoscimento delle frasi
    def new_request(self):
        self.sentence = ""
        try:
            stt.start()
            Clock.schedule_interval(self.check_state, 4 / 5)
        except NotImplementedError:
            self.openAlertDialog()
        except:
            tts.speak("Qualcosa è andato storto. Riprova")


    # Funzione eseguita una volta che l'engine ha rilevato che nessuno sta parlando
    def stop_listening_for_new_request(self):      
        stt.stop()
        self.update()
        Clock.unschedule(self.check_state)

        if self.sentences == []:
            self.noSentences()
            return
        
        self.sentence = self.sentences[0]

        new_day, new_hour = self.extractTime(self.sentence) 
        print(new_day, new_hour)

        if new_day == -1:
            tts.speak("Giorno non valido.")
            return
        elif new_day == None:
            tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
            return
        if new_day != 0:
            if self.diffInDays(new_day) > 4:
                tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione. Riprova")
                return

        if type(self.hour) == str:
            if not self.check_hour(self.hour):
                tts.speak("Orario non valido")
                return

        if new_hour != -1 and new_day != 0: 
            self.day = new_day
            self.newAudioResponse(new_hour, new_day) 
        elif new_hour != -1: 
            self.newAudioResponse(new_hour, None) 
        elif new_day != 0:
            self.day = new_day
            self.newAudioResponse(None, new_day) 
        else: 
            tts.speak("Non ho capito. Riprova") 
        return


    # Funzione per il nuovo response audio
    def newAudioResponse(self, hour, day):        

        if hour == None:
            main_weather, main_temp, main_wind, main_hum = self.getGeneralWeather(day)
            frase = f"{self.dayTranslate(day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi e con {self.windTranslate(main_wind)}. "

        elif day == None:
            if type(hour) != list:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, self.day)
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"
            else:
                list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
                if hour[0] < str(datetime.datetime.now())[11:16] and self.day == datetime.date.today().strftime("%A"):
                    frase = "La fascia oraria richiesta è già passata"
                else:
                    for orario in hour:
                        temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, self.day)
                        list_weather.append(temp_weather)
                        list_temp.append(temp_temp)
                        list_wind.append(temp_wind)
                        list_hum.append(temp_hum)
                    
                    main_temp = round(sum(list_temp)/2)
                    main_wind = round(sum(list_wind)/2)
                    main_hum = round(sum(list_hum)/2)

                    if "07:00" in hour:
                        fascia_oraria = "in mattinata"
                    elif "13:00" in hour:
                        fascia_oraria = "pomeriggio"
                    else:
                        fascia_oraria = "in serata"

                    weather1 = self.weatherTranslate(list_weather[0])
                    weather2 = self.weatherTranslate(list_weather[1])
                    if weather1 != weather2:
                        result_weather = "prima " + weather1 + " e poi " + weather2
                    else:
                        result_weather = weather1
                    if "temperatura" not in self.sentence:
                        frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}."
                    else:
                        frase = f"{self.dayTranslate(self.day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità."
        else:
            if type(hour) != list:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, day)
                frase = f"{self.dayTranslate(day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"
            else:
                list_weather, list_temp, list_wind, list_hum = [], [], [], []
            
                if hour[0] < str(datetime.datetime.now())[11:16] and day == datetime.date.today().strftime("%A"):
                    frase = "La fascia oraria richiesta è già passata"
                else:
                    for orario in hour:
                        temp_weather, temp_temp, temp_wind, temp_hum = self.getSpecificWeather(orario, day)
                        list_weather.append(temp_weather)
                        list_temp.append(temp_temp)
                        list_wind.append(temp_wind)
                        list_hum.append(temp_hum)
                    
                    main_temp = round(sum(list_temp)/2)
                    main_wind = round(sum(list_wind)/2)
                    main_hum = round(sum(list_hum)/2)

                    if "07:00" in hour:
                        fascia_oraria = "in mattinata"
                    elif "13:00" in hour:
                        fascia_oraria = "pomeriggio"
                    else:
                        fascia_oraria = "in serata"

                    weather1 = self.weatherTranslate(list_weather[0])
                    weather2 = self.weatherTranslate(list_weather[1])
                    if weather1 != weather2:
                        result_weather = "prima " + weather1 + " e poi " + weather2
                    else:
                        result_weather = weather1
                    if "temperatura" not in self.sentence:
                        frase = f"{self.dayTranslate(day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}."
                    else:
                        frase = f"{self.dayTranslate(day)} {fascia_oraria} il tempo a {self.location} sarà {result_weather} con una temperatura media di {main_temp} gradi e con il {main_hum} percento di umidità."
            
        tts.speak(frase)
        return 


    # Funzione chiamata in loop mentre l'engine ascolta per controllare se si sta ancora parlando o no
    def check_state(self, dt):
        if not stt.listening:
            self.stop_listening_for_new_request()


    # Funzione chiamata per ottenere la frase catturata dall'engine
    def update(self):
        self.sentences = stt.results


    # Funzione chiamata in caso non sia stata catturata nessuna frase
    def noSentences(self):
        tts.speak("Non ho capito, ripetere per favore")
        return


##############################################################################################



class HourlyForecast(MDGridLayout):
    pass



class ImageButton(ButtonBehavior, Image):
    pass



class PageManager(ScreenManager):
    pass



class WeatherApp(MDApp):
    api_key = "c0b583a8bb8b03e64dd0e16bccda95bf"
    def build(self):
        #kv = Builder.load_file('weather.kv')
        return
        #return kv


if __name__ == '__main__':
    WeatherApp().run()