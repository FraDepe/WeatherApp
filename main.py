from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.tab.tab import MDTabsBase, MDTabs
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.list import OneLineListItem 
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelOneLine
import datetime
from geopy.geocoders import Nominatim
import json
import speech_recognition
import pyttsx3


from kivy import kivy_data_dir



class MainPage(Screen):
    
    request = None
    city = ""
    recognizer = speech_recognition.Recognizer()
    sentence = ""

    def listenToSearch(self):
        print("Comincio ad ascoltare")
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




class ForecastPage(Screen):

    city = StringProperty()
    request_today = None
    request_forecast = None
    sentence = ""

    def on_enter(self):
        #analisi della frase per capire se eseguire getToday o getForecast
        self.getToday()
        
    def getToday(self):
        print(self.sentence)
        gn = Nominatim(user_agent='WeatherApp') # Oppure usare l'API di OpenWeather
        coordinates = gn.geocode(self.sentence)
        print(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        req_today = UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        req_forecast = UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        req_today.wait()
        req_forecast.wait()
        self.ids['today_icon'].source = self.getIcon(req_today.result['weather'][0]['description'])
        #print(req.result)
        self.request_today = req_today
        self.request_forecast = req_forecast
        for x in req_forecast.result['list']:
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

    def getForecast(self):
        pass

    def goBack(self):
        self.manager.current = 'main'
        self.manager.transition.direction = 'right'

    def getIcon(self, descritpion):
        return "media/alternative/" + descritpion.replace(" ", "_") + ".png"

    def getDay(self,timestamp):
        day = datetime.datetime.fromtimestamp(timestamp).strftime("%A")
        if datetime.datetime.now().strftime("%A") in day:
            return "Today " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
        else:
            return day + " " + str(datetime.datetime.fromtimestamp(timestamp))[11:16]
    


class HourlyForecast(MDGridLayout):
    pass



class PageManager(ScreenManager):
    pass





class WeatherApp(MDApp):
    api_key = "c0b583a8bb8b03e64dd0e16bccda95bf"
    def build(self):
        #kv = Builder.load_file('weather.kv')
        Window.size = (450,800)
        #return kv




class Tab(MDFloatLayout, MDTabsBase):
    pass




if __name__ == '__main__':
    WeatherApp().run()