from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.tab.tab import MDTabsBase, MDTabs
from kivymd.uix.floatlayout import MDFloatLayout
import datetime
from geopy.geocoders import Nominatim
import json


class Tab(MDFloatLayout, MDTabsBase):
    pass


class MainPage(Screen):
    
    location = ObjectProperty(None)
    request = None

    def search(self):
        city = self.location.text
        gn = Nominatim(user_agent='WeatherApp')
        coordinates = gn.geocode(city)
        print(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf")
        req = UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf")
        req.wait()
        print(req.result)
        self.request = req
        forecast_page = self.manager.get_screen('forecast')
        forecast_page.request = req
        self.location.text = ""
        return req

    def listenToSearch(self):
        pass

class ForecastPage(Screen):

    def getWeather(self):
        pass

    def getIcon(self):
        main_page = self.manager.get_screen('main')

        return f"https://openweathermap.org/img/wn/{self.request.result['weather'][0]['icon']}@2x.png"

    def getDay(self,day_to_add):
        day = datetime.datetime.now()
        if day_to_add == 0:
            return "Today"
        elif day_to_add == 1:
            return "Tomorrow"
        else: 
            return (day + datetime.timedelta(day_to_add)).strftime('%A')
    

class PageManager(ScreenManager):
    pass



class WeatherApp(MDApp):
    api_key = "c0b583a8bb8b03e64dd0e16bccda95bf"
    def build(self):
        kv = Builder.load_file('weather.kv')
        Window.size = (450,800)
        return kv


if __name__ == '__main__':
    WeatherApp().run()