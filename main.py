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


    # Funzione eseguita all'avvio dell'applicazione
    def on_start(self): 
        EventLoop.window.bind(on_keyboard=self.key_pressed)

    def on_enter(self):
        tts.speak("Applicazione aperta, toccare lo schermo e aspettare il segnale acustico per fare la richiesta. Previsioni disponibili fino a 5 giorni compreso oggi.")

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
            tts.speak("Qualcosa è andato storto, riprova")


    # Funzione eseguita una volta che l'engine ha rilevato che nessuno sta parlando
    def stop_listening(self):      
        stt.stop()
        self.update()
        Clock.unschedule(self.check_state)

        if self.sentences == []:
            self.noSentences()
            return
        self.sentence = self.sentences[0]
        self.manager.current = 'forecast'
        self.manager.transition.direction = 'left'


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
            tts.speak("Non ho capito in quale località")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        self.day, self.hour = self.extractTime(self.sentence)
        if self.day == 0: 
            self.day = datetime.date.today().strftime("%A") 

        if not self.check_hour(self.hour):
            tts.speak("Orario non valido")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return

        print(self.sentence)
        print(self.location)
        print(self.day)
        print(self.hour)
        print(self.diffInDays(self.day))

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

        if self.diffInDays(self.day) > 4:
            tts.speak("Il giorno richiesto non rientra tra i giorni disponibili per la previsione")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return
        elif self.diffInDays(self.day) == -1:
            tts.speak("Specificare un giorno del mese valido")
            self.manager.current = 'main'
            self.manager.transition.direction = 'right'
            return
        else:
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
            tts.speak("Qualcosa è andato storto, riprova")


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

        if new_hour != -1 and new_day != 0: 
            self.newAudioResponse(new_hour, new_day) 
        elif new_hour != -1: 
            self.newAudioResponse(new_hour, None) 
        elif new_day != 0: 
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
            main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, self.day)
            frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"

        else:
            main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(hour, day)
            frase = f"{self.dayTranslate(day)} il tempo a {self.location}, verso le {hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con {self.windTranslate(main_wind)}"

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
        tts.speak("C'è stato un errore con la richiesta al servizio per le previsioni")
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
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperatura media di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi e con il {main_hum} percento di umidità media. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"

        # Se ho una richiesta specifica (con orario) ad un giorno futuro diverso da oggi
        elif self.hour != -1 and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day)
            if "temperatura" not in self.sentence:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"
            else:
                frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"

        # Se ho una richiesta generale (senza orario) per oggi
        elif self.hour == -1 and self.day == datetime.datetime.today().strftime("%A"):
            main_weather = self.response_today['weather'][0]['main']
            main_temp = round(self.response_today['main']['temp'])
            main_wind = self.response_today['wind']['speed']
            main_hum = self.response_today['main']['humidity']
            if "temperatura" not in self.sentence:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}"
            else:
                frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità"

        # Se ho una richiesta specifica (con orario) per oggi
        elif self.hour != -1 and self.day == datetime.datetime.today().strftime("%A"):
            if self.hour < str(datetime.datetime.now())[11:16]:
                frase = f"Le {self.hour} sono già passate, prova con un altro orario"
            else:
                main_weather, main_temp, main_wind, main_hum = self.getSpecificWeather(self.hour, self.day)
                if "temperatura" not in self.sentence:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperatura di {main_temp} gradi e con {self.windTranslate(main_wind)}. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"
                else:
                    frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi e con il {main_hum} percento di umidità. Per altre richieste sul tempo a {self.location} premere sulla parte alta dello schermo"                    

        print(frase)
        tts.speak(frase)
        return


    # Risposta a richiesta futura specifica (con orario)
    def getSpecificWeather(self, hour, day):
        available_hours = ("02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00")
        if hour not in available_hours:
            if hour < available_hours[0] or hour > available_hours[-1]:
                custom_hour = available_hours[0]
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
        if hour.split(":")[0] > 24 or hour.split(":")[1] > 59:
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
                return "mercoledì "
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
            elif " tra " in frase or " fra " in frase or "ieri" in frase or "era " in frase:
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