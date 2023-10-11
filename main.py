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

    request_today = None
    request_forecast = None
    sentence = ""
    day = ""
    hour = ""
    location = ""

    def on_enter(self):     

        EventLoop.window.bind(on_keyboard=self.key_pressed)

        self.sentence = self.manager.get_screen("main").sentence # Prendo la frase da esaminare

        self.location = self.extractLocation(self.sentence)
        self.day = self.extractTime(self.sentence)[0]
        self.hour = self.extractTime(self.sentence)[1]

        print(self.sentence)
        print(self.location)
        print(self.day)
        print(self.hour)
        print(self.diffInDays(self.day))

        if self.diffInDays(self.day) > 4:
            tts.speak("Il giorno richiesto va oltre la previsione massima consentita")
            return


        req_geocode = UrlRequest(f"http://api.openweathermap.org/geo/1.0/direct?q={self.location}&limit=1&appid=c0b583a8bb8b03e64dd0e16bccda95bf")

        req_geocode.wait()

        latitude = req_geocode.result[0]['lat']
        longitude = req_geocode.result[0]['lon']

        print(latitude, longitude)

        req_today = UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={str(latitude)}&lon={str(longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        req_forecast = UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat={str(latitude)}&lon={str(longitude)}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")

        req_today.wait()
        req_forecast.wait()

        self.request_today = req_today
        self.request_forecast = req_forecast

        self.getToday(req_today.result, req_forecast.result)
        #self.responseToAudio()
        return
        

    def getToday(self, result_today, result_forecast):
        print(self.sentence)

        self.ids['today_icon'].source = self.getIcon(result_today['weather'][0]['description'])
        
        for x in result_forecast['list']:
            info = HourlyForecast()
            panel = MDExpansionPanel(
                content = info,
                
                icon = self.getIcon(x['weather'][0]['description']),
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


    def responseToAudio(self):
        pass


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


    def extractTime(self, frase):
        orario = -1
        giorno = datetime.date.today().strftime("%A")

        if "l'una" in frase:
            orario = "01"
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


    def diffInDays(self, day):
        if day == None:
            return 6
        today = datetime.date.today()
        diff = 0
        while day != today.strftime("%A"):
            diff += 1
            today = today + datetime.timedelta(1)
        return diff     #Funzione chiamata per controllare che si arrivi massimo a 4 (se passano più di 4 giorni non possiamo prevedere il tempo)



    def responseToAudio(self):
        return


    def goBack(self):
        self.ids['forecast_container'].clear_widgets()
        self.ids['today_icon'].source = "media/default.png"
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        request_today = None
        request_forecast = None
        sentence = ""
        day = ""
        hour = ""
        location = ""
        return True


    def key_pressed(self, window, key, *args):  
        if key == 27:
            if self.manager.current == 'forecast':
                self.ids['forecast_container'].clear_widgets()
                self.ids['today_icon'].source = "media/default.png"
                self.manager.current = 'main'
                self.manager.transition.direction = 'right'
                request_today = None
                request_forecast = None
                sentence = ""
                day = ""
                hour = ""
                location = ""
                return True
            return False


    def getIcon(self, descritpion):
        return "media/" + descritpion.replace(" ", "_") + ".png"


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