from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.tab.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout 
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
import datetime
from geopy.geocoders import Nominatim
import speech_recognition
import pyttsx3


##############################################################################################


class MainPage(Screen):
    
    request = None
    city = ""
    recognizer = speech_recognition.Recognizer()
    sentence = ""

    def listenToSearch(self):
        print("Comincio ad ascoltare")
        #engine = pyttsx3.init()
        #engine.say("Ascolto")
        #engine.runAndWait()
        self.ids['microphone'].background_normal = 'media/mic_listening.png' # NON CAMBIA
        try:
            with speech_recognition.Microphone() as mic:
                self.recognizer.adjust_for_ambient_noise(mic)
                audio = self.recognizer.record(mic, duration=1) # DURATION VA MESSO A 4 SECONDI
                text = self.recognizer.recognize_google(audio, language="it-it")
                text = text.lower()
                self.sentence = text
                print(text)
                self.manager.current = 'forecast'
                self.manager.transition.direction = 'left'
        except speech_recognition.UnknownValueError:
            print("Errore")
            self.sentence = "Roma"                      # NON HO VOGLIA DI PARLARE
            self.manager.current = 'forecast'           # NON HO VOGLIA DI PARLARE
            self.manager.transition.direction = 'left'  # NON HO VOGLIA DI PARLARE
        print("Finisco di ascoltare")
        self.ids['microphone'].background_normal = 'media/mic2.png' # NON CAMBIA


##############################################################################################


class ForecastPage(Screen):

    city = StringProperty()
    request_today = None
    request_forecast = None
    sentence = ""
    frase = 'suca'

    def on_enter(self):

        gn = Nominatim(user_agent='WeatherApp') # Oppure usare l'API di OpenWeather
        
        coordinates = gn.geocode(self.sentence) # Nella frase potrebbe non esserci una specifica
                                                # località (allora uso posizione del gps tramite plyer)

        req_today = UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        req_forecast = UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")

        req_today.wait()
        req_forecast.wait()

        self.request_today = req_today
        self.request_forecast = req_forecast

        #analisi della frase per capire se eseguire getToday o getForecast
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
        engine = pyttsx3.init()
        #rate = engine.getProperty('rate')
        #engine.setProperty('rate', rate-50)
        frase = self.frase
        #engine.say(frase)
        engine.say("suca")
        engine.runAndWait()
        return


    def goBack(self):
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'
        return


    def getIcon(self, descritpion):
        return "media/alternative/" + descritpion.replace(" ", "_") + ".png"

    def getDay(self,timestamp):
        day = datetime.datetime.fromtimestamp(timestamp).strftime("%A")
        if datetime.datetime.now().strftime("%A") in day:
            return "Today " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        else:
            return day + " " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
    

##############################################################################################


class HourlyForecast(MDGridLayout):
    pass


##############################################################################################


class PageManager(ScreenManager):
    pass


##############################################################################################


class WeatherApp(MDApp):
    api_key = "c0b583a8bb8b03e64dd0e16bccda95bf"
    def build(self):
        #kv = Builder.load_file('weather.kv')
        Window.size = (450,800)
        #return kv


##############################################################################################


if __name__ == '__main__':
    WeatherApp().run()