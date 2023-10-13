from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.gridlayout import MDGridLayout 
from kivy.base import EventLoop
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
import datetime
from plyer import tts, stt



##############################################################################################


class MainPage(Screen):
    
    sentence = ""
    sentences = ""

    def on_start(self): 
        EventLoop.window.bind(on_keyboard=self.key_pressed)

    def listenToSearch(self):        
        self.start_listening()

    def start_listening(self):
        self.sentence = ""
        stt.start()
        Clock.schedule_interval(self.check_state, 1 / 5)

    def stop_listening(self):      
        stt.stop()
        self.update()
        Clock.unschedule(self.check_state)

        self.sentence = self.sentences[0]
        self.manager.current = 'forecast'
        self.manager.transition.direction = 'left'

    def check_state(self, dt):
        if not stt.listening:
            self.stop_listening()

    def update(self):
        self.sentences = stt.results

    def key_pressed(self, window, key, *args):
        if key == 27:
            if self.manager.current == 'forecast':
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                return True
            return False


##############################################################################################


class ForecastPage(Screen):

    response_today = None
    response_forecast = None
    latitude = ""
    longitude = ""
    sentence = ""
    day = ""                # Opzionale di default datetime.datetime.today().strftime("%A") 
    hour = ""               # Opzionale (-1 se non specificato)
    location = ""           # Obbligatorio

    def on_enter(self):     

        EventLoop.window.bind(on_keyboard=self.key_pressed)

        self.sentence = self.manager.get_screen("main").sentence # Prendo la frase da esaminare

        self.location = self.extractLocation(self.sentence)

        self.day, self.hour = self.extractTime(self.sentence)

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
            self.gotAnError(req, r)
            return
        self.latitude = r[0]['lat']
        self.longitude = r[0]['lon']
        
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

        if self.diffInDays(self.day) > 4:
            tts.speak("Il giorno richiesto va oltre la previsione massima consentita")
            return
        else:
            self.responseToAudio()
        return


    # Funzione chiamata in caso di errore da parte della UrlRequest
    def gotAnError(self, req, r):
        tts.speak("C'è stato un errore con la richiesta al servizio per le previsioni")
        return


    #Fuzione che crea e inserisce i vari ExpansionPanel con le previsioni
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
            info.ids['humid'].text = str(x['main']['humidity']) + " %"
            info.ids['temp'].text = str(round(x['main']['temp'])) + " °C"
            info.ids['press'].text = str(x['main']['pressure']) + " hPa"
            info.ids['wind'].text = str(round(x['wind']['speed']*3.6)) + " Km/h"
            self.ids.forecast_container.add_widget(panel)
        return


    # Funzione che formula ed effettua la risposta vocale
    def responseToAudio(self):

        # Se ho una richiesta generale (senza orario) ad un giorno futuro diverso da oggi
        if self.hour == -1 and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp = self.getGeneralWeather()
            frase = f"{self.dayTranslate(self.day)} il tempo a {self.location} sarà {self.weatherTranslate(main_weather)} con una temperaturà media di {main_temp} gradi"
        
        # Se ho una richiesta specifica (con orario) ad un giorno futuro diverso da oggi
        elif self.hour != -1 and self.day != datetime.datetime.today().strftime("%A"):
            main_weather, main_temp = self.getSpecificWeather()
            frase = f"{self.dayTranslate(self.day)} il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi"
            
        # Se ho una richiesta generale (senza orario) per oggi
        elif self.hour == -1 and self.day == datetime.datetime.today().strftime("%A"):
            main_weather = self.response_today['weather'][0]['main']
            main_temp = round(self.response_today['main']['temp'])
            frase = f"Oggi il tempo a {self.location} è {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi"

        # Se ho una richiesta specifica (con orario) per oggi
        elif self.hour != -1 and self.day == datetime.datetime.today().strftime("%A"):
            if self.hour < str(datetime.datetime.now())[11:16]:
                frase = f"Le {self.hour} sono già passate, prova con un altro orario"
            else:
                main_weather, main_temp = self.getSpecificWeather()
                frase = f"Oggi il tempo a {self.location}, verso le {self.hour} sarà {self.weatherTranslate(main_weather)} con una temperaturà di {main_temp} gradi"

        print(frase)
        tts.speak(frase)
        return


    # Risposta a richiesta futura specifica (con orario)
    def getSpecificWeather(self):
        available_hours = ("02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00")
        if self.hour not in available_hours:
            if self.hour < available_hours[0] or self.hour > available_hours[-1]:
                custom_hour = available_hours[0]
            for x in range(0, len(available_hours)-1):
                if self.hour > available_hours[x] and self.hour < available_hours[x+1]:
                    custom_hour = available_hours[x+1]
        else:
            custom_hour = self.hour

        for desc in self.response_forecast['list']:
                if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == self.day and custom_hour in str(datetime.datetime.fromtimestamp(desc['dt'])):
                    weather = desc['weather'][0]['main']
                    temp = desc['main']['temp']

        return weather, round(temp)


    # Risposta a richiesta futura generale (senza orario)
    def getGeneralWeather(self):  
        stats = {}
        avarage_temp = 0
        for desc in self.response_forecast['list']:
            if datetime.datetime.fromtimestamp(desc['dt']).strftime("%A") == self.day:
                if desc['weather'][0]['main'] in stats:
                    stats.update({desc['weather'][0]['main']: stats[desc['weather'][0]['main']] + 1})
                else:
                    stats.update({desc['weather'][0]['main']: 1})
                avarage_temp += desc['main']['temp']

        highest = ""
        temp = 0 
        #print(stats.items())
        for key in stats.keys():
            if stats[key] > temp:
                highest = key
                temp = stats[key]
        return highest, round(avarage_temp/8)


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


    #Funzione che estrae la località richiesta
    def extractLocation(self, frase):
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


    #Funzione che estrae dalla frase il giorno e l'orario richiesto (l'orario se non viene specificato è -1)
    def extractTime(self, frase):
        orario = -1
        giorno = datetime.date.today().strftime("%A")

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
                    orario = parola + ":00"
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
        return giorno, orario


    #Funzione chiamata per controllare che si arrivi massimo a 4 (se passano più di 4 giorni non possiamo prevedere il tempo)
    def diffInDays(self, day):
        if day == None:
            return 6
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
        self.sentence = ""
        self.day = ""
        self.hour = ""
        self.location = ""
        return True


    #Funzione che binda il back button di android per far tornare indietro alla main page 
    def key_pressed(self, window, key, *args):  
        if key == 27:
            if self.manager.current == 'forecast':
                self.ids['forecast_container'].clear_widgets()
                self.ids['today_icon'].source = "media/default.png"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                self.response_today = None
                self.response_forecast = None
                self.sentence = ""
                self.day = ""
                self.hour = ""
                self.location = ""
                return True
            return False


    #Funzione per ricavare l'icona dalla cartella "media"
    def getIcon(self, descritpion, main, timestamp):
        time = str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        if main == "Thunderstorm":
            return "media/thunderstorm.png"
        elif main == "Drizzle":
            return "media/rain.png"
        elif descritpion in ("clear sky", "few clouds", "light rain"):
            if time >= "06:00" and time <= "18:00":
                return "media/day" + descritpion.replace(" ", "_") + ".png"
            else:
                return "media/night" + descritpion.replace(" ", "_") + ".png"
        else:
            return "media/" + descritpion.replace(" ", "_").replace("/", "_") + ".png"
         

    # Funzione che traduce i timestamp in giorni della settimana
    def getDay(self,timestamp):
        day = datetime.datetime.fromtimestamp(timestamp).strftime("%A")
        if datetime.datetime.now().strftime("%A") in day:
            return "Today " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        else:
            return day + " " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
    

##############################################################################################


class HourlyForecast(MDGridLayout):
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